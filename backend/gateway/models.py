"""
Gateway API models — request/response schemas for VirLIfe Gateway API.

These are used by the main FastAPI app to handle user actions,
world advancement, and rendering.
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class UserActionRequest(BaseModel):
    """User performs an action in the world."""
    user_id: int
    action_type: str  # "speak", "move", "interact", etc.
    target_id: Optional[int] = None  # agent or object ID
    text: Optional[str] = None  # for speech actions
    destination_location_id: Optional[int] = None  # for movement


class UserActionResponse(BaseModel):
    """Response after user action."""
    success: bool
    world_tick: int
    world_time: str
    message: str


class WorldAdvanceRequest(BaseModel):
    """Advance world time by N ticks."""
    ticks: int = 1


class WorldAdvanceResponse(BaseModel):
    """Response after world advance."""
    ticks_advanced: int
    world_tick: int
    world_time: str
    events_generated: int


class RenderRequest(BaseModel):
    """Request rendering of the world for the user."""
    user_id: int
    pov: str = "second_person"  # "second_person" or "omniscient" (for testing)


class VisibleAgentInfo(BaseModel):
    """Information about a visible agent."""
    id: int
    name: str


class VisibleObjectInfo(BaseModel):
    """Information about a visible object."""
    id: int
    name: str


class RenderResponse(BaseModel):
    """Rendered perception of the world."""
    narrative: str
    visible_agents: List[VisibleAgentInfo]
    visible_objects: List[VisibleObjectInfo]
    current_location_id: int
    world_tick: int


class StatusResponse(BaseModel):
    """System status response."""
    status: str
    world_tick: int
    world_time: str
    total_agents: int
    total_locations: int
