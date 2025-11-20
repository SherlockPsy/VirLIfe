"""
Renderer Router

Routes rendering requests to appropriate LLM model based on event classification.
Per Plan.md §6.2 and MASTER_SPEC §8 (Renderer Service).

"Implement dual-model renderer architecture:
- reasoning model for non-sexual scenes
- adult-capable model for sexual scenes
- routing logic based on event classification"
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class SceneClassification(Enum):
    """Scene content classification for routing."""
    STANDARD = "standard"          # Safe for all audiences
    SUGGESTIVE = "suggestive"      # Flirting, intimate without explicit content
    SEXUAL = "sexual"              # Explicit sexual content
    VIOLENT = "violent"            # Violence (non-sexual)
    EMOTIONAL = "emotional"        # Emotional intensity but not sexual/violent
    ROUTINE = "routine"            # Mundane everyday interaction


class RendererModel(Enum):
    """Available renderer models via Venice.ai."""
    QWEN3_4B = "qwen3-4b"              # Standard reasoning model
    VENICE_UNCENSORED = "venice-uncensored"  # Adult-capable model
    DEFAULT = "qwen3-4b"               # Fallback to qwen3


@dataclass
class RenderingRouting:
    """Routing decision with metadata."""
    target_model: RendererModel
    scene_classification: SceneClassification
    should_use_adult_content_handling: bool
    narrative_tone: str  # "direct", "suggestive", "explicit", etc.
    content_warnings: Optional[str] = None
    
    def __str__(self) -> str:
        return (
            f"RenderingRouting("
            f"model={self.target_model.value}, "
            f"classification={self.scene_classification.value}, "
            f"adult_handling={self.should_use_adult_content_handling})"
        )


class RendererRouter:
    """
    Routes rendering requests to appropriate LLM model.
    
    Per Plan.md §6.2:
    "Implement dual-model renderer architecture:
    - reasoning model for non-sexual scenes
    - adult-capable model for sexual scenes
    - routing logic based on event classification"
    """
    
    # Keywords indicating sexual content (deterministic classification)
    SEXUAL_KEYWORDS = {
        "kiss", "kissed", "kissing",
        "embrace", "embraced", "embracing",
        "touch", "touched", "touching", "caress", "caressing",
        "undress", "undressed", "undressing",
        "sex", "sexual", "intercourse",
        "penetrate", "penetration",
        "orgasm",
        "arousal", "aroused",
        "seduction", "seductive",
        "desire", "lustful",
        "passion", "passionate",
        "intimate", "intimacy",
        "nude", "naked",
        "breast", "penis", "vagina", "cock", "pussy",
        "climax", "cum", "come",
    }
    
    # Keywords indicating violence
    VIOLENT_KEYWORDS = {
        "hit", "punch", "kick", "slap", "strike",
        "stab", "cut", "wound", "bleed", "bleeding",
        "kill", "murder", "death", "die", "dying",
        "attack", "assault", "beat", "beaten",
        "fight", "fighting",
        "weapon",
        "gun", "knife", "sword",
        "violence", "violent",
    }
    
    # Keywords indicating emotional intensity
    EMOTIONAL_KEYWORDS = {
        "cry", "crying", "tears", "weeping",
        "anger", "angry", "furious", "rage",
        "fear", "afraid", "terrified", "scared",
        "sadness", "sad", "despair", "grief",
        "joy", "happy", "delighted",
        "conflict", "argument", "fight", "quarrel",
        "reconciliation", "apology", "forgiveness",
    }
    
    @staticmethod
    def classify_scene(
        event_description: str,
        event_type: str,
        perceiver_type: str,  # "user" or "agent"
        has_explicit_sexual_content: Optional[bool] = None
    ) -> SceneClassification:
        """
        Classify a scene based on event description and type.
        
        Deterministic classification rules:
        1. If explicit sexual content flagged → SEXUAL
        2. If description contains sexual keywords → SEXUAL
        3. If description contains violent keywords → VIOLENT
        4. If description contains emotional keywords → EMOTIONAL
        5. If event_type indicates routine → ROUTINE
        6. Otherwise → STANDARD
        
        Args:
            event_description: Text describing what's happening
            event_type: Type of event (interaction, movement, incursion, etc.)
            perceiver_type: Who's perceiving (user or agent)
            has_explicit_sexual_content: Optional explicit flag
        
        Returns:
            SceneClassification
        """
        # Explicit sexual content flag takes highest priority
        if has_explicit_sexual_content is True:
            return SceneClassification.SEXUAL
        
        description_lower = event_description.lower()
        event_type_lower = event_type.lower()
        
        # Check for sexual content
        for keyword in RendererRouter.SEXUAL_KEYWORDS:
            if keyword in description_lower or keyword in event_type_lower:
                return SceneClassification.SEXUAL
        
        # Check for violence
        for keyword in RendererRouter.VIOLENT_KEYWORDS:
            if keyword in description_lower or keyword in event_type_lower:
                return SceneClassification.VIOLENT
        
        # Check for emotional content
        for keyword in RendererRouter.EMOTIONAL_KEYWORDS:
            if keyword in description_lower or keyword in event_type_lower:
                return SceneClassification.EMOTIONAL
        
        # Routine events
        routine_patterns = ["movement", "walking", "standing", "sitting", "routine", "daily", "normal"]
        if any(p in event_type_lower for p in routine_patterns):
            return SceneClassification.ROUTINE
        
        # Default to standard
        return SceneClassification.STANDARD
    
    @staticmethod
    def route_rendering(
        event_description: str,
        event_type: str,
        perceiver_type: str,
        has_explicit_sexual_content: Optional[bool] = None,
        user_preferences: Optional[dict] = None  # Optional user content preferences
    ) -> RenderingRouting:
        """
        Determine routing for a rendering request.
        
        Args:
            event_description: What's happening
            event_type: Type of event
            perceiver_type: "user" or "agent"
            has_explicit_sexual_content: Optional explicit flag
            user_preferences: Optional dict with keys like {"allow_adult_content": bool}
        
        Returns:
            RenderingRouting with model selection and metadata
        """
        classification = RendererRouter.classify_scene(
            event_description,
            event_type,
            perceiver_type,
            has_explicit_sexual_content
        )
        
        # Check user preferences (default: adult content allowed)
        allow_adult_content = True
        if user_preferences and "allow_adult_content" in user_preferences:
            allow_adult_content = user_preferences["allow_adult_content"]
        
        # Route based on classification
        if classification == SceneClassification.SEXUAL:
            if allow_adult_content:
                return RenderingRouting(
                    target_model=RendererModel.VENICE_UNCENSORED,
                    scene_classification=classification,
                    should_use_adult_content_handling=True,
                    narrative_tone="explicit",
                    content_warnings="sexual content"
                )
            else:
                # User prefers non-explicit; use qwen3 with content filtering
                return RenderingRouting(
                    target_model=RendererModel.QWEN3_4B,
                    scene_classification=classification,
                    should_use_adult_content_handling=False,
                    narrative_tone="suggestive",
                    content_warnings="sexual content (filtered to non-explicit)"
                )
        
        elif classification == SceneClassification.VIOLENT:
            # Violence typically uses standard model with content notes
            return RenderingRouting(
                target_model=RendererModel.QWEN3_4B,
                scene_classification=classification,
                should_use_adult_content_handling=False,
                narrative_tone="direct",
                content_warnings="violence"
            )
        
        elif classification == SceneClassification.EMOTIONAL:
            # Emotional intensity uses standard model
            return RenderingRouting(
                target_model=RendererModel.QWEN3_4B,
                scene_classification=classification,
                should_use_adult_content_handling=False,
                narrative_tone="direct",
                content_warnings=None
            )
        
        elif classification == SceneClassification.ROUTINE:
            # Routine events: minimal processing
            return RenderingRouting(
                target_model=RendererModel.QWEN3_4B,
                scene_classification=classification,
                should_use_adult_content_handling=False,
                narrative_tone="direct",
                content_warnings=None
            )
        
        else:  # STANDARD
            return RenderingRouting(
                target_model=RendererModel.QWEN3_4B,
                scene_classification=classification,
                should_use_adult_content_handling=False,
                narrative_tone="direct",
                content_warnings=None
            )
