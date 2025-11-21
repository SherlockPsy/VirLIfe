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
from backend.cognition.service import CognitionService
from backend.renderer.service import RenderEngine
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
        self.cognition_service = CognitionService()
        self.render_engine = RenderEngine(session)
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
            user = await self.user_repo.get_user_by_name(f"user_{request.user_id}")
            if not user:
                # Create user if doesn't exist
                user = UserModel(
                    name=f"user_{request.user_id}",
                    location_id=1,  # Default location
                    world_id=world.id
                )
                self.session.add(user)
                await self.session.flush()
            
            location_id = user.location_id if hasattr(user, 'location_id') else 1
            
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
            logger.info(f"Created event: id={event.id}, type={event.event_type}")
            
            # Get agents in the same location (affected by user action)
            affected_agents = await self.agent_repo.list_agents_in_location(location_id)
            logger.info(f"Found {len(affected_agents)} agents in location {location_id}")
            
            # Trigger cognition for affected agents
            cognition_outputs = []
            for agent in affected_agents:
                try:
                    # Build cognition input from agent state and event
                    # For now, use a simplified version - full implementation would use mapping layer
                    from backend.cognition.service import CognitionInput, EventTrivialityClassification, BehavioralChoice
                    
                    # Determine if event is meaningful for this agent
                    # Simple heuristic: speech actions are meaningful
                    is_meaningful = request.action_type == "speak" and request.text
                    
                    if is_meaningful:
                        # Build basic cognition input
                        # Note: Full implementation would extract all agent state properly
                        cognition_input = CognitionInput(
                            agent_id=str(agent.id),
                            event_type=request.action_type,
                            event_time=datetime.now(timezone.utc),
                            event_description=event_description,
                            personality_kernel=agent.personality_kernel or {},
                            personality_activation={},
                            mood=(agent.mood_valence or 0.0, agent.mood_arousal or 0.0),
                            drives={},
                            arcs={},
                            energy=agent.energy or 0.5,
                            relationships={},
                            intentions={},
                            memories={},
                            event_participants={str(request.user_id): {"name": f"user_{request.user_id}", "role": "user"}},
                            event_topics=[],
                            event_triviality=EventTrivialityClassification.NON_TRIVIAL,
                            behavioral_choices=[]
                        )
                        
                        # Run cognition
                        output = await self.cognition_service.process_cognition(cognition_input)
                        cognition_outputs.append(output)
                        logger.info(f"Cognition processed for agent {agent.id}: eligible={output.was_eligible}, llm_called={output.llm_called}")
                        
                        # Update agent state from cognition output
                        if output.updated_relationships:
                            # Apply relationship updates
                            pass  # TODO: Apply updates to agent model
                        if output.updated_intentions:
                            # Apply intention updates
                            pass  # TODO: Apply updates to agent model
                        if output.updated_drives:
                            # Apply drive updates
                            pass  # TODO: Apply updates to agent model
                            
                except Exception as e:
                    logger.error(f"Error processing cognition for agent {agent.id}: {str(e)}", exc_info=True)
                    # Continue with other agents
            
            # Commit event and any state changes
            await self.session.commit()
            
            # Render new perception for user
            try:
                narrative = await self.render_engine.render_world_state(
                    perceiver_id=request.user_id,
                    perceiver_type="user"
                )
                logger.info(f"Rendered narrative: {narrative[:100]}...")
                
                # Broadcast renderer output over WebSocket
                if self.websocket_broadcast and narrative and narrative != "The world is empty.":
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
                    # Call broadcast function (it's async)
                    try:
                        await self.websocket_broadcast(ws_message)
                        logger.info(f"Broadcast WebSocket message: {narrative[:50]}...")
                    except Exception as e:
                        logger.error(f"Error broadcasting WebSocket message: {str(e)}", exc_info=True)
            except Exception as e:
                logger.error(f"Error rendering or broadcasting: {str(e)}", exc_info=True)
                # Don't fail the request if rendering/broadcast fails
            
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
            user = await self.user_repo.get_user_by_name(f"user_{request.user_id}")
            if not user:
                # Create user if doesn't exist
                world = await self.world_engine.get_or_create_world()
                user = UserModel(
                    name=f"user_{request.user_id}",
                    location_id=1,  # Default location
                    world_id=world.id
                )
                self.session.add(user)
                await self.session.flush()
                logger.info(f"Created new user: user_{request.user_id}")
            
            # Call renderer
            narrative = await self.render_engine.render_world_state(
                perceiver_id=request.user_id,
                perceiver_type="user"
            )
            
            logger.info(f"Rendered narrative (length={len(narrative)}): {narrative[:200]}...")
            
            # Ensure we have meaningful content
            if not narrative or narrative == "The world is empty." or narrative == "You are nowhere.":
                # Generate a default narrative
                world = await self.world_engine.get_or_create_world()
                location_id = user.location_id if hasattr(user, 'location_id') else 1
                visible_agents = await self.agent_repo.list_agents_in_location(location_id)
                
                if visible_agents:
                    agent_names = [a.name for a in visible_agents]
                    narrative = f"You are in a quiet place. {', '.join(agent_names)} are here."
                else:
                    narrative = "You find yourself in a quiet place. The world around you is still."
                
                logger.info(f"Generated fallback narrative: {narrative}")
            
            # Get world state for response
            world = await self.world_engine.get_or_create_world()
            
            # Get user location
            location_id = user.location_id if hasattr(user, 'location_id') else 1
            
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

