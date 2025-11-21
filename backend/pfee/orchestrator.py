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
from backend.pfee.validation import ValidationResult, validate_llm_output_against_world

from backend.cognition.service import CognitionService, SemanticCognitionInput
from backend.mapping.semantic_mappers import PersonalityMapper
from backend.cognition.salience import SalienceCalculator
from backend.cognition.meaningfulness import MeaningfulnessCalculator
from backend.cognition.eligibility import (
    CognitionEligibilityChecker,
    EventTrivialityClassification,
    BehavioralChoice,
    BehavioralChoiceType,
)
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
    
    def __init__(
        self,
        session: AsyncSession,
        *,
        cognition_service: Optional[CognitionService] = None,
        render_engine: Optional[RenderEngine] = None
    ):
        self.session = session
        self.trigger_evaluator = TriggerEvaluator(session)
        self.entity_manager = EntityPersistenceManager(session)
        self.potential_resolver = PotentialResolver(session)
        self.consequence_integrator = ConsequenceIntegrator(session)
        self.time_manager = TimeAndContinuityManager(session)
        self.influence_manager = InfluenceFieldManager(session)
        self.info_event_manager = InformationEventManager(session)
        self.logger = PFEELogger(session)
        
        self.cognition_service = cognition_service or CognitionService()
        self.render_engine = render_engine or RenderEngine(session)
        
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

            # Handle explicit time instructions before evaluating triggers
            if optional_user_action:
                world_state = await self.time_manager.handle_user_time_instruction(
                    optional_user_action, world_state
                )
            
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
                    cognition_result = self.cognition_service.process_semantic_cognition(cognition_input)
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
                            # Deterministic fallback (silence + no action)
                            if validation_result.corrected_output:
                                fallback = validation_result.corrected_output.copy()
                                fallback["agent_id"] = cognition_result.agent_id
                                fallback.setdefault("stance_shifts", [])
                                fallback.setdefault("intention_updates", [])
                                cognition_output = fallback
                            else:
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

            # Mark information events as processed once handled
            for info_event in info_events:
                await self.info_event_manager.mark_event_processed(info_event.id)
            
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
        
        original_drives = agent.drives or {}
        drive_levels = {
            k: (v.get("level", 0.0) if isinstance(v, dict) else v)
            for k, v in original_drives.items()
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
            drive_levels=drive_levels,
            arcs=arcs,
            agent_relationships=relationships,
            agent_intentions=intentions
        )
        
        m_score = MeaningfulnessCalculator.compute_m_score(
            salience_context=salience_context,
            drive_levels=drive_levels,
            arcs=arcs,
            relationships=relationships,
            energy=agent.energy or 1.0
        )
        
        # Check eligibility
        event_triviality = EventTrivialityClassification.SIGNIFICANT
        behavioral_choices = [
            BehavioralChoice(
                choice_type=BehavioralChoiceType.RESPONSE_TO_DIRECT_ADDRESS,
                description="Decide whether to respond verbally or remain silent.",
                stakes=0.5,
            ),
            BehavioralChoice(
                choice_type=BehavioralChoiceType.WITHDRAWAL_VS_ENGAGEMENT,
                description="Choose to lean in or withdraw from the interaction.",
                stakes=0.4,
            ),
            BehavioralChoice(
                choice_type=BehavioralChoiceType.ESCALATION_VS_DEESCALATION,
                description="Consider escalating or de-escalating the emotional tone.",
                stakes=0.35,
            ),
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
            "drives": original_drives,
            "drive_levels": drive_levels,
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
    ) -> Optional[SemanticCognitionInput]:
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
        drive_profiles = numeric_state.get("drives", {})
        drive_levels = numeric_state.get("drive_levels", {})
        relationships = numeric_state.get("relationships", {})
        arcs = numeric_state.get("arcs", {})
        energy = numeric_state.get("energy", 1.0)
        intentions = numeric_state.get("intentions", {})
        personality_kernel = numeric_state.get("personality_kernel", {})
        
        # Create semantic summaries (NO numeric values)
        semantic_mood = PFEESemanticMapper.map_mood_to_semantic(mood_dict)
        semantic_drives = PFEESemanticMapper.map_drives_to_semantic(drive_profiles)
        semantic_relationships = PFEESemanticMapper.map_relationships_to_semantic(relationships)
        semantic_arcs = PFEESemanticMapper.map_arcs_to_semantic(arcs)
        semantic_energy = PFEESemanticMapper.map_energy_to_semantic(energy)
        semantic_intentions = PFEESemanticMapper.map_intentions_to_semantic(intentions)
        
        # Compute personality activation deterministically (for semantic mapping)
        activation_stress = (
            sum(drive_levels.values()) / max(len(drive_levels), 1) if drive_levels else 0.0
        )
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
            drive_profiles,
            energy,
            arcs,
            relationships
        )

        personality_kernel = numeric_state.get("personality_kernel", {})
        personality_stable = PersonalityMapper.kernel_to_stable_summary(personality_kernel)
        personality_domain = PersonalityMapper.kernel_to_domain_summaries(personality_kernel)
        semantic_personality = {
            "stable_summary": personality_stable,
            "domain_summaries": personality_domain
        }
        
        # Store semantic summaries in context for renderer/validation
        context["semantic_summaries"] = {
            "personality": semantic_personality,
            "personality_activation": semantic_activation,
            "mood": semantic_mood,
            "drives": semantic_drives,
            "relationships": semantic_relationships,
            "arcs": semantic_arcs,
            "energy": semantic_energy,
            "intentions": semantic_intentions
        }
        
        eligibility_metadata = {
            "is_eligible": eligibility_result.get("is_eligible", True),
            "eligibility_result": eligibility_result.get("eligibility_result")
        }
        
        return SemanticCognitionInput(
            agent_id=str(agent_id),
            event_type="agent_initiative",
            event_time=world_state.get("current_time", datetime.now(timezone.utc)),
            event_description="Agent has initiative to act based on internal state",
            personality=semantic_personality,
            personality_activation=semantic_activation,
            mood_summary=semantic_mood,
            drives_summary=semantic_drives,
            relationships_summary=semantic_relationships,
            arcs_summary=semantic_arcs,
            energy_summary=semantic_energy,
            intentions_summary=semantic_intentions,
            memories={"episodic": episodic, "biographical": biographical},
            event_participants=event_participants,
            event_topics=context.get("topics", []),
            event_triviality=EventTrivialityClassification.SIGNIFICANT,
            behavioral_choices=[
                BehavioralChoice(
                    choice_type=BehavioralChoiceType.RESPONSE_TO_DIRECT_ADDRESS,
                    description="Respond verbally or remain silent.",
                    stakes=0.5,
                ),
                BehavioralChoice(
                    choice_type=BehavioralChoiceType.WITHDRAWAL_VS_ENGAGEMENT,
                    description="Approach or withdraw physically.",
                    stakes=0.4,
                ),
                BehavioralChoice(
                    choice_type=BehavioralChoiceType.ESCALATION_VS_DEESCALATION,
                    description="Escalate or soften the exchange.",
                    stakes=0.35,
                ),
            ],
            relevant_calendar_context=context.get("calendar_context"),
            relevant_unexpected_event_context=context.get("unexpected_event_context"),
            eligibility_metadata=eligibility_metadata
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
        semantic_context = context.get("semantic_summaries", {})
        
        perception_packet = {
            "location_id": world_state.get("current_location_id"),
            "location_name": world_state.get("current_location"),
            "time": world_state.get("current_time"),
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
        
        if semantic_context:
            perception_packet["semantic_context"] = semantic_context
        
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
        return validate_llm_output_against_world(llm_output, world_state, context)

