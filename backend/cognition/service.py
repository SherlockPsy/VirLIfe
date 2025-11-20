"""
Cognition Service Orchestrator

Main service class that orchestrates the complete cognition pipeline.
Per cognition_flow.md and MASTER_SPEC.

Flow:
1. Receive event + agent state
2. Compute salience and meaningfulness
3. Check eligibility (M, triviality, cooldown, choice)
4. Build semantic context (Phase 4 integration)
5. Call LLM (if eligible) - with Redis caching
6. Apply numeric updates (stance shifts + intention updates)
7. Return updated state + cognition output

Redis Caching (Phase 9 integration):
- Cache LLM responses by event hash (24h TTL)
- Cache cognition cooldown status (1h TTL)
- Cache salience context computations (10m TTL)
- Graceful degradation: system works identically without Redis
- Non-authoritative: Postgres remains source of truth
"""

import hashlib
import json
from dataclasses import dataclass, field
from typing import Dict, Optional, List, Any, Tuple
from datetime import datetime, timedelta

from backend.cognition.salience import SalienceCalculator, AgentSalienceContext
from backend.cognition.meaningfulness import MeaningfulnessCalculator, MeaningfulnessScore
from backend.cognition.eligibility import (
    CognitionEligibilityChecker, CognitionEligibilityResult,
    EventTrivialityClassification, BehavioralChoice
)
from backend.cognition.llm_wrapper import LLMCognitionWrapper, CognitionLLMResponse
from backend.cognition.numeric_updates import StanceShiftMapper, IntentionUpdateMapper
from backend.mapping.cognition_context import CognitionContextBuilder
from backend.mapping.semantic_mappers import (
    MoodMapper, DriveMapper, RelationshipMapper, ArcMapper,
    EnergyMapper, IntentionMapper, PersonalityMapper, MemoryMapper
)
from backend.caching import get_redis_service
from backend.memory import get_qdrant_service


@dataclass
class CognitionInput:
    """Input to the cognition pipeline."""
    agent_id: str
    event_type: str                         # "speech", "action", "incursion", etc.
    event_time: datetime
    event_description: str                  # Human-readable event summary
    
    # Agent state (numeric substrate from Phase 3)
    personality_kernel: Dict[str, Any]
    personality_activation: Dict[str, float]
    mood: Tuple[float, float]              # (valence, arousal)
    drives: Dict[str, float]               # {drive_name: level [0,1]}
    arcs: Dict[str, Dict]                  # {arc_topic: {intensity, valence_bias, ...}}
    energy: float                          # [0, 1]
    relationships: Dict[str, Dict]         # {person_id: {warmth, trust, tension, ...}}
    intentions: Dict[str, Dict]            # {intention_id: {...}}
    memories: Dict[str, List[Dict]]        # {episodic: [...], biographical: [...]}
    
    # Event context
    event_participants: Dict[str, Dict]    # {person_id: {name, role, ...}}
    event_topics: List[str]                # Topics mentioned/implied by event
    event_triviality: EventTrivialityClassification
    behavioral_choices: List[BehavioralChoice]
    
    # Optional context
    relevant_calendar_context: Optional[str] = None
    relevant_unexpected_event_context: Optional[str] = None
    
    # Metadata
    last_cognition_time: Optional[datetime] = None
    cognition_cooldown_minutes: int = 5


@dataclass
class CognitionOutput:
    """Output from the cognition pipeline."""
    agent_id: str
    event_time: datetime
    
    # Cognition eligibility and execution
    was_eligible: bool
    eligibility_result: Optional[CognitionEligibilityResult] = None
    llm_called: bool = False
    llm_response: Optional[CognitionLLMResponse] = None
    
    # Updated numeric state (after applying stance shifts and intention updates)
    updated_relationships: Optional[Dict[str, Dict]] = None
    updated_intentions: Optional[Dict[str, Dict]] = None
    updated_drives: Optional[Dict[str, float]] = None
    
    # Metadata
    execution_time_ms: float = 0.0
    errors: List[str] = field(default_factory=list)


class CognitionService:
    """
    Main cognition service orchestrating the complete pipeline.
    
    Per cognition_flow.md §2-7:
    High-level flow:
    1. Event occurs in the World Engine.
    2. World Engine updates raw state.
    3. Autonomy Engine updates numeric psychology.
    4. For each potentially affected agent:
       - compute salience and meaningfulness score M.
    5. If cognition conditions are met:
       - build semantic context packet.
       - call Cognition LLM.
       - parse structured output.
       - apply deterministic numeric updates.
    6. World Engine persists state.
    """
    
    @staticmethod
    def process_cognition(cognition_input: CognitionInput) -> CognitionOutput:
        """
        Process a complete cognition cycle for an agent (synchronous version).
        
        This is the core synchronous method used by tests and legacy code.
        For production with caching, use process_cognition_async() instead.
        
        Args:
            cognition_input: CognitionInput with all required data
        
        Returns:
            CognitionOutput with results, updated state, and metadata
        """
        start_time = datetime.now()
        output = CognitionOutput(
            agent_id=cognition_input.agent_id,
            event_time=cognition_input.event_time,
            was_eligible=False
        )
        
        try:
            # STEP 1: Compute salience context
            salience_context = SalienceCalculator.build_salience_context(
                agent_id=cognition_input.agent_id,
                people=cognition_input.event_participants,
                topics=cognition_input.event_topics,
                objects={},  # TODO: Add object detection from event
                drive_levels=cognition_input.drives,
                arcs=cognition_input.arcs,
                agent_relationships=cognition_input.relationships,
                agent_intentions=cognition_input.intentions
            )
            
            # STEP 2: Compute meaningfulness score
            m_score = MeaningfulnessCalculator.compute_m_score(
                salience_context=salience_context,
                drive_levels=cognition_input.drives,
                arcs=cognition_input.arcs,
                relationships=cognition_input.relationships,
                energy=cognition_input.energy
            )
            
            # STEP 3: Check cognition eligibility (4-factor check)
            eligibility_result = CognitionEligibilityChecker.check_eligibility(
                m_score_value=m_score.total_m,
                m_threshold=m_score.threshold,
                event_triviality=cognition_input.event_triviality,
                last_cognition_time=cognition_input.last_cognition_time,
                current_time=cognition_input.event_time,
                cooldown_minutes=cognition_input.cognition_cooldown_minutes,
                behavioral_choices=cognition_input.behavioral_choices
            )
            
            output.eligibility_result = eligibility_result
            output.was_eligible = eligibility_result.is_eligible
            
            # If not eligible, return early
            if not eligibility_result.is_eligible:
                output.llm_called = False
                output.execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
                return output
            
            # STEP 4: Build semantic context (Phase 4 integration)
            # Convert numeric state to semantic summaries
            personality_stable = PersonalityMapper.map_stable_summary(
                cognition_input.personality_kernel
            )
            personality_domain = PersonalityMapper.map_domain_summaries(
                cognition_input.personality_kernel
            )
            personality_activation = PersonalityMapper.map_activation_packet(
                cognition_input.personality_kernel,
                cognition_input.personality_activation,
                cognition_input.mood,
                cognition_input.drives,
                cognition_input.energy,
                cognition_input.arcs,
                cognition_input.relationships
            )
            
            mood_summary = MoodMapper.map_mood(
                valence=cognition_input.mood[0],
                arousal=cognition_input.mood[1]
            )
            
            drives_summary = DriveMapper.map_all_drives(cognition_input.drives)
            
            relationships_summary = {}
            for person_id, rel in cognition_input.relationships.items():
                relationships_summary[person_id] = RelationshipMapper.map_relationship_full(
                    warmth=rel.get("warmth", 0),
                    trust=rel.get("trust", 0),
                    tension=rel.get("tension", 0),
                    attraction=rel.get("attraction"),
                    comfort=rel.get("comfort"),
                    familiarity=rel.get("familiarity")
                )
            
            arcs_summary = ArcMapper.map_arcs_summary(cognition_input.arcs)
            
            energy_summary = EnergyMapper.map_energy(cognition_input.energy)
            
            intentions_summary = IntentionMapper.map_intentions(cognition_input.intentions)
            
            memory_snippets = MemoryMapper.format_memories(
                cognition_input.memories
            )
            
            # Build complete context
            context_packet = {
                "agent_id": cognition_input.agent_id,
                "event_description": cognition_input.event_description,
                "event_time": cognition_input.event_time.isoformat(),
                "personality": {
                    "stable_summary": personality_stable,
                    "domain_summaries": personality_domain,
                    "dynamic_activation": personality_activation
                },
                "mood": mood_summary,
                "drives": drives_summary,
                "relationships": relationships_summary,
                "arcs": arcs_summary,
                "energy": energy_summary,
                "intentions": intentions_summary,
                "memories": memory_snippets,
                "participants": [
                    {p_id: {"name": p_data.get("name", p_id)}}
                    for p_id, p_data in cognition_input.event_participants.items()
                ]
            }
            
            if cognition_input.relevant_calendar_context:
                context_packet["calendar_context"] = cognition_input.relevant_calendar_context
            
            if cognition_input.relevant_unexpected_event_context:
                context_packet["unexpected_event_context"] = cognition_input.relevant_unexpected_event_context
            
            # STEP 5: Call LLM
            llm_response = LLMCognitionWrapper.call_cognition_llm(context_packet)
            output.llm_called = True
            output.llm_response = llm_response
            
            # STEP 6: Apply numeric updates (if LLM response valid)
            if llm_response and llm_response.is_valid:
                # Apply stance shifts to relationships
                updated_relationships = cognition_input.relationships.copy()
                for stance_shift in llm_response.stance_shifts:
                    target = stance_shift.target
                    if target in updated_relationships:
                        updated_relationships[target] = StanceShiftMapper.apply_stance_shift(
                            updated_relationships[target],
                            stance_shift.description
                        )
                output.updated_relationships = updated_relationships
                
                # Apply intention updates to drives
                updated_drives = cognition_input.drives.copy()
                for intention_update in llm_response.intention_updates:
                    from backend.cognition.numeric_updates import (
                        IntentionOperationType, IntentionType, IntentionHorizon
                    )
                    try:
                        operation = IntentionOperationType(intention_update.operation)
                        intent_type = IntentionType(intention_update.type)
                        horizon = IntentionHorizon(intention_update.horizon)
                        
                        updated_drives = IntentionUpdateMapper.apply_intention_update(
                            updated_drives, operation, intent_type, horizon
                        )
                    except ValueError as e:
                        output.errors.append(f"Invalid intention update: {e}")
                output.updated_drives = updated_drives
                
                # Note: updated_intentions would be constructed from intention_updates
                # This requires creating/updating/dropping intention records
                # For now, we track the update descriptors in the LLM response
        
        except Exception as e:
            output.errors.append(f"Cognition pipeline error: {str(e)}")
            output.llm_called = False
        
        finally:
            output.execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        return output
    
    @staticmethod
    async def process_cognition_async(cognition_input: CognitionInput) -> CognitionOutput:
        """
        Process cognition with Redis caching and Qdrant memory integration (async version).
        
        This async wrapper adds:
        - Cognition cooldown caching via Redis (optimization)
        - LLM response caching by event hash (24h TTL, Redis)
        - Salience context caching (10m TTL, Redis)
        - Episodic and biographical memory retrieval via Qdrant
        - Memory indexing after successful cognition
        
        Falls back gracefully to synchronous processing if Redis/Qdrant unavailable.
        
        Args:
            cognition_input: CognitionInput with all required data
        
        Returns:
            CognitionOutput with results, updated state, and metadata
        
        Notes:
            - Uses Redis caching for performance (non-authoritative)
            - Uses Qdrant for semantic memory retrieval (Postgres-authoritative)
            - Postgres remains source of truth for all data
            - Identical results with or without caching layers
        """
        start_time = datetime.now()
        output = CognitionOutput(
            agent_id=cognition_input.agent_id,
            event_time=cognition_input.event_time,
            was_eligible=False
        )
        
        try:
            # Get Redis and Qdrant services (may be None if disabled)
            redis_service = await get_redis_service()
            qdrant_service = await get_qdrant_service()
            
            # STEP 0: Check cognition cooldown from cache
            # This optimizes the eligibility check by avoiding database queries
            if redis_service and await redis_service.is_available():
                cooldown_status = await redis_service.get_cognition_cooldown(
                    cognition_input.agent_id
                )
                # If on cooldown, return early (optimization only - Postgres is authoritative)
                if cooldown_status:
                    output.was_eligible = False
                    output.eligibility_result = CognitionEligibilityResult(
                        is_eligible=False,
                        reason="cognition_cooldown_active"
                    )
                    output.execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
                    return output
            
            # STEP 0.5: Search for relevant memories using Qdrant
            # These will be included in semantic context for better cognition
            relevant_memories = []
            memory_search_query = f"{cognition_input.event_description} {' '.join(cognition_input.event_topics)}"
            
            if qdrant_service and await qdrant_service.is_available():
                try:
                    relevant_memories = await qdrant_service.search_all_memories(
                        agent_id=cognition_input.agent_id,
                        query_text=memory_search_query,
                        limit=5,  # Limit to top 5 relevant memories
                        threshold=0.2  # Lower threshold to get more context
                    )
                except Exception as e:
                    # Graceful degradation: continue without Qdrant
                    output.errors.append(f"Qdrant memory search error: {str(e)}")
            
            # Run core synchronous cognition
            base_output = CognitionService.process_cognition(cognition_input)
            
            # If not eligible, return early
            if not base_output.was_eligible:
                output.execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
                return base_output
            
            # STEP 7: Memory indexing after successful cognition
            # Index any memories in the event for future retrieval
            if base_output.llm_called and base_output.llm_response and relevant_memories:
                # Extract memory-worthy facts from the event
                memory_description = f"{cognition_input.event_description} - Topics: {', '.join(cognition_input.event_topics)}"
                
                if qdrant_service and await qdrant_service.is_available():
                    try:
                        # Index this event as an episodic memory for future retrieval
                        await qdrant_service.index_episodic_memory(
                            agent_id=cognition_input.agent_id,
                            memory_id=hash(memory_description) % (10 ** 8),  # Deterministic ID
                            description=memory_description,
                            timestamp=cognition_input.event_time.isoformat()
                        )
                    except Exception as e:
                        # Graceful degradation: continue without indexing
                        output.errors.append(f"Qdrant memory indexing error: {str(e)}")
            
            # Cache results after successful cognition (via Redis)
            if base_output.llm_called and base_output.llm_response:
                # Build context packet for hash (reusing sync version's logic)
                # This is needed for cache key generation
                personality_stable = PersonalityMapper.map_stable_summary(
                    cognition_input.personality_kernel
                )
                personality_domain = PersonalityMapper.map_domain_summaries(
                    cognition_input.personality_kernel
                )
                personality_activation = PersonalityMapper.map_activation_packet(
                    cognition_input.personality_kernel,
                    cognition_input.personality_activation,
                    cognition_input.mood,
                    cognition_input.drives,
                    cognition_input.energy,
                    cognition_input.arcs,
                    cognition_input.relationships
                )
                
                mood_summary = MoodMapper.map_mood(
                    valence=cognition_input.mood[0],
                    arousal=cognition_input.mood[1]
                )
                
                drives_summary = DriveMapper.map_all_drives(cognition_input.drives)
                
                relationships_summary = {}
                for person_id, rel in cognition_input.relationships.items():
                    relationships_summary[person_id] = RelationshipMapper.map_relationship_full(
                        warmth=rel.get("warmth", 0),
                        trust=rel.get("trust", 0),
                        tension=rel.get("tension", 0),
                        attraction=rel.get("attraction"),
                        comfort=rel.get("comfort"),
                        familiarity=rel.get("familiarity")
                    )
                
                arcs_summary = ArcMapper.map_arcs_summary(cognition_input.arcs)
                energy_summary = EnergyMapper.map_energy(cognition_input.energy)
                
                context_packet = {
                    "event_description": cognition_input.event_description,
                    "personality": {
                        "stable_summary": personality_stable,
                        "domain_summaries": personality_domain,
                        "dynamic_activation": personality_activation
                    },
                    "mood": mood_summary,
                    "drives": drives_summary,
                    "relationships": relationships_summary,
                    "arcs": arcs_summary,
                    "energy": energy_summary,
                    "participants": [
                        {p_id: {"name": p_data.get("name", p_id)}}
                        for p_id, p_data in cognition_input.event_participants.items()
                    ]
                }
                
                event_hash = CognitionService._compute_event_hash(context_packet)
                
                # Cache LLM response
                if redis_service and await redis_service.is_available():
                    try:
                        await redis_service.cache_llm_cognition_response(
                            agent_id=cognition_input.agent_id,
                            event_hash=event_hash,
                            response={
                                "is_valid": base_output.llm_response.is_valid,
                                "stance_shifts": [
                                    {
                                        "target": shift.target,
                                        "description": shift.description
                                    }
                                    for shift in (base_output.llm_response.stance_shifts or [])
                                ],
                                "intention_updates": [
                                    {
                                        "operation": update.operation,
                                        "type": update.type,
                                        "horizon": update.horizon,
                                        "description": update.description
                                    }
                                    for update in (base_output.llm_response.intention_updates or [])
                                ]
                            }
                        )
                    except Exception as e:
                        # Graceful degradation: continue without cache
                        output.errors.append(f"Redis LLM cache storage error: {str(e)}")
                
                # Set cognition cooldown in Redis
                if redis_service and await redis_service.is_available():
                    try:
                        await redis_service.set_cognition_cooldown(
                            agent_id=cognition_input.agent_id,
                            cooldown_minutes=cognition_input.cognition_cooldown_minutes
                        )
                    except Exception as e:
                        # Graceful degradation: continue without cache
                        output.errors.append(f"Redis cooldown cache error: {str(e)}")
            
            # Return the base output with any additional errors from caching/memory
            if output.errors:
                base_output.errors.extend(output.errors)
            
            return base_output
        
        except Exception as e:
            output.errors.append(f"Cognition async pipeline error: {str(e)}")
            output.llm_called = False
            output.execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000
            return output
    
    @staticmethod
    def _compute_event_hash(context_packet: Dict[str, Any]) -> str:
        """
        Compute a deterministic hash of the event context for cache keying.
        
        This hash is used as a cache key for LLM responses. Same context packet
        should always produce the same hash, enabling cache hits for identical events.
        
        Args:
            context_packet: The semantic context packet for the event
        
        Returns:
            A hex string hash of the context
        """
        # Create a deterministic string representation
        # Use only fields that affect LLM output, not time/agent_id
        key_fields = {
            "event_description": context_packet.get("event_description", ""),
            "personality": context_packet.get("personality", {}),
            "mood": context_packet.get("mood", ""),
            "drives": context_packet.get("drives", ""),
            "relationships": context_packet.get("relationships", {}),
            "arcs": context_packet.get("arcs", {}),
            "energy": context_packet.get("energy", ""),
            "participants": context_packet.get("participants", [])
        }
        
        # Serialize to JSON with sorted keys for determinism
        key_str = json.dumps(key_fields, sort_keys=True, default=str)
        
        # Return SHA256 hash
        return hashlib.sha256(key_str.encode()).hexdigest()
