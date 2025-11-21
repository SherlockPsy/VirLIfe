"""
Renderer Service - RenderEngine

Per CompleteWork.md Phase 6 and MASTER_SPEC §8 (Renderer Service).

The RenderEngine is a dedicated LLM-enabled subsystem responsible ONLY for:
• producing second-person perceptual descriptions for the user
• producing first-person descriptions for any agent POV (if future internal testing)
• respecting the renderer constraints from MASTER_SPEC and Appendix F

ABSOLUTE RULES:
• Renderer MUST describe ONLY sensory perception, never internal states.
• Renderer MUST speak to the user in second-person ("you see…").
• Renderer MUST NOT describe the user's feelings, thoughts, or intentions.
• Renderer MUST NOT break determinism.
• Renderer MUST NOT generate numeric content.
• Renderer MUST use semantic summaries from mapping layer, not numeric state.
• Renderer MUST obey the "no omniscience" rule: only render what is perceptually available.
• Renderer MUST NOT trigger agent cognition.
• Renderer MUST be a dedicated service in backend/renderer/

Implements:
- Plan.md §6 (Renderer Service Wrapper)
- MASTER_SPEC §PART II §8 (Renderer Service)
- APPENDIX A (Renderer POV Rules)
- APPENDIX I (Unexpected Events/Incursions)
- APPENDIX J (Calendars and Obligations)
"""

from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession

from backend.persistence.repo import WorldRepo, AgentRepo, UserRepo
from backend.persistence.models import AgentModel, LocationModel, EventModel, UserModel
from backend.mapping.renderer_context import RendererContext, RendererContextBuilder
from backend.renderer.perception import PerceptionPacket, PerceptionPacketBuilder
from backend.renderer.llm_wrapper import LLMRendererWrapper, RendererOutput
from backend.renderer.router import RendererRouter
from backend.renderer.validators import RendererResponseValidator
from backend.renderer.incursion_rendering import IncursionRenderer
import logging

logger = logging.getLogger(__name__)


class RenderEngine:
    """
    Main renderer service engine.
    
    Per CompleteWork.md Phase 6:
    - render_world_state(perceiver_id) → text
    - render_event(event, perceiver_id) → text
    - render_scene_chunk(context_packet) → text
    
    MUST integrate ONLY with:
    - WorldRepo (location lookup)
    - Mapping layer semantic packets
    - Personality summaries
    
    MUST NOT integrate with CognitionService.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize RenderEngine.
        
        Args:
            session: Database session for accessing world state
        """
        self.session = session
        self.world_repo = WorldRepo(session)
        self.agent_repo = AgentRepo(session)
        self.user_repo = UserRepo(session)
        self.llm_wrapper = LLMRendererWrapper()
        self._previous_perceptions: Dict[str, PerceptionPacket] = {}  # Cache for continuity
    
    async def render_world_state(
        self,
        perceiver_id: int,
        perceiver_type: str = "user"
    ) -> str:
        """
        Render current world state from perceiver's POV.
        
        Per CompleteWork.md Phase 6:
        "render_world_state(perceiver_id) → text"
        
        Args:
            perceiver_id: ID of the perceiver (user or agent)
            perceiver_type: "user" or "agent"
        
        Returns:
            Narrative text describing current perception
        """
        try:
            # Get world state
            world = await self.world_repo.get_world()
            if not world:
                return "The world is empty."
            
            # Get perceiver location
            if perceiver_type == "user":
                user = await self.user_repo.get_user_by_name(f"user_{perceiver_id}")
                if not user:
                    return "You are nowhere."
                location_id = user.location_id if hasattr(user, 'location_id') else None
            else:
                agent = await self.agent_repo.get_agent_by_id(perceiver_id)
                if not agent:
                    return "The perceiver does not exist."
                location_id = agent.location_id
            
            if not location_id:
                return "You are nowhere."
            
            # Get location
            from sqlalchemy import select
            stmt = select(LocationModel).where(LocationModel.id == location_id)
            result = await self.session.execute(stmt)
            location = result.scalars().first()
            
            if not location:
                return "You are in an unknown place."
            
            # Get visible agents in location
            visible_agents = await self.agent_repo.list_agents_in_location(location_id)
            
            # Build perception packet
            perception_packet = await self._build_perception_packet(
                perceiver_id=perceiver_id,
                perceiver_type=perceiver_type,
                location=location,
                visible_agents=visible_agents,
                current_event=None,
                world=world
            )
            
            # Build renderer context
            renderer_context = await self._packet_to_context(
                perception_packet=perception_packet,
                perceiver_id=perceiver_id,
                perceiver_type=perceiver_type,
                visible_agents=visible_agents
            )
            
            # Render using LLM
            output = await self.llm_wrapper.render(renderer_context)
            
            # Validate output
            validator = RendererResponseValidator()
            validation = validator.validate_narrative(
                narrative=output.narrative,
                perceiver_type=perceiver_type,
                visible_entities=[a.name for a in visible_agents],
                event_description=perception_packet.current_event_description
            )
            
            if not validation.is_valid:
                logger.warning(f"Renderer output validation failed: {validation.error_message}")
                # Return a safe fallback
                return self._generate_fallback_narrative(perception_packet, perceiver_type)
            
            # Cache for continuity
            cache_key = f"{perceiver_type}_{perceiver_id}"
            self._previous_perceptions[cache_key] = perception_packet
            
            return output.narrative
            
        except Exception as e:
            logger.error(f"Error in render_world_state: {str(e)}", exc_info=True)
            return "The world fades from view."
    
    async def render_event(
        self,
        event: EventModel,
        perceiver_id: int,
        perceiver_type: str = "user"
    ) -> str:
        """
        Render a specific event from perceiver's POV.
        
        Per CompleteWork.md Phase 6:
        "render_event(event, perceiver_id) → text"
        
        Args:
            event: EventModel to render
            perceiver_id: ID of the perceiver
            perceiver_type: "user" or "agent"
        
        Returns:
            Narrative text describing the event
        """
        try:
            # Get world state
            world = await self.world_repo.get_world()
            if not world:
                return "The world is empty."
            
            # Get perceiver location
            if perceiver_type == "user":
                user = await self.user_repo.get_user_by_name(f"user_{perceiver_id}")
                if not user:
                    return "You are nowhere."
                location_id = user.location_id if hasattr(user, 'location_id') else None
            else:
                agent = await self.agent_repo.get_agent_by_id(perceiver_id)
                if not agent:
                    return "The perceiver does not exist."
                location_id = agent.location_id
            
            if not location_id:
                return "You are nowhere."
            
            # Get location
            from sqlalchemy import select
            stmt = select(LocationModel).where(LocationModel.id == location_id)
            result = await self.session.execute(stmt)
            location = result.scalars().first()
            
            if not location:
                return "You are in an unknown place."
            
            # Get visible agents in location
            visible_agents = await self.agent_repo.list_agents_in_location(location_id)
            
            # Build perception packet with event
            perception_packet = await self._build_perception_packet(
                perceiver_id=perceiver_id,
                perceiver_type=perceiver_type,
                location=location,
                visible_agents=visible_agents,
                current_event=event,
                world=world
            )
            
            # Build renderer context
            renderer_context = await self._packet_to_context(
                perception_packet=perception_packet,
                perceiver_id=perceiver_id,
                perceiver_type=perceiver_type,
                visible_agents=visible_agents
            )
            
            # Render using LLM
            output = await self.llm_wrapper.render(renderer_context)
            
            # Validate output
            validator = RendererResponseValidator()
            validation = validator.validate_narrative(
                narrative=output.narrative,
                perceiver_type=perceiver_type,
                visible_entities=[a.name for a in visible_agents],
                event_description=perception_packet.current_event_description
            )
            
            if not validation.is_valid:
                logger.warning(f"Renderer output validation failed: {validation.error_message}")
                return self._generate_fallback_narrative(perception_packet, perceiver_type)
            
            # Cache for continuity
            cache_key = f"{perceiver_type}_{perceiver_id}"
            self._previous_perceptions[cache_key] = perception_packet
            
            return output.narrative
            
        except Exception as e:
            logger.error(f"Error in render_event: {str(e)}", exc_info=True)
            return "Something happens, but you cannot make it out."
    
    async def render_scene_chunk(
        self,
        context_packet: Dict[str, Any]
    ) -> str:
        """
        Render a scene chunk from a pre-built context packet.
        
        Per CompleteWork.md Phase 6:
        "render_scene_chunk(context_packet) → text"
        
        Args:
            context_packet: Pre-built context dictionary with perception data
        
        Returns:
            Narrative text
        """
        try:
            # Convert context packet to RendererContext
            renderer_context = RendererContext(
                perceiver_name=context_packet.get("perceiver_name", "you"),
                perceiver_type=context_packet.get("perceiver_type", "user"),
                perceiver_id=context_packet.get("perceiver_id"),
                location=context_packet.get("location", "unknown"),
                visible_entities=context_packet.get("visible_entities", []),
                sensory_snapshot=context_packet.get("sensory_snapshot", ""),
                agent_personalities=context_packet.get("agent_personalities", {}),
                event_description=context_packet.get("event_description", ""),
                event_type=context_packet.get("event_type", "routine"),
                perceivable_calendar_context=context_packet.get("perceivable_calendar_context"),
                perceivable_unexpected_event=context_packet.get("perceivable_unexpected_event"),
                scene_mode=context_packet.get("scene_mode", "standard"),
                use_adult_renderer=context_packet.get("use_adult_renderer", False),
                previous_perception=context_packet.get("previous_perception")
            )
            
            # Render using LLM
            output = await self.llm_wrapper.render(renderer_context)
            
            # Validate output
            validator = RendererResponseValidator()
            validation = validator.validate_narrative(
                narrative=output.narrative,
                perceiver_type=renderer_context.perceiver_type,
                visible_entities=renderer_context.visible_entities,
                event_description=renderer_context.event_description
            )
            
            if not validation.is_valid:
                logger.warning(f"Renderer output validation failed: {validation.error_message}")
                # Generate fallback from context
                return self._generate_fallback_from_context(renderer_context)
            
            return output.narrative
            
        except Exception as e:
            logger.error(f"Error in render_scene_chunk: {str(e)}", exc_info=True)
            return "The scene is unclear."
    
    async def _build_perception_packet(
        self,
        perceiver_id: int,
        perceiver_type: str,
        location: LocationModel,
        visible_agents: List[AgentModel],
        current_event: Optional[EventModel],
        world: Any
    ) -> PerceptionPacket:
        """Build a PerceptionPacket from world state."""
        
        # Get previous perception for delta
        cache_key = f"{perceiver_type}_{perceiver_id}"
        previous_perception = self._previous_perceptions.get(cache_key)
        
        # Build visible entities list
        visible_entities_data = []
        for agent in visible_agents:
            # Get observable state (semantic, not numeric)
            observable_state = self._get_observable_agent_state(agent)
            
            visible_entities_data.append({
                "entity_id": f"agent_{agent.id}",
                "name": agent.name,
                "category": "agent",
                "observable_state": observable_state,
                "position_relative_to_perceiver": "nearby",
                "notable_behavior": None  # Could be enhanced with behavior detection
            })
        
        # Determine event description
        if current_event:
            event_description = self._describe_event(current_event)
            event_type = current_event.type or "interaction"
        else:
            event_description = "The scene is quiet."
            event_type = "routine"
        
        # Check for incursions (unexpected events)
        perceivable_incursion = None
        if current_event and current_event.type and "incursion" in current_event.type.lower():
            perceivable_incursion = IncursionRenderer.prepare_incursion_context(
                incursion_description=event_description,
                incursion_type=current_event.type,
                perceiver_type=perceiver_type
            )
        
        # Check for calendar context (perceivable)
        perceivable_calendar = await self._get_perceivable_calendar_context(
            location, visible_agents, world
        )
        
        # Build perception packet
        if perceiver_type == "user":
            packet = PerceptionPacketBuilder.build_user_pov_packet(
                location_name=location.name,
                location_description=location.description or f"The {location.name}",
                visible_agents=visible_entities_data,
                current_event_description=event_description,
                current_event_type=event_type,
                ambient_perceptions=self._get_ambient_perceptions(location),
                perceivable_incursion=perceivable_incursion,
                perceivable_calendar=perceivable_calendar,
                previous_perception=previous_perception,
                pov_focus="environment"
            )
        else:
            packet = PerceptionPacketBuilder.build_agent_pov_packet(
                agent_name=await self._get_agent_name(perceiver_id),
                location_name=location.name,
                location_description=location.description or f"The {location.name}",
                visible_entities=visible_entities_data,
                current_event_description=event_description,
                current_event_type=event_type,
                ambient_perceptions=self._get_ambient_perceptions(location),
                perceivable_incursion=perceivable_incursion,
                perceivable_calendar=perceivable_calendar,
                previous_perception=previous_perception,
                pov_focus="interaction"
            )
        
        return packet
    
    async def _packet_to_context(
        self,
        perception_packet: PerceptionPacket,
        perceiver_id: int,
        perceiver_type: str,
        visible_agents: List[AgentModel]
    ) -> RendererContext:
        """Convert PerceptionPacket to RendererContext."""
        
        # Build agent personalities (semantic only)
        agent_personalities = {}
        for agent in visible_agents:
            # Get personality summary (semantic, not numeric)
            personality_summary = agent.personality_summary or "A person."
            domain_summaries = agent.domain_summaries or {}
            
            # Build personality context
            agent_personalities[agent.name] = {
                "personality_summary": personality_summary,
                "domain_summaries": domain_summaries,
                "dynamic_activation": "Present in the scene.",
                "mood_context": self._get_semantic_mood(agent),
                "energy_context": self._get_semantic_energy(agent)
            }
        
        # Build visible entity names
        visible_names = [e.entity_name for e in perception_packet.visible_entities]
        
        # Build sensory snapshot
        sensory_snapshot = self._build_sensory_snapshot(perception_packet)
        
        # Build renderer context
        context = RendererContextBuilder.build_context(
            perceiver_name=perception_packet.perceiver_name,
            perceiver_type=perceiver_type,
            location=perception_packet.location_name,
            visible_agents=[{
                "agent_name": agent.name,
                "agent_id": agent.id,
                "personality_kernel": agent.personality_kernel or {},
                "domain_summaries": agent.domain_summaries or {},
                "personality_summary": agent.personality_summary or "",
                "mood": {"valence": agent.mood_valence or 0, "arousal": agent.mood_arousal or 0},
                "energy": agent.energy or 0.5,
                "drives": {},
                "arcs": [],
                "relationships": []
            } for agent in visible_agents],
            sensory_snapshot=sensory_snapshot,
            event_description=perception_packet.current_event_description,
            event_type=perception_packet.current_event_type,
            perceiver_id=str(perceiver_id),
            perceivable_calendar_context=perception_packet.perceivable_calendar,
            perceivable_unexpected_event=perception_packet.perceivable_incursion,
            scene_mode="standard",
            use_adult_renderer=False,
            previous_perception=perception_packet.perception_delta.event_occurred if perception_packet.perception_delta else None
        )
        
        return context
    
    def _get_observable_agent_state(self, agent: AgentModel) -> str:
        """Get semantic observable state of agent (no numeric values)."""
        # This should use mapping layer to convert numeric state to semantic
        # For now, return basic observable description
        return f"{agent.name} is present."
    
    def _describe_event(self, event: EventModel) -> str:
        """Describe event in semantic terms."""
        if event.payload:
            # Extract semantic description from payload
            return event.payload.get("description", "Something happens.")
        return "Something happens."
    
    async def _get_perceivable_calendar_context(
        self,
        location: LocationModel,
        visible_agents: List[AgentModel],
        world: Any
    ) -> Optional[str]:
        """Get perceivable calendar/obligation context."""
        # Check for visible calendar items, clocks, etc.
        # This is a simplified version - could be enhanced
        return None
    
    def _get_ambient_perceptions(self, location: LocationModel) -> Dict[str, str]:
        """Get ambient sensory perceptions for location."""
        return {
            "lighting": "normal",
            "sound": "quiet",
            "temperature": "comfortable"
        }
    
    def _build_sensory_snapshot(self, packet: PerceptionPacket) -> str:
        """Build sensory snapshot description from perception packet."""
        parts = []
        
        if packet.ambient_perceptions:
            for sense, desc in packet.ambient_perceptions.items():
                parts.append(f"{sense}: {desc}")
        
        if packet.visible_entities:
            entity_names = [e.entity_name for e in packet.visible_entities]
            parts.append(f"visible: {', '.join(entity_names)}")
        
        return ". ".join(parts) if parts else "The scene is quiet."
    
    def _get_semantic_mood(self, agent: AgentModel) -> str:
        """Get semantic mood description (no numeric values)."""
        # Should use MoodMapper from mapping layer
        return "neutral"
    
    def _get_semantic_energy(self, agent: AgentModel) -> str:
        """Get semantic energy description (no numeric values)."""
        # Should use EnergyMapper from mapping layer
        return "normal"
    
    async def _get_agent_name(self, agent_id: int) -> str:
        """Get agent name by ID."""
        agent = await self.agent_repo.get_agent_by_id(agent_id)
        return agent.name if agent else "Unknown"
    
    def _generate_fallback_narrative(
        self,
        packet: PerceptionPacket,
        perceiver_type: str
    ) -> str:
        """Generate a safe fallback narrative if LLM fails."""
        if perceiver_type == "user":
            if packet.visible_entities:
                names = [e.entity_name for e in packet.visible_entities]
                return f"You see {', '.join(names)} in the {packet.location_name}."
            return f"You are in the {packet.location_name}."
        else:
            if packet.visible_entities:
                names = [e.entity_name for e in packet.visible_entities]
                return f"I see {', '.join(names)} in the {packet.location_name}."
            return f"I am in the {packet.location_name}."
    
    def _generate_fallback_from_context(self, context: RendererContext) -> str:
        """Generate fallback narrative from RendererContext."""
        if context.perceiver_type == "user":
            if context.visible_entities:
                return f"You see {', '.join(context.visible_entities)} in the {context.location}."
            return f"You are in the {context.location}."
        else:
            if context.visible_entities:
                return f"I see {', '.join(context.visible_entities)} in the {context.location}."
            return f"I am in the {context.location}."

