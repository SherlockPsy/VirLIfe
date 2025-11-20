"""
Renderer Context Builder
Phase 4 Implementation

Builds semantic context packets for Renderer LLM calls.
Renderer receives ONLY perception data + personality context.
Ensures NO raw numeric state reaches the LLM.

Implements:
- MASTER_SPEC §PART II §8 (Renderer Service)
- APPENDIX A (Renderer POV Rules)
- docs/cognition_flow.md (perception-only rendering)
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from backend.mapping.semantic_mappers import (
    PersonalityMapper,
    MoodMapper,
    EnergyMapper,
)


@dataclass
class RendererContext:
    """
    Semantic context packet for Renderer LLM.
    
    MUST contain ONLY:
    - perception (what can be sensed)
    - personality context (semantic)
    - event context (what is happening now)
    
    MUST NOT contain:
    - raw numeric psychology of user
    - omniscient internal states
    - raw numeric values
    
    Implements: MASTER_SPEC §APPENDIX A (Renderer POV Rules)
    """
    
    # Perception snapshot
    perceiver_name: str  # Who is perceiving (usually "you" for user, or agent name)
    perceiver_type: str  # "user" or "agent"
    
    # What the perceiver sees/senses
    location: str  # Where the perceiver is
    visible_entities: List[str]  # Who/what is present
    sensory_snapshot: str  # What can be perceived right now
    
    # Agents involved in the scene (personality context only)
    agent_personalities: Dict[str, Dict[str, Any]]  # {agent_name: {summary, domain_summaries, activation}}
    
    # Current event/action context
    event_description: str  # What is happening
    event_type: str  # interaction, conflict, incursion, etc.
    
    # Optional cache-scoping identifier
    perceiver_id: Optional[str] = None  # Unique identifier for cache scoping
    
    # Calendar/obligation context (if perceivable)
    perceivable_calendar_context: Optional[str] = None  # e.g., "clock showing 19:00"
    
    # Unexpected event context (if perceivable)
    perceivable_unexpected_event: Optional[str] = None  # e.g., "key turning in lock, someone arriving"
    
    # Scene mode
    scene_mode: str = "standard"  # "standard", "intimate", "sexual"
    
    # Whether adult-capable renderer should be used
    use_adult_renderer: bool = False
    
    # Previous perception (for continuity)
    previous_perception: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Converts context to dict for JSON serialization.
        """
        return asdict(self)
    
    def to_prompt_dict(self) -> Dict[str, Any]:
        """
        Converts context to renderer-ready dict.
        Clean formatting for LLM consumption.
        """
        return {
            "perceiver": {
                "role": self.perceiver_type,  # "user" or "agent"
                "location": self.location,
            },
            "scene": {
                "present": self.visible_entities,
                "sensory": self.sensory_snapshot,
                "event": self.event_description,
            },
            "agent_context": self.agent_personalities,
            "meta": {
                "scene_mode": self.scene_mode,
                "use_adult_renderer": self.use_adult_renderer,
                "calendar_context": self.perceivable_calendar_context,
                "unexpected_event": self.perceivable_unexpected_event,
            },
            "continuity": {
                "previous_perception": self.previous_perception,
            },
        }


class RendererContextBuilder:
    """
    Builds RendererContext packets for Renderer LLM calls.
    
    Focus: perception + personality of visible agents.
    NO numeric state; all semantic.
    
    Implements:
    - MASTER_SPEC §APPENDIX A (Renderer POV Rules)
    - docs/numeric_semantic_mapping.md
    - BUILDER_CONTRACT §6 (Coding Obligations)
    """
    
    @staticmethod
    def build_context(
        perceiver_name: str,
        perceiver_type: str,  # "user" or "agent"
        location: str,
        visible_agents: List[Dict[str, Any]],  # [{agent_name, agent_id, personality_kernel, mood, energy, ...}, ...]
        sensory_snapshot: str,  # What can be perceived
        event_description: str,
        event_type: str,
        perceiver_id: Optional[str] = None,
        perceivable_calendar_context: Optional[str] = None,
        perceivable_unexpected_event: Optional[str] = None,
        scene_mode: str = "standard",
        use_adult_renderer: bool = False,
        previous_perception: Optional[str] = None,
    ) -> RendererContext:
        """
        Main entry point: builds complete renderer context packet.
        
        Args:
            perceiver_name: Name of perceiver ("you" for user, or agent name)
            perceiver_type: "user" or "agent"
            location: Location name where perceiver is
            visible_agents: List of visible agents with their personality/state
            sensory_snapshot: Semantic description of sensory input
            event_description: What is happening (semantic)
            event_type: Type of event
            perceiver_id: Optional unique identifier for cache scoping (e.g., user UUID)
            perceivable_calendar_context: Perceivable calendar info (e.g., "clock shows 19:00")
            perceivable_unexpected_event: Perceivable incursion (e.g., "key turning")
            scene_mode: "standard", "intimate", or "sexual"
            use_adult_renderer: Whether adult renderer should be used
            previous_perception: Previous perception for continuity
            
        Returns:
            RendererContext (fully semantic)
        """
        
        # Extract visible entity names
        visible_names = [agent.get("agent_name", f"Agent-{agent.get('agent_id')}") for agent in visible_agents]
        
        # Build personality context for visible agents
        agent_personalities = {}
        for agent in visible_agents:
            agent_name = agent.get("agent_name", "Unknown")
            personality_kernel = agent.get("personality_kernel", {})
            domain_summaries = agent.get("domain_summaries", {})
            mood = agent.get("mood", {})
            energy = agent.get("energy", 0.5)
            
            # Compute dynamic activation
            drives = agent.get("drives", {})
            arcs = agent.get("arcs", [])
            relationships = agent.get("relationships", [])
            
            dynamic_activation = PersonalityMapper.compute_dynamic_activation_packet(
                kernel=personality_kernel,
                drives=drives,
                mood=mood,
                arcs=arcs,
                relationships=relationships,
                energy=energy,
            )
            
            # Get stable personality summary
            personality_summary = agent.get("personality_summary", "")
            if not personality_summary:
                # Fallback: compute from kernel
                personality_summary = PersonalityMapper.kernel_to_stable_summary(personality_kernel, name="They")
            
            # Mood and energy for narrative context (optional, for renderer awareness)
            mood_summary = MoodMapper.map_mood(
                mood.get("valence", 0),
                mood.get("arousal", 0)
            )
            energy_summary = EnergyMapper.map_energy(energy)
            
            agent_personalities[agent_name] = {
                "personality_summary": personality_summary,
                "domain_summaries": domain_summaries,
                "dynamic_activation": dynamic_activation,
                "mood_context": mood_summary,
                "energy_context": energy_summary,
            }
        
        return RendererContext(
            perceiver_name=perceiver_name,
            perceiver_type=perceiver_type,
            perceiver_id=perceiver_id,
            location=location,
            visible_entities=visible_names,
            sensory_snapshot=sensory_snapshot,
            agent_personalities=agent_personalities,
            event_description=event_description,
            event_type=event_type,
            perceivable_calendar_context=perceivable_calendar_context,
            perceivable_unexpected_event=perceivable_unexpected_event,
            scene_mode=scene_mode,
            use_adult_renderer=use_adult_renderer,
            previous_perception=previous_perception,
        )
