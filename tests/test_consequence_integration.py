"""
F.5 TEST_CONSEQUENCE_INTEGRATION

Purpose: Ensure DB updates from cognition_output are applied correctly and safely.
"""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.persistence.models import RelationshipModel, ArcModel, MemoryModel, IntentionModel, AgentModel
from backend.pfee.consequences import ConsequenceIntegrator
from backend.pfee.world_state_builder import build_world_state


class TestConsequenceIntegration:
    """F.5: Test consequence integration"""
    
    @pytest.mark.asyncio
    async def test_george_updates_blocked(
        self, test_session: AsyncSession, seeded_world: dict
    ):
        """F.5.5: Verify George updates are blocked"""
        world_id = seeded_world["world_id"]
        george_id = seeded_world["george_agent_id"]
        
        world_state = await build_world_state(
            test_session,
            world_id=world_id
        )
        world_state["george_agent_id"] = george_id
        
        # Get initial state
        stmt = select(AgentModel).where(AgentModel.id == george_id)
        result = await test_session.execute(stmt)
        george_before = result.scalars().first()
        initial_drives = george_before.drives if george_before.drives else {}
        
        # Create illegal output
        illegal_output = {
            "memories": [{"agent_id": george_id, "content": "Test memory"}],
            "drives": {str(george_id): {"attachment": {"level": 0.8}}}
        }
        
        integrator = ConsequenceIntegrator(test_session)
        await integrator.integrate_consequences(
            world_state=world_state,
            cognition_output=illegal_output
        )
        
        # Check George unchanged
        await test_session.refresh(george_before)
        assert george_before.drives == initial_drives or george_before.drives == {}
        
        # Check no memory created
        stmt = select(MemoryModel).where(MemoryModel.agent_id == george_id)
        result = await test_session.execute(stmt)
        assert len(result.scalars().all()) == 0

