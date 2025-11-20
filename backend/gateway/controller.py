"""
Gateway Controller

Per CompleteWork.md Phase 7:
"backend/gateway/controller.py
 - GatewayController that orchestrates:
     • world engine
     • autonomy engine
     • cognition service
     • renderer
 - MUST NOT add new logic
 - MUST obey cognition_flow and mapping rules"

This controller orchestrates the full pipeline without adding business logic.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging

from backend.world.engine import WorldEngine
from backend.autonomy.engine import AutonomyEngine
from backend.cognition.service import CognitionService
from backend.renderer.service import RenderEngine
from backend.gateway.models import (
    UserActionRequest, UserActionResponse,
    WorldAdvanceRequest, WorldAdvanceResponse,
    RenderRequest, RenderResponse, StatusResponse
)
from backend.persistence.repo import WorldRepo, AgentRepo, UserRepo
from backend.persistence.models import AgentModel, EventModel

logger = logging.getLogger(__name__)


class GatewayController:
    """
    Gateway controller that orchestrates all subsystems.
    
    Per CompleteWork.md Phase 7:
    - Orchestrates: world engine, autonomy engine, cognition service, renderer
    - MUST NOT add new logic
    - MUST obey cognition_flow and mapping rules
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize GatewayController.
        
        Args:
            session: Database session
        """
        self.session = session
        self.world_engine = WorldEngine(session)
        self.autonomy_engine = AutonomyEngine()
        self.cognition_service = CognitionService()
        self.render_engine = RenderEngine(session)
        self.world_repo = WorldRepo(session)
        self.agent_repo = AgentRepo(session)
        self.user_repo = UserRepo(session)
    
    async def handle_user_action(
        self,
        request: UserActionRequest
    ) -> UserActionResponse:
        """
        Handle POST /user/action.
        
        Process:
        1. Parse user's physical action
        2. Update world state (deterministic)
        3. MAY trigger cognition (if defined by the pipeline)
        
        Per CompleteWork.md Phase 7:
        "POST /user/action
         • parse user's physical action
         • update world state (deterministic)
         • MAY trigger cognition (if defined by the pipeline)"
        """
        try:
            # Get or create world
            world = await self.world_engine.get_or_create_world()
            
            # TODO: Parse user action into world event
            # For now, create a placeholder event
            event_data = {
                "world_id": world.id,
                "event_type": request.action_type,
                "payload": {
                    "user_id": request.user_id,
                    "action_type": request.action_type,
                    "target_id": request.target_id,
                    "text": request.text,
                    "destination_location_id": request.destination_location_id
                }
            }
            
            event = await self.world_repo.add_event(event_data)
            
            # Update autonomy for affected agents
            # TODO: Determine which agents are affected
            # For now, skip autonomy update
            
            # Check if cognition should be triggered
            # Per cognition_flow.md: only trigger when meaningful
            # TODO: Implement meaningfulness check
            
            await self.session.commit()
            
            return UserActionResponse(
                success=True,
                world_tick=world.current_tick,
                world_time=world.current_time.isoformat(),
                message=f"Action '{request.action_type}' processed"
            )
            
        except Exception as e:
            logger.error(f"Error in handle_user_action: {str(e)}", exc_info=True)
            await self.session.rollback()
            raise
    
    async def handle_world_advance(
        self,
        request: WorldAdvanceRequest
    ) -> WorldAdvanceResponse:
        """
        Handle POST /world/advance.
        
        Process:
        1. Tick world N times
        2. Return nothing but status OK
        
        Per CompleteWork.md Phase 7:
        "POST /world/advance
         • tick world N times
         • return nothing but status OK"
        """
        try:
            world = await self.world_engine.get_or_create_world()
            events_generated = 0
            
            # Advance world by N ticks
            for _ in range(request.ticks):
                # Tick world
                world = await self.world_engine.tick()
                
                # Update autonomy for all agents
                agents = await self.agent_repo.list_agents_in_location(
                    location_id=None  # Get all agents
                )
                # TODO: Actually get all agents, not just in a location
                # For now, this is a placeholder
                
                # TODO: Trigger cognition where eligible
                # Per cognition_flow.md: only when meaningful
                
                events_generated += 1
            
            await self.session.commit()
            
            return WorldAdvanceResponse(
                ticks_advanced=request.ticks,
                world_tick=world.current_tick,
                world_time=world.current_time.isoformat(),
                events_generated=events_generated
            )
            
        except Exception as e:
            logger.error(f"Error in handle_world_advance: {str(e)}", exc_info=True)
            await self.session.rollback()
            raise
    
    async def handle_render(
        self,
        request: RenderRequest
    ) -> RenderResponse:
        """
        Handle GET /render.
        
        Process:
        1. Call renderer with perceiver_id=user
        2. Return renderer output
        
        Per CompleteWork.md Phase 7:
        "GET /render
         • call renderer with perceiver_id=user
         • return renderer output"
        """
        try:
            # Call renderer
            narrative = await self.render_engine.render_world_state(
                perceiver_id=request.user_id,
                perceiver_type="user"
            )
            
            # Get world state for response
            world = await self.world_engine.get_or_create_world()
            
            # Get user location
            user = await self.user_repo.get_user_by_name(f"user_{request.user_id}")
            location_id = user.location_id if user and hasattr(user, 'location_id') else 1
            
            # Get visible agents
            visible_agents = await self.agent_repo.list_agents_in_location(location_id)
            
            return RenderResponse(
                narrative=narrative,
                visible_agents=[
                    {"id": agent.id, "name": agent.name}
                    for agent in visible_agents
                ],
                visible_objects=[],  # TODO: Get visible objects
                current_location_id=location_id,
                world_tick=world.current_tick
            )
            
        except Exception as e:
            logger.error(f"Error in handle_render: {str(e)}", exc_info=True)
            raise
    
    async def handle_status(self) -> StatusResponse:
        """
        Handle GET /status.
        
        Return current system status.
        """
        try:
            world = await self.world_engine.get_or_create_world()
            
            # Get accurate counts
            from sqlalchemy import select, func
            from backend.persistence.models import AgentModel, LocationModel
            
            # Count agents
            stmt = select(func.count(AgentModel.id))
            result = await self.session.execute(stmt)
            total_agents = result.scalar() or 0
            
            # Count locations
            stmt = select(func.count(LocationModel.id))
            result = await self.session.execute(stmt)
            total_locations = result.scalar() or 0
            
            return StatusResponse(
                status="ok",
                world_tick=world.current_tick,
                world_time=world.current_time.isoformat(),
                total_agents=total_agents,
                total_locations=total_locations
            )
            
        except Exception as e:
            logger.error(f"Error in handle_status: {str(e)}", exc_info=True)
            raise

