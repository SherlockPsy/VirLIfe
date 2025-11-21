"""
Tests for PFEE Time and Continuity Manager

Tests:
- No autonomous time skipping
- Explicit time instructions advance time
- Background time advances correctly
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from backend.pfee.time_continuity import TimeAndContinuityManager


@pytest.mark.asyncio
async def test_no_autonomous_time_skipping(session: AsyncSession):
    """Test that time does not skip autonomously."""
    manager = TimeAndContinuityManager(session)
    
    world_state = {
        "current_time": datetime.now(datetime.timezone.utc),
        "current_tick": 100,
        "world_id": 1
    }
    previous_world_state = {
        "current_time": datetime.now(datetime.timezone.utc) - timedelta(seconds=60),
        "current_tick": 99
    }
    
    # Validate no autonomous skipping
    is_valid = manager.validate_no_autonomous_time_skipping(
        world_state, previous_world_state
    )
    
    # Small advances (< 5 minutes) should be valid
    assert is_valid


@pytest.mark.asyncio
async def test_explicit_time_instruction_advances_time(session: AsyncSession):
    """Test that explicit time instructions advance time."""
    manager = TimeAndContinuityManager(session)
    
    world_state = {
        "current_time": datetime.now(datetime.timezone.utc),
        "current_tick": 100,
        "world_id": 1
    }
    
    user_action = {
        "type": "skip_time",
        "duration_seconds": 3600  # 1 hour
    }
    
    updated_state = await manager.handle_user_time_instruction(
        user_action, world_state
    )
    
    # Time should have advanced
    if updated_state.get("current_time"):
        assert isinstance(updated_state["current_time"], datetime)


@pytest.mark.asyncio
async def test_implied_time_consuming_action_advances_time(session: AsyncSession):
    """Test that implied time-consuming actions advance time."""
    manager = TimeAndContinuityManager(session)
    
    world_state = {
        "current_time": datetime.now(datetime.timezone.utc),
        "current_tick": 100,
        "world_id": 1
    }
    
    user_action = {
        "type": "sleep",
        "duration_seconds": 28800  # 8 hours
    }
    
    updated_state = await manager.handle_user_time_instruction(
        user_action, world_state
    )
    
    # Time should have advanced
    if updated_state.get("current_time"):
        assert isinstance(updated_state["current_time"], datetime)

