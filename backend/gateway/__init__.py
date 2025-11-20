"""
Gateway API module — HTTP interface for VirLIfe backend.

Provides REST endpoints for:
- User actions
- World advancement
- Perceptual rendering
- System status

Part of Phase 7: Gateway API.
"""

from backend.gateway.models import (
    UserActionRequest,
    UserActionResponse,
    WorldAdvanceRequest,
    WorldAdvanceResponse,
    RenderRequest,
    RenderResponse,
    StatusResponse,
)
from backend.gateway.handlers import GatewayAPI

__all__ = [
    "GatewayAPI",
    "UserActionRequest",
    "UserActionResponse",
    "WorldAdvanceRequest",
    "WorldAdvanceResponse",
    "RenderRequest",
    "RenderResponse",
    "StatusResponse",
]
