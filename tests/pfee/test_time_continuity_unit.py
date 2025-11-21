from datetime import datetime, timedelta, timezone

import pytest

from backend.pfee.time_continuity import TimeAndContinuityManager
from tests.pfee import factories


@pytest.mark.asyncio
async def test_small_background_time_advance_allowed(session):
    world = await factories.create_world(
        session, current_time=datetime(2025, 5, 1, 9, tzinfo=timezone.utc)
    )
    manager = TimeAndContinuityManager(session)
    world_state = {"world_id": world.id, "current_time": world.current_time}

    updated = await manager.advance_background_time(
        world_state, delta=timedelta(minutes=2)
    )

    assert updated["current_time"] == world.current_time
    assert world.current_time.hour == 9
    assert world.current_time.minute == 2


@pytest.mark.asyncio
async def test_large_autonomous_jump_without_instruction_rejected(session):
    manager = TimeAndContinuityManager(session)
    previous = {"current_time": datetime(2025, 5, 1, 9, tzinfo=timezone.utc)}
    current = {
        "current_time": datetime(2025, 5, 1, 9, 20, tzinfo=timezone.utc)
    }

    is_valid = manager.validate_no_autonomous_time_skipping(current, previous)

    assert is_valid is False


@pytest.mark.asyncio
async def test_instruction_driven_time_jump_is_applied(session):
    world = await factories.create_world(
        session, current_time=datetime(2025, 5, 1, 10, tzinfo=timezone.utc)
    )
    manager = TimeAndContinuityManager(session)
    world_state = {"world_id": world.id, "current_time": world.current_time}
    user_action = {"type": "sleep", "duration_seconds": 8 * 3600}

    updated = await manager.handle_user_time_instruction(user_action, world_state)

    assert updated["current_time"].hour == 18
    assert world.current_time.hour == 18

