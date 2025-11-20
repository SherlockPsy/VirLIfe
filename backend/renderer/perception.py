"""
Perception Packet Builder

Builds perception-focused context packets for narrative rendering.
Per Plan.md §6.1 and MASTER_SPEC §8 (Renderer Service).

"The Renderer Service MUST:
- render ONLY perception (what can be sensed or reasonably inferred perceptually)
- speak to THE HUMAN USER in second person ('you…') when describing THE HUMAN USER's POV
- avoid omniscient narration of internal states
- avoid describing THE HUMAN USER's internal state"
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set
from enum import Enum


class EntityCategory(Enum):
    """Categories of visible/perceivable entities."""
    AGENT = "agent"
    OBJECT = "object"
    LOCATION_FEATURE = "location_feature"
    AMBIENT = "ambient"  # lights, sounds, weather, atmosphere


@dataclass
class PerceivableEntity:
    """A single visible entity in the perception snapshot."""
    entity_id: str
    entity_name: str
    category: EntityCategory
    observable_state: str  # Semantic description of what can be observed
    position_relative_to_perceiver: Optional[str] = None  # "nearby", "across room", etc.
    notable_behavior: Optional[str] = None  # Observable behavior only


@dataclass
class PerceptionDelta:
    """Changes since last perception (for continuity)."""
    newly_visible: List[str] = field(default_factory=list)  # Entity names now visible
    no_longer_visible: List[str] = field(default_factory=list)  # Entity names no longer visible
    changed_state: Dict[str, str] = field(default_factory=dict)  # {entity_name: new_observable_state}
    event_occurred: Optional[str] = None  # New event since last perception


@dataclass
class PerceptionPacket:
    """Complete perception snapshot for renderer."""
    perceiver_name: str
    perceiver_type: str  # "user" or "agent"
    
    # Location perception
    location_name: str
    location_description: str  # What the location looks like
    
    # Entity perception
    visible_entities: List[PerceivableEntity] = field(default_factory=list)
    
    # What's happening now (observable facts only)
    current_event_description: str = ""  # What is happening (perception-based)
    current_event_type: str = ""  # interaction, movement, incursion, etc.
    
    # Ambient perception
    ambient_perceptions: Dict[str, str] = field(default_factory=dict)  # {type: description}
    # e.g., {"sounds": "quiet", "lighting": "dim evening light", "temperature": "cold draft"}
    
    # Delta from previous render (for narrative continuity)
    perception_delta: Optional[PerceptionDelta] = None
    
    # Incursion/interruption perception
    perceivable_incursion: Optional[str] = None  # e.g., "knock on door", "phone buzzing"
    
    # Calendar/obligation perception
    perceivable_calendar: Optional[str] = None  # e.g., "wall clock shows 19:00"
    
    # POV metadata
    pov_focus: str = "environment"  # What should narrative emphasize?
    # Options: environment, action, interaction, reaction, thought
    
    def perceivable_agent_names(self) -> Set[str]:
        """Return set of visible agent names (not user)."""
        return {
            entity.entity_name
            for entity in self.visible_entities
            if entity.category == EntityCategory.AGENT
        }


class PerceptionPacketBuilder:
    """
    Builds perception-focused context for rendering.
    
    Key Constraints (MASTER_SPEC §8):
    - ONLY render perception (what can be sensed)
    - Second-person POV for user
    - First-person for agents
    - NO omniscient internal state narration
    - NO description of user's internal state
    - NO invented events
    
    Implements: Plan.md §6.1
    """
    
    @staticmethod
    def build_perception_packet(
        perceiver_name: str,
        perceiver_type: str,  # "user" or "agent"
        location_name: str,
        location_description: str,
        visible_entities: List[Dict[str, Any]],  # [{entity_id, name, category, observable_state, ...}, ...]
        current_event_description: str,
        current_event_type: str,
        ambient_perceptions: Optional[Dict[str, str]] = None,
        perceivable_incursion: Optional[str] = None,
        perceivable_calendar: Optional[str] = None,
        previous_perception: Optional['PerceptionPacket'] = None,
        pov_focus: str = "environment"
    ) -> PerceptionPacket:
        """
        Build a complete perception packet.
        
        Args:
            perceiver_name: Who is perceiving (user name or agent name)
            perceiver_type: "user" or "agent"
            location_name: Name of location
            location_description: Semantic description of location
            visible_entities: List of visible entity dicts
            current_event_description: What is happening (perception-based, no user psychology)
            current_event_type: Type of event (interaction, movement, incursion, etc.)
            ambient_perceptions: Dict of ambient sensory info (sounds, lighting, etc.)
            perceivable_incursion: Unexpected event if perceivable (knock, arrival, etc.)
            perceivable_calendar: Calendar context if perceivable (clock, dialogue mention, etc.)
            previous_perception: Previous perception packet for delta computation
            pov_focus: What should narrative focus on
        
        Returns:
            PerceptionPacket
        """
        # Build perceivable entity list
        perceivable_entities = []
        for entity_data in visible_entities:
            try:
                category = EntityCategory[entity_data.get("category", "AGENT").upper()]
            except KeyError:
                category = EntityCategory.AGENT
            
            entity = PerceivableEntity(
                entity_id=entity_data.get("entity_id", ""),
                entity_name=entity_data.get("name", entity_data.get("entity_name", "")),
                category=category,
                observable_state=entity_data.get("observable_state", ""),
                position_relative_to_perceiver=entity_data.get("position_relative_to_perceiver"),
                notable_behavior=entity_data.get("notable_behavior")
            )
            perceivable_entities.append(entity)
        
        # Compute perception delta if previous perception exists
        perception_delta = None
        if previous_perception:
            previous_visible = {e.entity_name for e in previous_perception.visible_entities}
            current_visible = {e.entity_name for e in perceivable_entities}
            
            perception_delta = PerceptionDelta(
                newly_visible=list(current_visible - previous_visible),
                no_longer_visible=list(previous_visible - current_visible),
                event_occurred=current_event_description if current_event_description != previous_perception.current_event_description else None
            )
            
            # Track state changes for entities that remain visible
            for entity in perceivable_entities:
                prev_entity = next(
                    (e for e in previous_perception.visible_entities if e.entity_name == entity.entity_name),
                    None
                )
                if prev_entity and entity.observable_state != prev_entity.observable_state:
                    perception_delta.changed_state[entity.entity_name] = entity.observable_state
        
        if ambient_perceptions is None:
            ambient_perceptions = {}
        
        return PerceptionPacket(
            perceiver_name=perceiver_name,
            perceiver_type=perceiver_type,
            location_name=location_name,
            location_description=location_description,
            visible_entities=perceivable_entities,
            current_event_description=current_event_description,
            current_event_type=current_event_type,
            ambient_perceptions=ambient_perceptions,
            perception_delta=perception_delta,
            perceivable_incursion=perceivable_incursion,
            perceivable_calendar=perceivable_calendar,
            pov_focus=pov_focus
        )
    
    @staticmethod
    def build_user_pov_packet(
        location_name: str,
        location_description: str,
        visible_agents: List[Dict[str, Any]],  # Agent names, observable states
        current_event_description: str,
        current_event_type: str,
        ambient_perceptions: Optional[Dict[str, str]] = None,
        perceivable_incursion: Optional[str] = None,
        perceivable_calendar: Optional[str] = None,
        previous_perception: Optional['PerceptionPacket'] = None,
        pov_focus: str = "environment"
    ) -> PerceptionPacket:
        """
        Convenience method for building user POV packets.
        
        Automatically sets perceiver to "user" with second-person focus.
        
        Args:
            Same as build_perception_packet, minus perceiver_name/type
            
        Returns:
            PerceptionPacket with perceiver_type="user"
        """
        return PerceptionPacketBuilder.build_perception_packet(
            perceiver_name="you",  # User always "you" in second-person POV
            perceiver_type="user",
            location_name=location_name,
            location_description=location_description,
            visible_entities=visible_agents,
            current_event_description=current_event_description,
            current_event_type=current_event_type,
            ambient_perceptions=ambient_perceptions,
            perceivable_incursion=perceivable_incursion,
            perceivable_calendar=perceivable_calendar,
            previous_perception=previous_perception,
            pov_focus=pov_focus
        )
    
    @staticmethod
    def build_agent_pov_packet(
        agent_name: str,
        location_name: str,
        location_description: str,
        visible_entities: List[Dict[str, Any]],  # Including other agents
        current_event_description: str,
        current_event_type: str,
        ambient_perceptions: Optional[Dict[str, str]] = None,
        perceivable_incursion: Optional[str] = None,
        perceivable_calendar: Optional[str] = None,
        previous_perception: Optional['PerceptionPacket'] = None,
        pov_focus: str = "interaction"
    ) -> PerceptionPacket:
        """
        Convenience method for building agent POV packets.
        
        Automatically sets perceiver to agent name (first-person focus).
        
        Args:
            agent_name: Name of the perceiving agent
            Other args same as build_perception_packet
            
        Returns:
            PerceptionPacket with perceiver_type="agent"
        """
        return PerceptionPacketBuilder.build_perception_packet(
            perceiver_name=agent_name,
            perceiver_type="agent",
            location_name=location_name,
            location_description=location_description,
            visible_entities=visible_entities,
            current_event_description=current_event_description,
            current_event_type=current_event_type,
            ambient_perceptions=ambient_perceptions,
            perceivable_incursion=perceivable_incursion,
            perceivable_calendar=perceivable_calendar,
            previous_perception=previous_perception,
            pov_focus=pov_focus
        )
