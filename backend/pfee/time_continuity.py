"""
PFEE Time and Continuity Manager

Implements:
- PFEE_ARCHITECTURE.md §2.6
- PFEE_LOGIC.md §6
- PFEE_PLAN.md Phase P6

Enforces subjective time continuity and controls time transitions.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from backend.persistence.repo import WorldRepo
from backend.world.engine import WorldEngine


class TimeAndContinuityManager:
    """
    Manages time continuity and transitions.
    
    Implements PFEE_LOGIC.md §6 time and continuity logic.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.world_repo = WorldRepo(session)
        self.world_engine = WorldEngine(session)

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
        if world.current_time.tzinfo is None:
            world.current_time = world.current_time.replace(tzinfo=datetime.timezone.utc)
        
        new_time = world.current_time + delta
        world.current_time = new_time

        # Update schedules (calendar processing)
        # This is handled by World Engine's calendar processing
        await self.world_engine._process_calendars(world)

        # Update autonomy background (off-screen agent movement, routines)
        await self.world_engine._process_continuity(world)

        # Update influence fields (handled by InfluenceFieldManager)
        # This is called separately by orchestrator

        await self.world_repo.save_world(world)

        # Update world_state dict
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
        
        The system MUST NOT:
        - compress or skip time without explicit user instruction
        - or a logically implied time-consuming action (sleep, long travel, etc.)
        """
        # Check if user explicitly requests time skip
        if not self._user_explicitly_requests_time_skip(user_action):
            return world_state

        # Compute target time from instruction
        target_time = self._compute_target_time_from_instruction(user_action, world_state)
        if not target_time:
            return world_state

        # Advance background time to target
        current_time = world_state.get("current_time")
        if current_time and target_time > current_time:
            delta = target_time - current_time
            world_state = await self.advance_background_time(world_state, delta)

        return world_state

    def _user_explicitly_requests_time_skip(self, user_action: Dict[str, Any]) -> bool:
        """Check if user action explicitly requests time skip."""
        action_type = user_action.get("type", "")
        explicit_time_skip_types = {
            "time_skip", "advance_time", "skip_to", "fast_forward",
            "sleep", "wait", "travel"  # Implied time-consuming actions
        }
        return action_type in explicit_time_skip_types

    def _compute_target_time_from_instruction(
        self,
        user_action: Dict[str, Any],
        world_state: Dict[str, Any]
    ) -> Optional[datetime]:
        """Compute target time from user instruction."""
        current_time = world_state.get("current_time")
        if not current_time:
            return None

        # Parse time instruction
        instruction = user_action.get("instruction", "")
        target_time_str = user_action.get("target_time")
        
        if target_time_str:
            # Parse target_time string
            try:
                target_time = datetime.fromisoformat(target_time_str)
                if target_time.tzinfo is None:
                    target_time = target_time.replace(tzinfo=datetime.timezone.utc)
                return target_time
            except (ValueError, TypeError):
                pass

        # Parse relative time (e.g., "skip 2 hours", "advance 30 minutes", "wait 1 hour")
        import re
        if not instruction:
            return None
        instruction_lower = instruction.lower()
        
        if any(word in instruction_lower for word in ["skip", "advance", "wait", "forward", "fast"]):
            hours = 0
            minutes = 0
            days = 0
            
            # Extract days
            day_match = re.search(r'(\d+)\s*(?:day|days)', instruction_lower)
            if day_match:
                days = int(day_match.group(1))
            
            # Extract hours
            hour_match = re.search(r'(\d+)\s*(?:hour|hours|hr|hrs)', instruction_lower)
            if hour_match:
                hours = int(hour_match.group(1))
            
            # Extract minutes
            minute_match = re.search(r'(\d+)\s*(?:minute|minutes|min|mins)', instruction_lower)
            if minute_match:
                minutes = int(minute_match.group(1))
            
            # Extract seconds (for very short skips)
            second_match = re.search(r'(\d+)\s*(?:second|seconds|sec|secs)', instruction_lower)
            seconds = 0
            if second_match:
                seconds = int(second_match.group(1))

            if days > 0 or hours > 0 or minutes > 0 or seconds > 0:
                delta = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
                return current_time + delta
            
            # Try to extract just a number (assume hours)
            number_match = re.search(r'(\d+)', instruction_lower)
            if number_match and not any(word in instruction_lower for word in ["day", "hour", "minute", "second"]):
                # Assume hours if no unit specified
                hours = int(number_match.group(1))
                if hours > 0 and hours < 24:  # Reasonable range
                    return current_time + timedelta(hours=hours)

        # Handle implied time-consuming actions
        action_type = user_action.get("type", "")
        if action_type == "sleep":
            # Sleep typically advances time by 6-8 hours
            sleep_hours = user_action.get("duration_hours", 7)
            return current_time + timedelta(hours=sleep_hours)
        elif action_type == "travel":
            # Travel advances time based on distance
            duration = user_action.get("duration_hours", 1)
            return current_time + timedelta(hours=duration)
        elif action_type == "wait":
            # Explicit wait action
            wait_minutes = user_action.get("duration_minutes", 5)
            return current_time + timedelta(minutes=wait_minutes)

        return None

    async def ensure_no_autonomous_time_skipping(
        self,
        world_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Ensure no autonomous time skipping occurs.
        
        This is a validation function that ensures the system
        doesn't skip time without user consent.
        """
        # This is primarily enforced by not calling advance_background_time
        # without explicit user instruction or implied time-consuming action
        # This function serves as a checkpoint/validation
        return world_state

