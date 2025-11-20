"""
Gateway API Routes

Per CompleteWork.md Phase 7:
"backend/gateway/routes.py
 Endpoints:
   - POST /user/action
   - POST /world/advance
   - GET /render"

This module defines the FastAPI route handlers for the Gateway API.
Routes are registered in backend/main.py.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.persistence.database import AsyncSessionLocal
from backend.gateway.controller import GatewayController
from backend.gateway.models import (
    UserActionRequest, UserActionResponse,
    WorldAdvanceRequest, WorldAdvanceResponse,
    RenderRequest, RenderResponse, StatusResponse
)

router = APIRouter(prefix="/api/v1", tags=["gateway"])


async def get_db():
    """Get database session for dependency injection."""
    async with AsyncSessionLocal() as session:
        yield session


async def get_controller(db: AsyncSession = Depends(get_db)) -> GatewayController:
    """Get GatewayController instance."""
    return GatewayController(db)


@router.post("/user/action", response_model=UserActionResponse)
async def user_action(
    request: UserActionRequest,
    controller: GatewayController = Depends(get_controller)
):
    """
    User performs an action in the world.
    
    Per CompleteWork.md Phase 7:
    - POST /user/action
      • parse user's physical action
      • update world state (deterministic)
      • MAY trigger cognition (if defined by the pipeline)
    """
    try:
        return await controller.handle_user_action(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/world/advance", response_model=WorldAdvanceResponse)
async def world_advance(
    request: WorldAdvanceRequest,
    controller: GatewayController = Depends(get_controller)
):
    """
    Advance world time by N ticks.
    
    Per CompleteWork.md Phase 7:
    - POST /world/advance
      • tick world N times
      • return nothing but status OK
    """
    try:
        return await controller.handle_world_advance(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/render", response_model=RenderResponse)
async def render(
    user_id: int,
    pov: str = "second_person",
    controller: GatewayController = Depends(get_controller)
):
    """
    Render perceptual experience for user.
    
    Per CompleteWork.md Phase 7:
    - GET /render
      • call renderer with perceiver_id=user
      • return renderer output
    """
    try:
        request = RenderRequest(user_id=user_id, pov=pov)
        return await controller.handle_render(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=StatusResponse)
async def status(
    controller: GatewayController = Depends(get_controller)
):
    """
    Get system status.
    """
    try:
        return await controller.handle_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

