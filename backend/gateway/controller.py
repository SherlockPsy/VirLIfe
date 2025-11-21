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
from typing import Optional, Callable
import logging
from datetime import datetime, timezone

from backend.world.engine import WorldEngine
from backend.autonomy.engine import AutonomyEngine
from backend.pfee.orchestrator import PerceptionOrchestrator
from backend.pfee.world_state_builder import build_world_state_for_pfee
from backend.gateway.models import (
    UserActionRequest, UserActionResponse,
    WorldAdvanceRequest, WorldAdvanceResponse,
    RenderRequest, RenderResponse, StatusResponse
)
from backend.persistence.repo import WorldRepo, AgentRepo, UserRepo
from backend.persistence.models import AgentModel, EventModel, UserModel

logger = logging.getLogger(__name__)


class GatewayController:
    """
    Gateway controller that orchestrates all subsystems.
    
    Per CompleteWork.md Phase 7:
    - Orchestrates: world engine, autonomy engine, cognition service, renderer
    - MUST NOT add new logic
    - MUST obey cognition_flow and mapping rules
    """
    
    def __init__(self, session: AsyncSession, websocket_broadcast: Optional[Callable[[dict], None]] = None):
        """
        Initialize GatewayController.
        
        Args:
            session: Database session
            websocket_broadcast: Optional function to broadcast messages over WebSocket
        """
        self.session = session
        self.world_engine = WorldEngine(session)
        self.autonomy_engine = AutonomyEngine()
        self.pfee_orchestrator = PerceptionOrchestrator(session)
        self.world_repo = WorldRepo(session)
        self.agent_repo = AgentRepo(session)
        self.user_repo = UserRepo(session)
        self.websocket_broadcast = websocket_broadcast
    
    async def handle_user_action(
        self,
        request: UserActionRequest
    ) -> UserActionResponse:
        """
        Handle POST /user/action.
        
        Process:
        1. Parse user's physical action
        2. Update world state (deterministic)
        3. Trigger cognition for relevant agents
        4. Render new perception
        5. Broadcast over WebSocket
        
        Per CompleteWork.md Phase 7:
        "POST /user/action
         • parse user's physical action
         • update world state (deterministic)
         • MAY trigger cognition (if defined by the pipeline)"
        """
        try:
            logger.info(f"Processing user action: user_id={request.user_id}, action_type={request.action_type}, text={request.text}")
            
            # Get or create world
            world = await self.world_engine.get_or_create_world()
            
            # Get user location to find affected agents
            # Note: UserModel doesn't have location_id, so we default to location 1
            user = await self.user_repo.get_user_by_name(f"user_{request.user_id}")
            if not user:
                # Create user if doesn't exist
                user = UserModel(
                    name=f"user_{request.user_id}"
                )
                self.session.add(user)
                await self.session.flush()
                logger.info(f"Created new user: user_{request.user_id}")
            
            # Default to location 1 (UserModel doesn't track location)
            location_id = 1
            
            # Create world event from user action
            event_description = request.text if request.text else f"User performs {request.action_type}"
            event_data = {
                "world_id": world.id,
                "type": request.action_type,
                "description": event_description,
                "payload": {
                    "user_id": request.user_id,
                    "action_type": request.action_type,
                    "target_id": request.target_id,
                    "text": request.text,
                    "destination_location_id": request.destination_location_id
                },
                "tick": world.current_tick,
                "timestamp": datetime.now(timezone.utc),
                "processed": False
            }
            
            event = await self.world_repo.add_event(event_data)
            logger.info(f"Created event: id={event.id}, type={event.type}")
            
            # Build world state for PFEE
            world_state = await build_world_state_for_pfee(
                self.session, world, request.user_id
            )
            
            # Build user action dict for PFEE
            user_action = {
                "type": request.action_type,
                "text": request.text,
                "target_id": request.target_id,
                "destination_location_id": request.destination_location_id,
                "user_id": request.user_id
            }
            
            # Run PFEE perception cycle
            # This handles: trigger evaluation, cognition, renderer, consequence integration
            logger.info(f"[PFEE] Running perception cycle for user action")
            try:
                perception_result = await self.pfee_orchestrator.run_perception_cycle(
                    world_state=world_state,
                    optional_user_action=user_action
                )
                
                # Get narrative from perception result
                narrative = perception_result.text
                
                # If no narrative, generate fallback
                if not narrative or narrative in ["The world is empty.", "You are nowhere.", "You are in an unknown place."]:
                    logger.info(f"[PFEE] No narrative from orchestrator, generating fallback")
                    visible_agents = await self.agent_repo.list_agents_in_location(location_id)
                    
                    if visible_agents:
                        agent_names = [a.name for a in visible_agents]
                        narrative = f"After your action, the scene remains quiet. {', '.join(agent_names)} are here with you."
                    else:
                        if request.action_type == "speak" and request.text:
                            narrative = f"Your words echo in the quiet space: '{request.text}'. The world around you remains still, waiting."
                        else:
                            narrative = f"After your {request.action_type}, the world around you remains still and quiet."
                
                logger.info(f"[PFEE] Perception cycle complete, narrative length: {len(narrative) if narrative else 0}")
                
            except Exception as e:
                logger.error(f"[PFEE] Error in perception cycle: {str(e)}", exc_info=True)
                # Fallback to simple narrative
                narrative = f"After your {request.action_type}, the world responds."
            
            # Commit all changes (PFEE orchestrator handles state updates)
            await self.session.commit()
            
            # Broadcast renderer output over WebSocket
            if self.websocket_broadcast and narrative:
                try:
                    ws_message = {
                        "type": "perception",
                        "content": narrative,
                        "timestamp": int(datetime.now(timezone.utc).timestamp() * 1000),
                        "speaker": None,
                        "speakerId": None,
                        "metadata": {
                            "location": f"location_{location_id}",
                            "isIncursion": False
                        }
                    }
                    await self.websocket_broadcast(ws_message)
                    logger.info(f"[PFEE] Broadcast WebSocket message: {narrative[:50]}...")
                except Exception as e:
                    logger.error(f"[PFEE] Error broadcasting WebSocket: {str(e)}", exc_info=True)
            
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
            logger.info(f"Rendering for user_id={request.user_id}, pov={request.pov}")
            
            # Get or create user
            # Note: UserModel doesn't have location_id, so we default to location 1
            user = await self.user_repo.get_user_by_name(f"user_{request.user_id}")
            if not user:
                # Create user if doesn't exist
                user = UserModel(
                    name=f"user_{request.user_id}"
                )
                self.session.add(user)
                await self.session.flush()
                logger.info(f"Created new user: user_{request.user_id}")
            
            # Default to location 1 (UserModel doesn't track location)
            location_id = 1
            
            # Build world state for PFEE
            world = await self.world_engine.get_or_create_world()
            world_state = await build_world_state_for_pfee(
                self.session, world, request.user_id
            )
            
            # Run PFEE perception cycle (no user action, just render current state)
            logger.info(f"[PFEE] Running perception cycle for render request")
            try:
                perception_result = await self.pfee_orchestrator.run_perception_cycle(
                    world_state=world_state,
                    optional_user_action=None
                )
                
                narrative = perception_result.text
                
                # Fallback if no narrative
                if not narrative or narrative in ["The world is empty.", "You are nowhere.", "You are in an unknown place."]:
                    visible_agents = await self.agent_repo.list_agents_in_location(location_id)
                    if visible_agents:
                        agent_names = [a.name for a in visible_agents]
                        narrative = f"You are in a quiet place. {', '.join(agent_names)} are here."
                    else:
                        narrative = "You find yourself in a quiet place. The world around you is still."
                
                logger.info(f"[PFEE] Render complete, narrative length: {len(narrative) if narrative else 0}")
                
            except Exception as e:
                logger.error(f"[PFEE] Error in render perception cycle: {str(e)}", exc_info=True)
                # Fallback
                narrative = "You find yourself in a quiet place. The world around you is still."
            
            # Get world state for response
            world = await self.world_engine.get_or_create_world()
            
            # Get visible agents
            visible_agents = await self.agent_repo.list_agents_in_location(location_id)
            
            logger.info(f"Render response: location_id={location_id}, visible_agents={len(visible_agents)}")
            
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
            from backend.persistence.models import LocationModel
            
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

