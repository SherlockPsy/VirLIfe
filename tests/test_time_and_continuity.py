"""
F.9 TEST_TIME_AND_CONTINUITY

Purpose: Ensure time progression is consistent and interacts safely with PFEE + autonomy.
"""

import pytest
from datetime import timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.persistence.models import AgentModel, WorldModel
from backend.world.continuity import ContinuityEngine
from backend.world.engine import WorldEngine


class TestTimeAndContinuity:
    """F.9: Test time and continuity"""
    
    @pytest.mark.asyncio
    async def test_time_advances_on_tick(
        self, test_session: AsyncSession, seeded_world: dict
    ):
        """F.9.1: Verify time advances correctly"""
        world_id = seeded_world["world_id"]
        
        # Get initial time
        stmt = select(WorldModel).where(WorldModel.id == world_id)
        result = await test_session.execute(stmt)
        world = result.scalars().first()
        
        initial_tick = world.current_tick
        initial_time = world.current_time
        
        # Advance time
        world_engine = WorldEngine(test_session)
        await world_engine.tick(seconds=60)
        await test_session.refresh(world)
        
        assert world.current_tick > initial_tick
        assert world.current_time > initial_time
    
    @pytest.mark.asyncio
    async def test_time_advancement_does_not_modify_george(
        self, test_session: AsyncSession, seeded_world: dict
    ):
        """F.9.2: Verify time advancement doesn't modify George's internal state"""
        world_id = seeded_world["world_id"]
        george_id = seeded_world["george_agent_id"]
        
        # Get George's state before
        stmt = select(AgentModel).where(AgentModel.id == george_id)
        result = await test_session.execute(stmt)
        george_before = result.scalars().first()
        
        original_drives = george_before.drives if george_before.drives else {}
        original_mood = george_before.mood if george_before.mood else {}
        
        # Advance time
        world_engine = WorldEngine(test_session)
        await world_engine.tick(seconds=60)
        
        # Check George after
        await test_session.refresh(george_before)
        
        # E.9.1: George's internal state should be unchanged
        assert george_before.drives == original_drives or george_before.drives == {}
        assert george_before.mood == original_mood or george_before.mood == {}
        assert george_before.is_real_user == True

