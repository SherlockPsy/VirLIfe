"""
Incursion Rendering

Renders incursions (unexpected events) as perceptual interruptions.
Surfaces calendar/obligation context through perception.

Per Plan.md §6.6 and MASTER_SPEC §8 (Renderer Service).

"Integrate incursion rendering:
- Render incursions as perceptual interruptions (knocks, arrivals, messages)
- Surface calendar/obligation through perception (clocks, body language, dialogue)
- No assignment of psychology unless from cognition output"
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class IncursionCategory(Enum):
    """Categories of incursions that can be rendered."""
    SENSORY = "sensory"          # Ambient: sounds, drafts, flickers
    IRREGULARITY = "irregularity"  # Entropy: objects fall, noise, etc.
    DIGITAL = "digital"           # Notifications, messages, alerts
    ARRIVAL = "arrival"           # Someone arriving/knocking
    INTERACTION = "interaction"   # Someone trying to engage
    OBLIGATION = "obligation"     # Calendar/time pressure (perceived)


class IncursionRendering(Enum):
    """How to render different incursion types."""
    AMBIENT = "ambient"           # Background sensation (low prominence)
    INTRUSIVE = "intrusive"       # Demanding attention (high prominence)
    CONTEXT = "context"           # Shapes narrative tone (calendar, time pressure)


@dataclass
class IncursionRenderingStrategy:
    """Strategy for rendering a specific incursion."""
    incursion_type: IncursionCategory
    rendering_mode: IncursionRendering
    narrative_template: str  # How to weave into narrative
    prominence: int  # 0-10, how much narrative focus


class IncursionRenderer:
    """
    Renders incursions as perceptual interruptions.
    
    Per Plan.md §6.6:
    "Integrate incursion rendering:
    - Render incursions as perceptual interruptions (knocks, arrivals, messages)
    - Surface calendar/obligation through perception (clocks, body language, dialogue)
    - No assignment of psychology unless from cognition output"
    """
    
    # Incursion rendering strategies
    STRATEGIES = {
        IncursionCategory.SENSORY: IncursionRenderingStrategy(
            incursion_type=IncursionCategory.SENSORY,
            rendering_mode=IncursionRendering.AMBIENT,
            narrative_template="[Weave ambient sensation into narrative as background detail]",
            prominence=2
        ),
        IncursionCategory.IRREGULARITY: IncursionRenderingStrategy(
            incursion_type=IncursionCategory.IRREGULARITY,
            rendering_mode=IncursionRendering.INTRUSIVE,
            narrative_template="[Include small disruption that momentarily breaks focus]",
            prominence=3
        ),
        IncursionCategory.DIGITAL: IncursionRenderingStrategy(
            incursion_type=IncursionCategory.DIGITAL,
            rendering_mode=IncursionRendering.INTRUSIVE,
            narrative_template="[Include notification as perceptual interruption]",
            prominence=5
        ),
        IncursionCategory.ARRIVAL: IncursionRenderingStrategy(
            incursion_type=IncursionCategory.ARRIVAL,
            rendering_mode=IncursionRendering.INTRUSIVE,
            narrative_template="[Describe arrival as sensory event: key in door, footsteps, voice]",
            prominence=8
        ),
        IncursionCategory.INTERACTION: IncursionRenderingStrategy(
            incursion_type=IncursionCategory.INTERACTION,
            rendering_mode=IncursionRendering.INTRUSIVE,
            narrative_template="[Describe interaction attempt as perceived action]",
            prominence=7
        ),
        IncursionCategory.OBLIGATION: IncursionRenderingStrategy(
            incursion_type=IncursionCategory.OBLIGATION,
            rendering_mode=IncursionRendering.CONTEXT,
            narrative_template="[Surface obligation through perceivable context: clocks, body language, dialogue cues]",
            prominence=3
        ),
    }
    
    @staticmethod
    def classify_incursion(
        incursion_type: str,
        incursion_description: str
    ) -> IncursionCategory:
        """
        Classify an incursion for rendering strategy.
        
        Args:
            incursion_type: Type from world/incursions.py (e.g., "incursion_sensory")
            incursion_description: Description of the incursion
        
        Returns:
            IncursionCategory
        """
        incursion_type_lower = incursion_type.lower()
        description_lower = incursion_description.lower()
        
        # Arrival detection
        if any(word in description_lower for word in ["knock", "door", "arrival", "arriving", "approaching", "footstep", "entering"]):
            return IncursionCategory.ARRIVAL
        
        # Interaction detection
        if any(word in description_lower for word in ["call", "message", "text", "speak", "say", "ask", "question"]):
            return IncursionCategory.INTERACTION
        
        # Digital detection
        if "incursion_digital" in incursion_type_lower or any(
            word in description_lower for word in ["notification", "chime", "alert", "message", "text", "phone"]
        ):
            return IncursionCategory.DIGITAL
        
        # Irregularity detection
        if "incursion_irregularity" in incursion_type_lower:
            return IncursionCategory.IRREGULARITY
        
        # Obligation detection (calendar-based)
        if any(word in description_lower for word in ["clock", "time", "appointment", "meeting", "schedule", "deadline"]):
            return IncursionCategory.OBLIGATION
        
        # Default to sensory
        return IncursionCategory.SENSORY
    
    @staticmethod
    def get_rendering_strategy(incursion_category: IncursionCategory) -> IncursionRenderingStrategy:
        """
        Get rendering strategy for incursion category.
        
        Args:
            incursion_category: Classification of incursion
        
        Returns:
            IncursionRenderingStrategy with rendering instructions
        """
        return IncursionRenderer.STRATEGIES.get(
            incursion_category,
            IncursionRenderer.STRATEGIES[IncursionCategory.SENSORY]  # Default fallback
        )
    
    @staticmethod
    def prepare_incursion_context(
        incursion_description: str,
        incursion_type: str,
        perceiver_type: str
    ) -> str:
        """
        Prepare incursion context for inclusion in renderer LLM call.
        
        Args:
            incursion_description: What the incursion is
            incursion_type: Type of incursion
            perceiver_type: Who perceives it ("user" or "agent")
        
        Returns:
            Formatted incursion context string
        """
        category = IncursionRenderer.classify_incursion(incursion_type, incursion_description)
        strategy = IncursionRenderer.get_rendering_strategy(category)
        
        pov = "you" if perceiver_type == "user" else "I"
        
        context = f"""INCURSION (Unexpected Event):
- What: {incursion_description}
- Category: {category.value}
- Rendering: {strategy.rendering_mode.value} (prominence: {strategy.prominence}/10)
- Strategy: {strategy.narrative_template.replace("[", "").replace("]", "")}

Instructions: Weave this incursion into the narrative as something {pov} perceive(s).
Do NOT describe the perceiver's internal reaction.
DO describe the sensory aspect: what {pov} see(s), hear(s), or sense(s).
"""
        return context
    
    @staticmethod
    def should_render_incursion(incursion_category: IncursionCategory) -> bool:
        """
        Determine if incursion should be rendered in current narrative.
        
        Some incursions (very low prominence) might be omitted from narrative.
        
        Args:
            incursion_category: Classification of incursion
        
        Returns:
            True if should be rendered, False if can be omitted
        """
        strategy = IncursionRenderer.get_rendering_strategy(incursion_category)
        # Only render if prominence >= 2 (exclude near-invisible incursions)
        return strategy.prominence >= 2
    
    @staticmethod
    def render_obligation_context(
        calendar_context: Optional[str],
        perceiver_type: str
    ) -> Optional[str]:
        """
        Render obligation/calendar context through perception.
        
        Per Plan.md §6.6:
        "Surface calendar/obligation through perception (clocks, body language, dialogue cues)"
        
        Args:
            calendar_context: Perceivable calendar info (e.g., "clock showing 19:00")
            perceiver_type: "user" or "agent"
        
        Returns:
            Narrative context for obligation, or None if not perceivable
        """
        if not calendar_context:
            return None
        
        pov = "you" if perceiver_type == "user" else "I"
        
        # Parse calendar context for sensory details
        context_lower = calendar_context.lower()
        
        # Time-based narrative cues
        if "19:00" in calendar_context or "7pm" in context_lower or "evening" in context_lower:
            return f"The light outside is beginning to fade. {calendar_context}."
        elif "20:00" in calendar_context or "8pm" in context_lower or "night" in context_lower:
            return f"It's getting late. {calendar_context}."
        elif "09:00" in calendar_context or "9am" in context_lower or "morning" in context_lower:
            return f"The day is just beginning. {calendar_context}."
        elif "clock" in context_lower or "time" in context_lower:
            return calendar_context
        else:
            return calendar_context
