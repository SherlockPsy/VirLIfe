"""
Tests for Time and Continuity Manager

Implements PFEE_PLAN.md Phase P9 test requirements for time continuity.
"""

import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from backend.pfee.time_continuity import TimeAndContinuityManager


@pytest.mark.asyncio
async def test_no_spontaneous_fast_forwarding(session: AsyncSession):
    """Test that no spontaneous fast-forwarding occurs."""
    manager = TimeAndContinuityManager(session)
    
    world_state = {
        "world_id": 1,
        "current_time": datetime.now(timezone.utc),
        "current_tick": 0
    }
    
    # No user action - should not advance time
    result = await manager.handle_user_time_instruction({}, world_state)
    
    assert result["current_time"] == world_state["current_time"]


@pytest.mark.asyncio
async def test_explicit_instructions_cause_time_jumps(session: AsyncSession):
    """Test that explicit instructions cause controlled time jumps."""
    manager = TimeAndContinuityManager(session)
    
    initial_time = datetime.now(timezone.utc)
    world_state = {
        "world_id": 1,
        "current_time": initial_time,
        "current_tick": 0
    }
    
    user_action = {
        "type": "time_skip",
        "instruction": "skip 2 hours",
        "target_time": None
    }
    
    result = await manager.handle_user_time_instruction(user_action, world_state)
    
    # Time should have advanced
    assert result["current_time"] > initial_time


@pytest.mark.asyncio
async def test_background_reality_updates_deterministically(session: AsyncSession):
    """Test that background reality updates deterministically."""
    manager = TimeAndContinuityManager(session)
    
    initial_time = datetime.now(timezone.utc)
    world_state = {
        "world_id": 1,
        "current_time": initial_time,
        "current_tick": 0
    }
    
    # Advance background time
    delta = timedelta(hours=1)
    result = await manager.advance_background_time(world_state, delta)
    
    # Time should have advanced by exactly delta
    expected_time = initial_time + delta
    assert result["current_time"] == expected_time

