"""
Renderer Context Builders

Per CompleteWork.md Phase 6:
"backend/renderer/context_builders.py
 - Build 'perception packets':
     • visible agents
     • visible actions
     • environment cues
     • proxemics
     • incursion semantic summaries
     • calendar context
 - MUST obey renderer context rules (visual, auditory, olfactory IF spec allows)"

This module builds perception packets specifically for the renderer service,
integrating with the perception module and mapping layer.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from backend.persistence.models import AgentModel, LocationModel, EventModel
from backend.renderer.perception import (
    PerceptionPacket,
    PerceptionPacketBuilder,
    PerceivableEntity,
    EntityCategory
)
from backend.renderer.incursion_rendering import IncursionRenderer
from backend.mapping.renderer_context import RendererContext, RendererContextBuilder
import logging

logger = logging.getLogger(__name__)


class RendererPerceptionBuilder:
    """
    Builds perception packets for the renderer service.
    
    Per CompleteWork.md Phase 6:
    - Builds perception packets with:
      • visible agents
      • visible actions
      • environment cues
      • proxemics
      • incursion semantic summaries
      • calendar context
    """
    
    @staticmethod
    async def build_perception_packet(
        session: AsyncSession,
        perceiver_id: int,
        perceiver_type: str,  # "user" or "agent"
        location: LocationModel,
        visible_agents: List[AgentModel],
        current_event: Optional[EventModel] = None,
        previous_perception: Optional[PerceptionPacket] = None
    ) -> PerceptionPacket:
        """
        Build a complete perception packet for rendering.
        
        Args:
            session: Database session
            perceiver_id: ID of perceiver
            perceiver_type: "user" or "agent"
            location: LocationModel where perceiver is
            visible_agents: List of AgentModel visible in location
            current_event: Optional EventModel for current event
            previous_perception: Optional previous PerceptionPacket for delta
        
        Returns:
            PerceptionPacket ready for rendering
        """
        # Build visible entities
        visible_entities_data = []
        for agent in visible_agents:
            entity_data = await RendererPerceptionBuilder._build_agent_entity(
                agent, perceiver_id
            )
            visible_entities_data.append(entity_data)
        
        # Determine event description
        event_description, event_type = RendererPerceptionBuilder._describe_event(
            current_event
        )
        
        # Check for incursions
        perceivable_incursion = None
        if current_event and current_event.type:
            if "incursion" in current_event.type.lower():
                perceivable_incursion = IncursionRenderer.prepare_incursion_context(
                    incursion_description=event_description,
                    incursion_type=current_event.type,
                    perceiver_type=perceiver_type
                )
        
        # Get calendar context (perceivable)
        perceivable_calendar = await RendererPerceptionBuilder._get_calendar_context(
            location, visible_agents
        )
        
        # Get environment cues
        ambient_perceptions = RendererPerceptionBuilder._get_environment_cues(location)
        
        # Build perception packet
        if perceiver_type == "user":
            packet = PerceptionPacketBuilder.build_user_pov_packet(
                location_name=location.name,
                location_description=location.description or f"The {location.name}",
                visible_agents=visible_entities_data,
                current_event_description=event_description,
                current_event_type=event_type,
                ambient_perceptions=ambient_perceptions,
                perceivable_incursion=perceivable_incursion,
                perceivable_calendar=perceivable_calendar,
                previous_perception=previous_perception,
                pov_focus="environment"
            )
        else:
            # Get agent name
            from backend.persistence.repo import AgentRepo
            agent_repo = AgentRepo(session)
            agent = await agent_repo.get_agent_by_id(perceiver_id)
            agent_name = agent.name if agent else "Unknown"
            
            packet = PerceptionPacketBuilder.build_agent_pov_packet(
                agent_name=agent_name,
                location_name=location.name,
                location_description=location.description or f"The {location.name}",
                visible_entities=visible_entities_data,
                current_event_description=event_description,
                current_event_type=event_type,
                ambient_perceptions=ambient_perceptions,
                perceivable_incursion=perceivable_incursion,
                perceivable_calendar=perceivable_calendar,
                previous_perception=previous_perception,
                pov_focus="interaction"
            )
        
        return packet
    
    @staticmethod
    async def _build_agent_entity(
        agent: AgentModel,
        perceiver_id: int
    ) -> Dict[str, Any]:
        """
        Build perceivable entity data for an agent.
        
        Includes:
        - Observable state (semantic, not numeric)
        - Proxemics (position relative to perceiver)
        - Visible actions
        """
        # Get observable state (semantic description)
        observable_state = RendererPerceptionBuilder._get_observable_state(agent)
        
        # Determine proxemics (position relative to perceiver)
        proxemics = RendererPerceptionBuilder._determine_proxemics(agent, perceiver_id)
        
        # Get visible actions
        notable_behavior = RendererPerceptionBuilder._get_visible_actions(agent)
        
        return {
            "entity_id": f"agent_{agent.id}",
            "name": agent.name,
            "category": "agent",
            "observable_state": observable_state,
            "position_relative_to_perceiver": proxemics,
            "notable_behavior": notable_behavior
        }
    
    @staticmethod
    def _get_observable_state(agent: AgentModel) -> str:
        """
        Get semantic observable state of agent.
        
        MUST NOT include numeric values.
        MUST only include what can be perceived.
        """
        # This should use mapping layer for semantic conversion
        # For now, return basic observable description
        parts = []
        
        # Observable physical state
        if hasattr(agent, 'energy') and agent.energy:
            if agent.energy < 0.3:
                parts.append("appears tired")
            elif agent.energy > 0.7:
                parts.append("seems energetic")
        
        # Observable mood (from behavior, not internal state)
        if hasattr(agent, 'mood_valence') and agent.mood_valence:
            if agent.mood_valence < -0.3:
                parts.append("looks downcast")
            elif agent.mood_valence > 0.3:
                parts.append("seems cheerful")
        
        if parts:
            return f"{agent.name} {', '.join(parts)}."
        return f"{agent.name} is present."
    
    @staticmethod
    def _determine_proxemics(
        agent: AgentModel,
        perceiver_id: int
    ) -> str:
        """
        Determine proxemics (spatial relationship).
        
        Options: "nearby", "across room", "distant", "adjacent", etc.
        """
        # Simplified: could be enhanced with actual spatial calculations
        if agent.id == perceiver_id:
            return "self"
        return "nearby"
    
    @staticmethod
    def _get_visible_actions(agent: AgentModel) -> Optional[str]:
        """
        Get visible actions/behavior of agent.
        
        MUST only include observable behavior, not internal states.
        """
        # Could be enhanced with behavior detection from agent state
        # For now, return None (no notable behavior)
        return None
    
    @staticmethod
    def _describe_event(event: Optional[EventModel]) -> tuple[str, str]:
        """
        Describe event in semantic terms.
        
        Returns:
            (description, event_type)
        """
        if not event:
            return ("The scene is quiet.", "routine")
        
        event_type = event.type or "interaction"
        
        if event.payload:
            description = event.payload.get("description", "Something happens.")
        else:
            description = "Something happens."
        
        return (description, event_type)
    
    @staticmethod
    async def _get_calendar_context(
        location: LocationModel,
        visible_agents: List[AgentModel]
    ) -> Optional[str]:
        """
        Get perceivable calendar/obligation context.
        
        Per APPENDIX J: Must be perceivable (clocks, dialogue, behavior).
        """
        # Check for visible calendar items, clocks, etc.
        # This is a simplified version - could be enhanced
        # For now, return None (no perceivable calendar context)
        return None
    
    @staticmethod
    def _get_environment_cues(location: LocationModel) -> Dict[str, str]:
        """
        Get environment cues (visual, auditory, olfactory).
        
        Per CompleteWork.md: MUST obey renderer context rules.
        """
        cues = {}
        
        # Visual cues
        if location.description:
            # Extract lighting from description if available
            if "dim" in location.description.lower():
                cues["lighting"] = "dim"
            elif "bright" in location.description.lower():
                cues["lighting"] = "bright"
            else:
                cues["lighting"] = "normal"
        else:
            cues["lighting"] = "normal"
        
        # Auditory cues
        cues["sound"] = "quiet"  # Default
        
        # Olfactory cues (if spec allows)
        # For now, omit unless explicitly needed
        
        return cues

