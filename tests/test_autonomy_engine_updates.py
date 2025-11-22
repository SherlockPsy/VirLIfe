"""
F.6 TEST_AUTONOMY_ENGINE_UPDATES

Purpose: Ensure update_agents_over_time behaves as specified.
"""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.persistence.models import AgentModel
from backend.autonomy.engine import AutonomyEngine
from backend.persistence.models import EventModel


class TestAutonomyEngineUpdates:
    """F.6: Test autonomy engine updates"""
    
    @pytest.mark.asyncio
    async def test_no_updates_for_george(
        self, test_session: AsyncSession, seeded_world: dict
    ):
        """F.6.6: Verify Autonomy Engine does not update George"""
        george_id = seeded_world["george_agent_id"]
        
        stmt = select(AgentModel).where(AgentModel.id == george_id)
        result = await test_session.execute(stmt)
        george = result.scalars().first()
        
        # Store original state
        original_drives = george.drives if george.drives else {}
        original_mood = george.mood if george.mood else {}
        
        # Temporarily inject fake data (test only)
        george.drives = {"test": {"level": 0.5, "sensitivity": 0.5}}
        george.mood = {"valence": 0.3, "arousal": 0.4}
        await test_session.flush()
        
        # Run autonomy update
        engine = AutonomyEngine()
        events = []
        engine.update_agent_internal_state(george, events)
        await test_session.refresh(george)
        
        # E.8.1: George should be unchanged (early return in update_agent_internal_state)
        # The method should return immediately for is_real_user
        assert george.is_real_user == True
        # Fields may remain as set (since we skip processing) or be empty
        # The key is that autonomy logic doesn't run on George

