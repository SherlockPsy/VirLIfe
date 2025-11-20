"""
Gateway API endpoints — HTTP interface for the VirLIfe backend.

Exposes three main endpoints:
- POST /user/action — user performs an action
- POST /world/advance — advance world state
- GET /render — render perceptual experience for user

This module integrates:
- World Engine (physical state)
- Autonomy Engine (numeric psychology)
- Cognition Service (semantic reflection)
- Renderer Service (perceptual narrative)

No UI logic here. No session history. No state beyond world state.
"""

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.gateway.models import (
    UserActionRequest, UserActionResponse,
    WorldAdvanceRequest, WorldAdvanceResponse,
    RenderRequest, RenderResponse, StatusResponse
)
from backend.world.engine import WorldEngine
from backend.autonomy.engine import AutonomyEngine
from backend.cognition.service import CognitionService
from backend.renderer.perception import PerceptionPacketBuilder
from backend.renderer.llm_wrapper import LLMRendererWrapper
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# GATEWAY API HANDLERS
# ============================================================================

class GatewayAPI:
    """Gateway API handler for all endpoints."""

    def __init__(self):
        pass

    async def user_action(
        self,
        request: UserActionRequest,
        db: AsyncSession,
    ) -> UserActionResponse:
        """
        Handle POST /user/action.

        Process:
        1. Validate user and world state
        2. Create world event from user action
        3. Update autonomy for affected agents
        4. Trigger cognition if conditions met
        5. Persist state
        6. Return world state
        """
        try:
            world_engine = WorldEngine(db)

            # Get or create world
            world = await world_engine.get_or_create_world()

            # TODO: Validate user exists
            # For now, just verify we have a world

            # TODO: Process user action into world event
            # This would:
            # - Create EventModel
            # - Update affected agent states
            # - Trigger cognition

            # For now, just advance tick as placeholder
            world = await world_engine.tick()

            await db.commit()

            return UserActionResponse(
                success=True,
                world_tick=world.current_tick,
                world_time=world.current_time.isoformat(),
                message=f"Action '{request.action_type}' processed",
            )

        except Exception as e:
            logger.error(f"Error in user_action: {str(e)}")
            await db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

    async def world_advance(
        self,
        request: WorldAdvanceRequest,
        db: AsyncSession,
    ) -> WorldAdvanceResponse:
        """
        Handle POST /world/advance.

        Process:
        1. Advance world clock by N ticks
        2. Generate calendar and incursion events
        3. Update autonomy for all agents
        4. Trigger cognition where eligible
        5. Persist state
        6. Return world state and event count
        """
        try:
            world_engine = WorldEngine(db)
            autonomy_engine = AutonomyEngine()  # No arguments
            # CognitionService is static, no instantiation needed

            world = await world_engine.get_or_create_world()
            events_generated = 0

            # Advance world by N ticks
            for _ in range(request.ticks):
                # Tick world
                world = await world_engine.tick()

                # TODO: Generate events from calendars and incursions
                # For now, just count the tick as an event
                events_generated += 1

                # TODO: Update autonomy for all agents
                # TODO: Trigger cognition

            await db.commit()

            return WorldAdvanceResponse(
                ticks_advanced=request.ticks,
                world_tick=world.current_tick,
                world_time=world.current_time.isoformat(),
                events_generated=events_generated,
            )

        except Exception as e:
            logger.error(f"Error in world_advance: {str(e)}")
            await db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

    async def render(
        self,
        request: RenderRequest,
        db: AsyncSession,
    ) -> RenderResponse:
        """
        Handle GET /render.

        Process:
        1. Get current world state
        2. Build perception packet from user POV
        3. Call Renderer LLM
        4. Return formatted narrative and context
        """
        try:
            world_engine = WorldEngine(db)

            # Get world state
            world = await world_engine.get_or_create_world()

            # TODO: Get user location
            # TODO: Build perception packet
            # TODO: Call renderer LLM

            # Placeholder response
            return RenderResponse(
                narrative="The world awakens around you...",
                visible_agents=[],
                visible_objects=[],
                current_location_id=1,
                world_tick=world.current_tick,
            )

        except Exception as e:
            logger.error(f"Error in render: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    async def status(self, db: AsyncSession) -> StatusResponse:
        """
        Handle GET /status.

        Return current system status.
        """
        try:
            world_engine = WorldEngine(db)
            world = await world_engine.get_or_create_world()

            # TODO: Get accurate counts
            total_agents = 0
            total_locations = 0

            return StatusResponse(
                status="ok",
                world_tick=world.current_tick,
                world_time=world.current_time.isoformat(),
                total_agents=total_agents,
                total_locations=total_locations,
            )

        except Exception as e:
            logger.error(f"Error in status: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
