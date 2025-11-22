"""
F.2 TEST_WORLD_STATE_BUILDER

Purpose: Ensure world_state_builder reads DB correctly and constructs a complete, George-safe world state.
"""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.persistence.models import AgentModel, LocationModel
from backend.pfee.world_state_builder import build_world_state


class TestWorldStateBuilder:
    """F.2: Test world state builder"""
    
    @pytest.mark.asyncio
    async def test_world_state_includes_correct_agents(
        self, test_session: AsyncSession, seeded_world: dict
    ):
        """F.2.1: Verify world_state includes correct agents with proper fields"""
        world_id = seeded_world["world_id"]
        george_id = seeded_world["george_agent_id"]
        rebecca_id = seeded_world["rebecca_agent_id"]
        lucy_id = seeded_world.get("lucy_agent_id")
        
        # Place agents in same location
        stmt = select(LocationModel).where(LocationModel.world_id == world_id)
        result = await test_session.execute(stmt)
        locations = result.scalars().all()
        if locations:
            location_id = locations[0].id
            
            # Update agent locations
            for agent_id in [george_id, rebecca_id]:
                if agent_id:
                    stmt = select(AgentModel).where(AgentModel.id == agent_id)
                    result = await test_session.execute(stmt)
                    agent = result.scalars().first()
                    if agent:
                        agent.location_id = location_id
            await test_session.flush()
        
        world_state = await build_world_state(
            test_session,
            world_id=world_id
        )
        
        agents_in_scene = world_state.get("agents_in_scene", [])
        agent_ids = [a.get("id") for a in agents_in_scene]
        
        assert george_id in agent_ids, "George must be in world_state"
        assert rebecca_id in agent_ids, "Rebecca must be in world_state"
        
        # Check George has no psychological fields
        george_data = next((a for a in agents_in_scene if a.get("id") == george_id), None)
        assert george_data is not None
        assert "drives" not in george_data or not george_data.get("drives")
        assert "mood" not in george_data or not george_data.get("mood")
        
        # Check Rebecca has psychological fields
        rebecca_data = next((a for a in agents_in_scene if a.get("id") == rebecca_id), None)
        assert rebecca_data is not None
        assert rebecca_data.get("drives") or rebecca_data.get("personality_kernel")
    
    @pytest.mark.asyncio
    async def test_world_state_relationships_present(
        self, test_session: AsyncSession, seeded_world: dict
    ):
        """F.2.2: Verify relationships are present in world_state"""
        world_id = seeded_world["world_id"]
        george_id = seeded_world["george_agent_id"]
        
        world_state = await build_world_state(
            test_session,
            world_id=world_id
        )
        
        relationships = world_state.get("relationships", {})
        assert len(relationships) > 0, "Relationships must be present"
        
        # Check for relationships toward George
        george_rels = [k for k in relationships.keys() if str(george_id) in k or "george" in k.lower()]
        assert len(george_rels) > 0, "Relationships toward George must exist"
        
        # Check relationship values are valid
        for rel_key, rel_data in relationships.items():
            if isinstance(rel_data, dict):
                if "warmth" in rel_data:
                    assert 0.0 <= rel_data["warmth"] <= 1.0
                if "trust" in rel_data:
                    assert 0.0 <= rel_data["trust"] <= 1.0
    
    @pytest.mark.asyncio
    async def test_world_state_memories_filtered(
        self, test_session: AsyncSession, seeded_world: dict
    ):
        """F.2.3: Verify memories are filtered correctly"""
        world_id = seeded_world["world_id"]
        rebecca_id = seeded_world["rebecca_agent_id"]
        
        world_state = await build_world_state(
            test_session,
            world_id=world_id
        )
        
        # Find Rebecca in world_state
        agents_in_scene = world_state.get("agents_in_scene", [])
        rebecca_data = next((a for a in agents_in_scene if a.get("id") == rebecca_id), None)
        
        if rebecca_data:
            memories = rebecca_data.get("memories", [])
            # Should have a small number of high-salience memories
            assert len(memories) <= 7, f"Too many memories: {len(memories)}"
            for memory in memories:
                assert memory.get("salience", 0) >= 0.0
    
    @pytest.mark.asyncio
    async def test_george_not_internal_in_world_state(
        self, test_session: AsyncSession, seeded_world: dict
    ):
        """F.2.5: Verify George has no internal fields in world_state"""
        world_id = seeded_world["world_id"]
        george_id = seeded_world["george_agent_id"]
        
        world_state = await build_world_state(
            test_session,
            world_id=world_id
        )
        
        agents_in_scene = world_state.get("agents_in_scene", [])
        george_data = next((a for a in agents_in_scene if a.get("id") == george_id or a.get("is_real_user")), None)
        
        assert george_data is not None
        
        # E.3.1: George should have only external fields
        assert "name" in george_data
        assert "public_profile" in george_data or "location" in george_data
        
        # E.3.1: George should NOT have internal fields
        assert "drives" not in george_data or not george_data.get("drives")
        assert "mood" not in george_data or not george_data.get("mood")
        assert "memories" not in george_data or len(george_data.get("memories", [])) == 0
        assert "arcs" not in george_data or len(george_data.get("arcs", [])) == 0
        assert "influence_fields" not in george_data or not george_data.get("influence_fields")

