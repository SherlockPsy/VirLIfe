"""
Renderer Service Module

Converts world state + cognition output into user-facing narrative.
Per MASTER_SPEC §8: Perception-only, second-person POV, no user simulation.

Submodules:
- perception: PerceptionPacketBuilder (convert world state to perception packets)
- router: RendererRouter (route events to appropriate LLM model)
- llm_wrapper: LLMRendererWrapper (call LLM with perception context)
- validators: Response validation (reject invalid outputs)
"""

from backend.renderer.perception import (
    EntityCategory,
    PerceivableEntity,
    PerceptionDelta,
    PerceptionPacket,
    PerceptionPacketBuilder,
)

from backend.renderer.router import (
    SceneClassification,
    RendererModel,
    RenderingRouting,
    RendererRouter,
)

from backend.renderer.llm_wrapper import (
    RendererOutput,
    RendererSystemPrompt,
    LLMRendererWrapper,
)

from backend.renderer.validators import (
    ValidationResult,
    RendererResponseValidator,
)

from backend.renderer.incursion_rendering import (
    IncursionCategory,
    IncursionRendering,
    IncursionRenderingStrategy,
    IncursionRenderer,
)

from backend.renderer.service import RenderEngine
from backend.renderer.context_builders import RendererPerceptionBuilder

__all__ = [
    # Perception
    "EntityCategory",
    "PerceivableEntity",
    "PerceptionDelta",
    "PerceptionPacket",
    "PerceptionPacketBuilder",
    # Router
    "SceneClassification",
    "RendererModel",
    "RenderingRouting",
    "RendererRouter",
    # LLM Wrapper
    "RendererOutput",
    "RendererSystemPrompt",
    "LLMRendererWrapper",
    # Validators
    "ValidationResult",
    "RendererResponseValidator",
    # Incursion Rendering
    "IncursionCategory",
    "IncursionRendering",
    "IncursionRenderingStrategy",
    "IncursionRenderer",
    # Service
    "RenderEngine",
    # Context Builders
    "RendererPerceptionBuilder",
]
