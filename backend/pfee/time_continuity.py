"""
PFEE Time and Continuity Manager

Implements:
- PFEE_ARCHITECTURE.md §2.6
- PFEE_LOGIC.md §6
- PFEE_PLAN.md Phase P6

Enforces subjective time continuity and controls time transitions.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from backend.persistence.repo import WorldRepo
from backend.persistence.models import WorldModel
from backend.pfee.influence_fields import InfluenceFieldManager


class TimeAndContinuityManager:
    """
    Manages time continuity and time transitions.
    
    Implements PFEE_LOGIC.md §6 time continuity logic.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.world_repo = WorldRepo(session)
        self.influence_manager = InfluenceFieldManager(session)
    
    async def advance_background_time(
        self,
        world_state: Dict[str, Any],
        delta: timedelta
    ) -> Dict[str, Any]:
        """
        Advance background time deterministically.
        
        Implements PFEE_LOGIC.md §6.2
        
        Updates:
        - world time
        - schedules
        - autonomy background
        - influence fields
        """
        world_id = world_state.get("world_id", 1)
        world = await self.world_repo.get_world(world_id)
        if not world:
            return world_state
        
        # Advance time
        world.current_time = world.current_time + delta
        world.current_tick += int(delta.total_seconds() / 60)  # Assuming 1 tick per minute
        
        # Update schedules (handled by World Engine)
        # Update autonomy background (handled by Autonomy Engine)
        # Update influence fields
        await self.influence_manager.update_influence_fields_from_background(world_state)
        
        await self.world_repo.save_world(world)
        
        # Update world_state
        world_state["current_time"] = world.current_time
        world_state["current_tick"] = world.current_tick
        
        return world_state
    
    async def handle_user_time_instruction(
        self,
        user_action: Dict[str, Any],
        world_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle explicit user time instruction.
        
        Implements PFEE_LOGIC.md §6.1
        
        Rules:
        - Explicit time skip requests → advance time
        - No autonomous time skipping
        - Only explicit/implicit user-driven time jumps
        """
        if not user_action:
            return world_state
        
        # Check if user explicitly requests time skip
        action_type = user_action.get("type", "")
        if action_type in ["skip_time", "advance_time", "wait"]:
            # Extract target time or duration
            target_time_str = user_action.get("target_time")
            duration_seconds = user_action.get("duration_seconds", 0)
            
            if target_time_str:
                # Parse target time
                try:
                    target_time = datetime.fromisoformat(target_time_str.replace("Z", "+00:00"))
                    current_time = world_state.get("current_time")
                    if isinstance(current_time, datetime):
                        delta = target_time - current_time
                        if delta.total_seconds() > 0:
                            return await self.advance_background_time(world_state, delta)
                except Exception:
                    pass
            
            if duration_seconds > 0:
                delta = timedelta(seconds=duration_seconds)
                return await self.advance_background_time(world_state, delta)
        
        # Check for logically implied time-consuming actions
        if action_type in ["sleep", "travel", "long_activity"]:
            # Implied time jump
            duration_seconds = user_action.get("duration_seconds", 3600)  # Default 1 hour
            delta = timedelta(seconds=duration_seconds)
            return await self.advance_background_time(world_state, delta)
        
        return world_state
    
    def validate_no_autonomous_time_skipping(
        self,
        world_state: Dict[str, Any],
        previous_world_state: Dict[str, Any]
    ) -> bool:
        """
        Validate that no autonomous time skipping occurred.
        
        Returns True if valid, False if illegal skip detected.
        """
        current_time = world_state.get("current_time")
        previous_time = previous_world_state.get("current_time")
        
        if not isinstance(current_time, datetime) or not isinstance(previous_time, datetime):
            return True  # Can't validate
        
        # Time should only advance, not skip large amounts
        time_delta = (current_time - previous_time).total_seconds()
        
        # Allow small advances (up to 5 minutes) without explicit instruction
        MAX_AUTONOMOUS_ADVANCE_SECONDS = 300
        
        if time_delta > MAX_AUTONOMOUS_ADVANCE_SECONDS:
            # Large time jump without explicit instruction - invalid
            return False
        
        return True

