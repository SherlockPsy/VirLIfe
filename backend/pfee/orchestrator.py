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

from backend.cognition.service import CognitionService, CognitionInput
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
            
            # 3. Build LLM inputs (semantic only, no numeric state)
            cognition_input = await self._build_cognition_input(
                world_state, decisions, entities, context
            )
            renderer_input = await self._build_renderer_input(
                world_state, decisions, entities, context, info_events
            )
            
            # 4. Call LLM services
            cognition_output = None
            if cognition_input:
                try:
                    cognition_result = self.cognition_service.process_cognition(cognition_input)
                    if cognition_result.was_eligible and cognition_result.llm_response:
                        cognition_output = {
                            "agent_id": cognition_result.agent_id,
                            "utterance": cognition_result.llm_response.utterance,
                            "action": cognition_result.llm_response.action,
                            "stance_shifts": [
                                {
                                    "target": shift.get("target"),
                                    "description": shift.get("description")
                                }
                                for shift in (cognition_result.llm_response.stance_shifts or [])
                            ],
                            "intention_updates": [
                                {
                                    "operation": update.get("operation"),
                                    "type": update.get("type"),
                                    "target": update.get("target"),
                                    "horizon": update.get("horizon"),
                                    "description": update.get("description")
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
            
            # 5. Integrate consequences
            updated_world_state = await self.consequence_integrator.apply_perception_outcome(
                cognition_output, renderer_output, world_state
            )
            
            # 6. Log
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
    
    async def _build_cognition_input(
        self,
        world_state: Dict[str, Any],
        decisions: List[TriggerDecision],
        entities: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> Optional[CognitionInput]:
        """Build complete cognition input packet (semantic only)."""
        # Find agent initiative decisions
        agent_decisions = [d for d in decisions if d.reason == TriggerReason.AGENT_INITIATIVE]
        if not agent_decisions:
            return None
        
        # Use first agent (handle multiple in future iterations)
        agent_id = agent_decisions[0].agent_id
        if not agent_id:
            return None
        
        # Load agent with all relationships
        agent = await self.agent_repo.get_agent_by_id(agent_id)
        if not agent:
            return None
        
        # Load agent's arcs
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
        
        # Load agent's intentions
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
        
        # Load agent's relationships
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
        
        # Load agent's memories
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
        
        # Classify event triviality
        from backend.cognition.eligibility import EventTrivialityClassification, BehavioralChoice
        event_triviality = EventTrivialityClassification.NON_TRIVIAL
        
        behavioral_choices = [
            BehavioralChoice.SPEAK_OR_SILENCE,
            BehavioralChoice.APPROACH_OR_WITHDRAW,
            BehavioralChoice.ESCALATE_OR_DE_ESCALATE
        ]
        
        # Compute personality activation deterministically
        mood_valence = agent.mood.get("valence", 0.0) if isinstance(agent.mood, dict) else 0.0
        mood_arousal = agent.mood.get("arousal", 0.0) if isinstance(agent.mood, dict) else 0.0
        
        drives_dict = {
            k: (v.get("level", 0.0) if isinstance(v, dict) else v)
            for k, v in (agent.drives or {}).items()
        }
        
        activation_stress = sum(drives_dict.values()) / max(len(drives_dict), 1) if drives_dict else 0.0
        
        personality_activation = {
            "stress_modulation": activation_stress,
            "arousal_modulation": mood_arousal,
            "valence_modulation": mood_valence,
            "energy_modulation": agent.energy or 1.0
        }
        
        # Build complete CognitionInput
        return CognitionInput(
            agent_id=str(agent_id),
            event_type="agent_initiative",
            event_time=world_state.get("current_time", datetime.now(timezone.utc)),
            event_description="Agent has initiative to act based on internal state",
            personality_kernel=agent.personality_kernel or {},
            personality_activation=personality_activation,
            mood=(mood_valence, mood_arousal),
            drives=drives_dict,
            arcs=arcs,
            energy=agent.energy or 1.0,
            relationships=relationships,
            intentions=intentions,
            memories={"episodic": episodic, "biographical": biographical},
            event_participants=event_participants,
            event_topics=context.get("topics", []),
            event_triviality=event_triviality,
            behavioral_choices=behavioral_choices,
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
        """Build renderer input packet with full context."""
        return {
            "world_state": world_state,
            "decisions": [
                {
                    "reason": d.reason.value,
                    "agent_id": d.agent_id,
                    "metadata": d.metadata or {}
                }
                for d in decisions
            ],
            "entities": entities,
            "info_events": [
                {
                    "type": ev.type.value,
                    "content": ev.content,
                    "sender_id": ev.sender_id,
                    "sender_type": ev.sender_type
                }
                for ev in info_events
            ],
            "context": context
        }
    
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

