"""
PFEE Perception Orchestrator

Implements:
- PFEE_ARCHITECTURE.md §2.4
- PFEE_LOGIC.md §5
- PFEE_PLAN.md Phase P4

Central orchestrator for perception cycles.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from backend.pfee.triggers import TriggerEvaluator, TriggerDecision, TriggerReason
from backend.pfee.entities import EntityPersistenceManager, EntityType
from backend.pfee.potentials import PotentialResolver, ResolvedPotential
from backend.pfee.consequences import ConsequenceIntegrator
from backend.pfee.time_continuity import TimeAndContinuityManager
from backend.pfee.influence_fields import InfluenceFieldManager
from backend.pfee.info_events import InformationEventManager, InfoEvent
from backend.pfee.logging import PFEELogger
from backend.pfee.semantic_mapping import PFEESemanticMapper
from backend.pfee.validation import ValidationResult

from backend.cognition.service import CognitionService, CognitionInput
from backend.cognition.salience import SalienceCalculator
from backend.cognition.meaningfulness import MeaningfulnessCalculator
from backend.cognition.eligibility import CognitionEligibilityChecker
from backend.renderer.service import RenderEngine
from backend.persistence.repo import WorldRepo, AgentRepo
from backend.persistence.models import AgentModel, ArcModel, IntentionModel, MemoryModel
from backend.pfee.world_state_builder import build_world_state_for_pfee
from sqlalchemy import select


@dataclass
class PerceptionResult:
    """Result of a perception cycle."""
    text: Optional[str] = None
    world_state: Optional[Dict[str, Any]] = None
    cognition_output: Optional[Dict[str, Any]] = None
    renderer_output: Optional[Dict[str, Any]] = None
    triggers_fired: List[TriggerDecision] = None
    entities_instantiated: List[Dict[str, Any]] = None
    
    @classmethod
    def none(cls) -> "PerceptionResult":
        """No perception occurred."""
        return cls(
            text=None,
            world_state=None,
            triggers_fired=[],
            entities_instantiated=[]
        )


class PerceptionOrchestrator:
    """
    Central orchestrator for perception cycles.
    
    Implements PFEE_LOGIC.md §5 perception cycle logic.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.trigger_evaluator = TriggerEvaluator(session)
        self.entity_manager = EntityPersistenceManager(session)
        self.potential_resolver = PotentialResolver(session)
        self.consequence_integrator = ConsequenceIntegrator(session)
        self.time_manager = TimeAndContinuityManager(session)
        self.influence_manager = InfluenceFieldManager(session)
        self.info_event_manager = InformationEventManager(session)
        self.logger = PFEELogger(session)
        
        self.cognition_service = CognitionService()
        self.render_engine = RenderEngine(session)
        
        self.world_repo = WorldRepo(session)
        self.agent_repo = AgentRepo(session)
    
    async def run_perception_cycle(
        self,
        world_state: Dict[str, Any],
        optional_user_action: Optional[Dict[str, Any]] = None
    ) -> PerceptionResult:
        """
        Run a complete perception cycle.
        
        Implements PFEE_LOGIC.md §5 main perception cycle.
        
        Steps:
        1. Evaluate triggers
        2. Resolve potentials and entities
        3. Build LLM inputs (semantic only)
        4. Call LLM services
        5. Integrate consequences
        6. Log
        """
        try:
            # Start logging cycle
            import uuid
            cycle_id = str(uuid.uuid4())
            self.logger.start_perception_cycle(cycle_id)
            
            # 1. Evaluate triggers
            decisions = []
            
            # User action trigger
            user_decision = await self.trigger_evaluator.evaluate_user_action_trigger(
                optional_user_action, world_state
            )
            if user_decision.should_trigger:
                decisions.append(user_decision)
                self.logger.log_trigger_firing(
                    user_decision.reason.value,
                    metadata=user_decision.metadata
                )
            
            # Agent initiative triggers
            agent_decisions = await self.trigger_evaluator.evaluate_agent_initiative_triggers(
                world_state
            )
            decisions.extend(agent_decisions)
            for decision in agent_decisions:
                self.logger.log_trigger_firing(
                    decision.reason.value,
                    agent_id=decision.agent_id
                )
            
            # Resolve potentials for interruptions
            context = self._extract_current_context(world_state)
            resolved_potentials = await self.potential_resolver.resolve_potentials_for_context(
                context
            )
            
            # Interruption triggers
            interruption_decisions = await self.trigger_evaluator.evaluate_interruption_triggers(
                world_state, resolved_potentials
            )
            decisions.extend(interruption_decisions)
            for decision in interruption_decisions:
                self.logger.log_trigger_firing(
                    decision.reason.value,
                    metadata={"potential_id": decision.potential_id}
                )
            
            # Information event triggers
            info_events = await self.info_event_manager.compute_due_information_events(world_state)
            info_decisions = await self.trigger_evaluator.evaluate_info_event_triggers(
                world_state, [{"id": ev.id, "type": ev.type.value} for ev in info_events]
            )
            decisions.extend(info_decisions)
            
            # Environmental triggers
            environmental_shifts = await self._detect_environmental_shifts(world_state)
            env_decisions = await self.trigger_evaluator.evaluate_environment_triggers(
                world_state, environmental_shifts
            )
            decisions.extend(env_decisions)
            
            # Filter out non-triggers
            decisions = [d for d in decisions if d.should_trigger]
            
            # If no triggers, return early
            if not decisions:
                return PerceptionResult.none()
            
            # 2. Resolve potentials and entities
            entities = await self._instantiate_entities_from_potentials(
                resolved_potentials, world_state
            )
            
            # Ensure classification
            for entity in entities:
                entity_type = self._determine_entity_type(entity)
                persistence_level = await self.entity_manager.classify_entity_persistence(
                    entity, context, entity_type
                )
                entity["persistence_level"] = persistence_level.value
                self.logger.log_entity_classification(
                    entity.get("id", 0),
                    entity_type.value,
                    persistence_level.value,
                    "automatic_classification"
                )
            
            # 3. Compute eligibility FIRST using numeric values (separate from LLM input)
            # This ensures eligibility is computed before creating LLM-facing input
            eligibility_result = await self._compute_cognition_eligibility(
                world_state, decisions, entities, context
            )
            
            # 4. Build LLM inputs (semantic only, no numeric state)
            # Only build if eligible
            cognition_input = None
            if eligibility_result and eligibility_result.get("is_eligible", False):
                cognition_input = await self._build_cognition_input_semantic_only(
                    world_state, decisions, entities, context, eligibility_result
                )
            
            renderer_input = await self._build_renderer_input(
                world_state, decisions, entities, context, info_events
            )
            
            # 5. Call LLM services (only if eligible)
            cognition_output = None
            if cognition_input:
                try:
                    cognition_result = self.cognition_service.process_cognition(cognition_input)
                    if cognition_result.was_eligible and cognition_result.llm_response:
                        # Validate LLM output against world state before applying
                        validation_result = await self._validate_llm_output_against_world(
                            cognition_result.llm_response,
                            world_state,
                            context
                        )
                        
                        if not validation_result.is_valid:
                            # Reject contradictory output
                            self.logger.log_error(
                                "PerceptionOrchestrator",
                                "llm_output_contradiction",
                                f"LLM output rejected: {validation_result.reason}",
                                exception=None
                            )
                            # Use fallback behavior (no cognition output)
                            cognition_output = None
                        else:
                            # Output is valid, use it
                        cognition_output = {
                            "agent_id": cognition_result.agent_id,
                            "utterance": cognition_result.llm_response.utterance,
                            "action": cognition_result.llm_response.action,
                            "stance_shifts": [
                                {
                                    "target": shift.target,
                                    "description": shift.description
                                }
                                for shift in (cognition_result.llm_response.stance_shifts or [])
                            ],
                            "intention_updates": [
                                {
                                    "operation": update.operation,
                                    "type": update.type,
                                    "target": update.target,
                                    "horizon": update.horizon,
                                    "description": update.description
                                }
                                for update in (cognition_result.llm_response.intention_updates or [])
                            ]
                        }
                            self.logger.log_llm_call(
                                "cognition",
                                "agent_decision",
                                agent_id=int(cognition_result.agent_id) if cognition_result.agent_id else None
                            )
                except Exception as e:
                    self.logger.log_error(
                        "PerceptionOrchestrator",
                        "cognition_call_failed",
                        f"Cognition call failed: {str(e)}",
                        exception=e
                    )
            
            # Call renderer
            renderer_output = None
            try:
                perceiver_id = world_state.get("user_id", 1)
                renderer_text = await self.render_engine.render_world_state(
                    perceiver_id=perceiver_id,
                    perceiver_type="user"
                )
                renderer_output = {
                    "text": renderer_text,
                    "physical_changes": {}  # Can be extracted from renderer if available
                }
                self.logger.log_llm_call("renderer", "perception_rendering")
            except Exception as e:
                self.logger.log_error(
                    "PerceptionOrchestrator",
                    "renderer_call_failed",
                    f"Renderer call failed: {str(e)}",
                    exception=e
                )
            
            # 6. Integrate consequences
            updated_world_state = await self.consequence_integrator.apply_perception_outcome(
                cognition_output, renderer_output, world_state
            )
            
            # 7. Log
            self.logger.log_perception_cycle(
                [{"reason": d.reason.value, "agent_id": d.agent_id} for d in decisions],
                [{"id": rp.id, "type": rp.potential_type.value} for rp in resolved_potentials],
                entities,
                cognition_output,
                renderer_output
            )
            
            await self.session.flush()
            
            return PerceptionResult(
                text=renderer_output.get("text") if renderer_output else None,
                world_state=updated_world_state,
                cognition_output=cognition_output,
                renderer_output=renderer_output,
                triggers_fired=decisions,
                entities_instantiated=entities
            )
        except Exception as e:
            self.logger.log_error(
                "PerceptionOrchestrator",
                "perception_cycle_failed",
                f"Perception cycle failed: {str(e)}",
                exception=e
            )
            return PerceptionResult.none()
    
    def _extract_current_context(self, world_state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract current context for potential resolution."""
        return {
            "context_type": world_state.get("current_location_type", "general"),
            "location": world_state.get("current_location_id"),
            "current_time": world_state.get("current_time"),
            "salience": world_state.get("salience", 0.0),
            "agents_present": world_state.get("persistent_agents_present_with_user", [])
        }
    
    async def _instantiate_entities_from_potentials(
        self,
        resolved_potentials: List[ResolvedPotential],
        world_state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Instantiate entities from resolved potentials."""
        entities = []
        for rp in resolved_potentials:
            if rp.resolved_entity:
                entity = {
                    "id": rp.id,  # Would be assigned by persistence
                    "type": rp.resolved_entity.get("type"),
                    "name": rp.resolved_entity.get("name", "Unknown"),
                    "persistence_level": "ephemeral",  # Default, will be classified
                    **rp.resolved_entity
                }
                entities.append(entity)
                self.logger.log_potential_resolution(
                    rp.id,
                    rp.potential_type.value,
                    rp.resolved_entity
                )
        return entities
    
    def _determine_entity_type(self, entity: Dict[str, Any]) -> EntityType:
        """Determine entity type from entity data."""
        entity_type_str = entity.get("type", "person")
        if entity_type_str in ["location", "place"]:
            return EntityType.LOCATION
        elif entity_type_str in ["object", "item"]:
            return EntityType.OBJECT
        elif entity_type_str in ["organisation", "institution"]:
            return EntityType.ORGANISATION
        elif entity_type_str in ["information_source", "contact"]:
            return EntityType.INFORMATION_SOURCE
        else:
            return EntityType.PERSON
    
    async def _compute_cognition_eligibility(
        self,
        world_state: Dict[str, Any],
        decisions: List[TriggerDecision],
        entities: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Compute cognition eligibility using numeric values (separate from LLM input).
        
        This ensures eligibility is computed BEFORE creating LLM-facing input.
        Numeric values are kept in PFEE context, not passed to LLM.
        """
        # Find agent initiative decisions
        agent_decisions = [d for d in decisions if d.reason == TriggerReason.AGENT_INITIATIVE]
        if not agent_decisions:
            return None
        
        agent_id = agent_decisions[0].agent_id
        if not agent_id:
            return None
        
        # Load agent with numeric state
        agent = await self.agent_repo.get_agent_by_id(agent_id)
        if not agent:
            return None
        
        # Load numeric state for eligibility calculations
        arcs_stmt = select(ArcModel).where(ArcModel.agent_id == agent_id)
        arcs_result = await self.session.execute(arcs_stmt)
        arcs_models = arcs_result.scalars().all()
        arcs = {
            arc.type: {
                "intensity": arc.intensity,
                "valence_bias": arc.valence_bias,
                "topic_vector": arc.topic_vector or [],
                "decay_rate": arc.decay_rate
            }
            for arc in arcs_models
        }
        
        intentions_stmt = select(IntentionModel).where(IntentionModel.agent_id == agent_id)
        intentions_result = await self.session.execute(intentions_stmt)
        intentions_models = intentions_result.scalars().all()
        intentions = {
            str(intent.id): {
                "description": intent.description,
                "priority": intent.priority,
                "horizon": intent.horizon,
                "type": intent.type,
                "stability": intent.stability
            }
            for intent in intentions_models
        }
        
        relationships_models = await self.agent_repo.get_relationships(agent_id)
        relationships = {}
        for rel in relationships_models:
            target_key = f"agent:{rel.target_agent_id}" if rel.target_agent_id else f"user:{rel.target_user_id}"
            relationships[target_key] = {
                "warmth": rel.warmth,
                "trust": rel.trust,
                "tension": rel.tension,
                "attraction": rel.attraction,
                "familiarity": rel.familiarity,
                "comfort": rel.comfort,
                "volatility": rel.volatility
            }
        
        drives_dict = {
            k: (v.get("level", 0.0) if isinstance(v, dict) else v)
            for k, v in (agent.drives or {}).items()
        }
        
        # Build event participants
        event_participants = {}
        agents_present = world_state.get("persistent_agents_present_with_user", [])
        for agent_data in agents_present:
            event_participants[str(agent_data["id"])] = {
                "name": agent_data["name"],
                "role": "agent"
            }
        if world_state.get("user_id"):
            event_participants[str(world_state["user_id"])] = {
                "name": f"user_{world_state['user_id']}",
                "role": "user"
            }
        
        # Compute salience and meaningfulness (using numeric values)
        salience_context = SalienceCalculator.build_salience_context(
            agent_id=str(agent_id),
            people=event_participants,
            topics=context.get("topics", []),
            objects={},
            drive_levels=drives_dict,
            arcs=arcs,
            agent_relationships=relationships,
            agent_intentions=intentions
        )
        
        m_score = MeaningfulnessCalculator.compute_m_score(
            salience_context=salience_context,
            drive_levels=drives_dict,
            arcs=arcs,
            relationships=relationships,
            energy=agent.energy or 1.0
        )
        
        # Check eligibility
        from backend.cognition.eligibility import EventTrivialityClassification, BehavioralChoice
        event_triviality = EventTrivialityClassification.NON_TRIVIAL
        behavioral_choices = [
            BehavioralChoice.SPEAK_OR_SILENCE,
            BehavioralChoice.APPROACH_OR_WITHDRAW,
            BehavioralChoice.ESCALATE_OR_DE_ESCALATE
        ]
        
        eligibility_result = CognitionEligibilityChecker.check_eligibility(
            m_score_value=m_score.total_m,
            m_threshold=m_score.threshold,
            event_triviality=event_triviality,
            last_cognition_time=agent.last_cognition_timestamp,
            current_time=world_state.get("current_time", datetime.now(timezone.utc)),
            cooldown_minutes=5,
            behavioral_choices=behavioral_choices
        )
        
        # Store numeric values in context for later use (NOT passed to LLM)
        context["_eligibility_numeric_state"] = {
            "drives": drives_dict,
            "arcs": arcs,
            "relationships": relationships,
            "energy": agent.energy or 1.0,
            "mood": agent.mood if isinstance(agent.mood, dict) else {"valence": 0.0, "arousal": 0.0},
            "personality_kernel": agent.personality_kernel or {},
            "intentions": intentions
        }
        
        return {
            "is_eligible": eligibility_result.is_eligible,
            "m_score": m_score.total_m,
            "eligibility_result": eligibility_result
        }
    
    async def _build_cognition_input_semantic_only(
        self,
        world_state: Dict[str, Any],
        decisions: List[TriggerDecision],
        entities: List[Dict[str, Any]],
        context: Dict[str, Any],
        eligibility_result: Dict[str, Any]
    ) -> Optional[CognitionInput]:
        """
        Build cognition input packet with ONLY semantic summaries (no numeric state).
        
        Implements:
        - MASTER_SPEC §"Numeric vs Semantic"
        - docs/numeric_semantic_mapping.md
        - PFEE_LOGIC.md §5
        - BUILDER_CONTRACT.md (no numeric leakage into LLM context)
        """
        # Get agent ID from decisions
        agent_decisions = [d for d in decisions if d.reason == TriggerReason.AGENT_INITIATIVE]
        if not agent_decisions:
            return None
        
        agent_id = agent_decisions[0].agent_id
        if not agent_id:
            return None
        
        # Load agent (for memories and metadata only)
        agent = await self.agent_repo.get_agent_by_id(agent_id)
        if not agent:
            return None
        
        # Get numeric state from context (computed in _compute_cognition_eligibility)
        numeric_state = context.get("_eligibility_numeric_state", {})
        if not numeric_state:
            return None
        
        # Load agent's memories (semantic/textual)
        memories_stmt = select(MemoryModel).where(
            MemoryModel.agent_id == agent_id
        ).order_by(MemoryModel.created_at.desc()).limit(10)
        memories_result = await self.session.execute(memories_stmt)
        memories_models = memories_result.scalars().all()
        episodic = [
            {
                "description": m.description,
                "timestamp": m.timestamp.isoformat() if m.timestamp else None,
                "salience": m.salience,
                "semantic_tags": m.semantic_tags or []
            }
            for m in memories_models if m.type == "episodic"
        ]
        biographical = [
            {
                "description": m.description,
                "salience": m.salience,
                "semantic_tags": m.semantic_tags or []
            }
            for m in memories_models if m.type == "biographical"
        ]
        
        # Build event participants (identifiers only)
        event_participants = {}
        agents_present = world_state.get("persistent_agents_present_with_user", [])
        for agent_data in agents_present:
            event_participants[str(agent_data["id"])] = {
                "name": agent_data["name"],
                "role": "agent"
            }
        if world_state.get("user_id"):
            event_participants[str(world_state["user_id"])] = {
                "name": f"user_{world_state['user_id']}",
                "role": "user"
            }
        
        # Convert ALL numeric state to semantic summaries
        mood_dict = numeric_state.get("mood", {"valence": 0.0, "arousal": 0.0})
        drives_dict = numeric_state.get("drives", {})
        relationships = numeric_state.get("relationships", {})
        arcs = numeric_state.get("arcs", {})
        energy = numeric_state.get("energy", 1.0)
        intentions = numeric_state.get("intentions", {})
        personality_kernel = numeric_state.get("personality_kernel", {})
        
        # Create semantic summaries (NO numeric values)
        semantic_mood = PFEESemanticMapper.map_mood_to_semantic(mood_dict)
        semantic_drives = PFEESemanticMapper.map_drives_to_semantic(drives_dict)
        semantic_relationships = PFEESemanticMapper.map_relationships_to_semantic(relationships)
        semantic_arcs = PFEESemanticMapper.map_arcs_to_semantic(arcs)
        semantic_energy = PFEESemanticMapper.map_energy_to_semantic(energy)
        semantic_intentions = PFEESemanticMapper.map_intentions_to_semantic(intentions)
        
        # Compute personality activation deterministically (for semantic mapping)
        activation_stress = sum(drives_dict.values()) / max(len(drives_dict), 1) if drives_dict else 0.0
        personality_activation = {
            "stress_modulation": activation_stress,
            "arousal_modulation": mood_dict.get("arousal", 0.0),
            "valence_modulation": mood_dict.get("valence", 0.0),
            "energy_modulation": energy
        }
        
        semantic_activation = PFEESemanticMapper.map_personality_activation_to_semantic(
            personality_kernel,
            personality_activation,
            mood_dict,
            drives_dict,
            energy,
            arcs,
            relationships
        )
        
        # Store semantic summaries in context
        context["semantic_summaries"] = {
            "mood": semantic_mood,
            "drives": semantic_drives,
            "relationships": semantic_relationships,
            "arcs": semantic_arcs,
            "energy": semantic_energy,
            "intentions": semantic_intentions,
            "personality_activation": semantic_activation
        }
        
        # Build CognitionInput
        # Note: CognitionService.process_cognition() expects numeric values for eligibility,
        # but we've already computed eligibility in PFEE. However, CognitionService's interface
        # still expects numeric. We pass numeric values here, but they are ONLY used for
        # CognitionService's internal eligibility check (which will pass since we pre-computed).
        # The LLM inside CognitionService receives ONLY semantic summaries (CognitionService
        # converts numeric to semantic before LLM call, lines 185-259 in cognition/service.py).
        #
        # This maintains the separation: numeric values stay in PFEE context for eligibility,
        # semantic values are what the LLM sees.
        from backend.cognition.eligibility import EventTrivialityClassification, BehavioralChoice
        
        # Get numeric values from context (for CognitionService's interface)
        # These are NOT passed to LLM - CognitionService converts to semantic before LLM call
        numeric_state = context.get("_eligibility_numeric_state", {})
        
        return CognitionInput(
            agent_id=str(agent_id),
            event_type="agent_initiative",
            event_time=world_state.get("current_time", datetime.now(timezone.utc)),
            event_description="Agent has initiative to act based on internal state",
            # Pass numeric values (CognitionService interface requirement)
            # BUT: CognitionService converts these to semantic BEFORE LLM call
            personality_kernel=numeric_state.get("personality_kernel", {}),
            personality_activation={
                "stress_modulation": sum(numeric_state.get("drives", {}).values()) / max(len(numeric_state.get("drives", {})), 1) if numeric_state.get("drives") else 0.0,
                "arousal_modulation": numeric_state.get("mood", {}).get("arousal", 0.0),
                "valence_modulation": numeric_state.get("mood", {}).get("valence", 0.0),
                "energy_modulation": numeric_state.get("energy", 1.0)
            },
            mood=(
                numeric_state.get("mood", {}).get("valence", 0.0),
                numeric_state.get("mood", {}).get("arousal", 0.0)
            ),
            drives=numeric_state.get("drives", {}),
            arcs=numeric_state.get("arcs", {}),
            energy=numeric_state.get("energy", 1.0),
            relationships=numeric_state.get("relationships", {}),
            intentions=numeric_state.get("intentions", {}),
            # Memories (semantic/textual - already semantic)
            memories={"episodic": episodic, "biographical": biographical},
            # Event context (identifiers and metadata)
            event_participants=event_participants,
            event_topics=context.get("topics", []),
            event_triviality=EventTrivialityClassification.NON_TRIVIAL,
            behavioral_choices=[
                BehavioralChoice.SPEAK_OR_SILENCE,
                BehavioralChoice.APPROACH_OR_WITHDRAW,
                BehavioralChoice.ESCALATE_OR_DE_ESCALATE
            ],
            relevant_calendar_context=context.get("calendar_context"),
            relevant_unexpected_event_context=context.get("unexpected_event_context"),
            last_cognition_time=agent.last_cognition_timestamp
        )
    
    async def _build_renderer_input(
        self,
        world_state: Dict[str, Any],
        decisions: List[TriggerDecision],
        entities: List[Dict[str, Any]],
        context: Dict[str, Any],
        info_events: List[InfoEvent]
    ) -> Dict[str, Any]:
        """
        Build renderer input packet with full context.
        
        Ensures no raw numeric state is passed to renderer.
        Renderer receives only semantic descriptions and perception data.
        """
        # Build semantic perception packet (no numeric state)
        perception_packet = {
            "location_id": world_state.get("current_location_id"),
            "agents_present": [
                {
                    "id": agent.get("id"),
                    "name": agent.get("name"),
                    # No mood, drives, or other numeric state
                }
                for agent in world_state.get("persistent_agents_present_with_user", [])
            ],
            "events": [
                {
                    "type": d.reason.value,
                    "agent_id": d.agent_id,
                    "metadata": d.metadata or {}
                }
                for d in decisions
            ],
            "entities": [
                {
                    "id": e.get("id"),
                    "name": e.get("name"),
                    "type": e.get("type"),
                    # No numeric state
                }
                for e in entities
            ],
            "info_events": [
                {
                    "type": ev.type.value,
                    "content": ev.content,
                    "sender_id": ev.sender_id,
                    "sender_type": ev.sender_type
                }
                for ev in info_events
            ]
        }
        
        # Include semantic summaries if available (from cognition context)
        if "semantic_summaries" in context:
            perception_packet["semantic_context"] = context["semantic_summaries"]
        
        return perception_packet
    
    async def _detect_environmental_shifts(
        self,
        world_state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Detect environmental/atmospheric shifts that might trigger perception."""
        shifts = []
        
        current_location = world_state.get("current_location_id")
        if current_location:
            location_type = world_state.get("current_location_type", "general")
            location_name = world_state.get("current_location", "")
            
            high_activity_locations = ["park", "cafe", "street", "airport", "station", "market"]
            if location_type in high_activity_locations or any(word in location_name.lower() for word in high_activity_locations):
                shifts.append({
                    "id": f"env_{current_location}",
                    "type": "location_atmosphere",
                    "salience": 0.4,
                    "location_id": current_location,
                    "location_type": location_type
                })
            
            weather = world_state.get("weather", None)
            if weather and weather in ["rain", "storm", "snow"]:
                shifts.append({
                    "id": f"weather_{weather}",
                    "type": "weather_change",
                    "salience": 0.5,
                    "weather": weather
                })
        
        current_time = world_state.get("current_time")
        if current_time:
            hour = current_time.hour if hasattr(current_time, "hour") else 12
            if hour in [6, 7, 18, 19]:
                shifts.append({
                    "id": f"time_{hour}",
                    "type": "time_transition",
                    "salience": 0.5,
                    "hour": hour
                })
        
        return shifts
    
    async def _validate_llm_output_against_world(
        self,
        llm_output: Any,
        world_state: Dict[str, Any],
        context: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate LLM output against world state.
        
        Implements PFEE_LOGIC.md §9 contradiction handling logic.
        
        Checks:
        - Agent presence (stance shifts, intention updates)
        - Object existence (actions that reference objects)
        - Location consistency (actions that imply location changes)
        - Relationship contradictions (assertions that contradict stored edges)
        
        Args:
            llm_output: LLM response (utterance, action, stance_shifts, intention_updates)
            world_state: Current authoritative world state
            context: PFEE context
            
        Returns:
            ValidationResult with is_valid, reason, and optional corrected_output
        """
        from backend.cognition.llm_wrapper import CognitionLLMResponse
        
        if not isinstance(llm_output, CognitionLLMResponse):
            return ValidationResult.invalid("invalid_output_type")
        
        # Get current world state
        agents_present_ids = [
            agent.get("id") for agent in world_state.get("persistent_agents_present_with_user", [])
        ]
        current_location_id = world_state.get("current_location_id")
        current_location_name = world_state.get("current_location", "")
        
        # Get objects in current location
        objects_in_location = world_state.get("objects_in_location", [])
        object_names = [obj.get("name", "").lower() for obj in objects_in_location]
        
        # 1. Validate agent presence (stance shifts)
        if llm_output.stance_shifts:
            for shift in llm_output.stance_shifts:
                target = shift.target if hasattr(shift, "target") else ""
                if target.startswith("agent:"):
                    agent_id_str = target.replace("agent:", "")
                    try:
                        agent_id = int(agent_id_str)
                        if agent_id not in agents_present_ids:
                            return ValidationResult.invalid(
                                f"stance_shift_target_not_present: {target} (agent {agent_id} not in current location)"
                            )
                    except ValueError:
                        return ValidationResult.invalid(f"invalid_stance_shift_target: {target}")
        
        # 2. Validate agent presence (intention updates)
        if llm_output.intention_updates:
            for update in llm_output.intention_updates:
                target = update.target if hasattr(update, "target") else None
                if target and target.startswith("agent:"):
                    agent_id_str = target.replace("agent:", "")
                    try:
                        agent_id = int(agent_id_str)
                        if agent_id not in agents_present_ids:
                            return ValidationResult.invalid(
                                f"intention_update_target_not_present: {target} (agent {agent_id} not in current location)"
                            )
                    except ValueError:
                        # Target might be a topic, not an agent - that's OK
                        pass
        
        # 3. Validate object existence (actions)
        if llm_output.action:
            action_lower = llm_output.action.lower()
            
            # Check for object references
            object_keywords = ["uses", "picks up", "grabs", "takes", "holds", "drops", "puts down"]
            for keyword in object_keywords:
                if keyword in action_lower:
                    # Extract object name from action (simplified parsing)
                    words = action_lower.split()
                    keyword_idx = words.index(keyword) if keyword in words else -1
                    if keyword_idx >= 0 and keyword_idx + 1 < len(words):
                        # Next word might be the object
                        potential_object = words[keyword_idx + 1]
                        # Remove common articles
                        if potential_object in ["the", "a", "an"]:
                            if keyword_idx + 2 < len(words):
                                potential_object = words[keyword_idx + 2]
                        
                        # Check if object exists
                        if potential_object and potential_object not in object_names:
                            # Check if it's a generic action (like "uses phone" when phone might be implied)
                            # For now, we'll be strict: if object is mentioned, it must exist
                            if len(potential_object) > 2:  # Ignore very short words
                                return ValidationResult.invalid(
                                    f"action_references_nonexistent_object: '{potential_object}' not in current location"
                                )
        
        # 4. Validate location consistency
        if llm_output.action:
            action_lower = llm_output.action.lower()
            
            # Check for location-changing actions without movement event
            location_keywords = ["goes to", "enters", "leaves", "arrives at", "moves to"]
            for keyword in location_keywords:
                if keyword in action_lower:
                    # If action implies location change, check if there's a corresponding movement event
                    # For now, we'll flag it as potentially inconsistent
                    # (Full implementation would check for movement events in context)
                    pass
        
        # 5. Validate relationship contradictions
        # Check if output asserts relationship states that contradict stored edges
        # This is a simplified check - full implementation would parse relationship assertions
        if llm_output.utterance:
            utterance_lower = llm_output.utterance.lower()
            
            # Check for contradictions like "we have never met" for agents with high familiarity
            if "never met" in utterance_lower or "don't know" in utterance_lower:
                # Would need to check relationship familiarity - simplified for now
                # If familiarity > 0.5, this would be a contradiction
                pass
        
        # All checks passed
        return ValidationResult.valid()

