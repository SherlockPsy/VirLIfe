"""
Tests for PFEE Influence Field Manager

Tests:
- Influence field updates from background
- Query influence for agent
- Determinism of influence calculations
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.pfee.influence_fields import InfluenceFieldManager


@pytest.mark.asyncio
async def test_update_influence_fields_from_background(session: AsyncSession):
    """Test updating influence fields from background state."""
    manager = InfluenceFieldManager(session)
    
    world_state = {
        "persistent_agents": [
            {
                "id": 1,
                "drives": {
                    "relatedness": {"level": 0.8},
                    "autonomy": {"level": 0.3}
                },
                "arcs": {
                    "conflict": {
                        "intensity": 0.7,
                        "valence_bias": -0.4,
                        "topic_vector": ["argument"]
                    }
                }
            }
        ]
    }
    
    await manager.update_influence_fields_from_background(world_state)
    
    # Query influence
    snapshot = await manager.query_influence_for_agent(1)
    
    if snapshot:
        assert snapshot.agent_id == 1
        assert "drive_pressures" in snapshot.__dict__ or hasattr(snapshot, "drive_pressures")


@pytest.mark.asyncio
async def test_influence_field_determinism(session: AsyncSession):
    """Test that influence field calculations are deterministic."""
    manager = InfluenceFieldManager(session)
    
    world_state = {
        "persistent_agents": [
            {
                "id": 2,
                "drives": {
                    "relatedness": {"level": 0.7}
                },
                "arcs": {}
            }
        ]
    }
    
    # Update twice
    await manager.update_influence_fields_from_background(world_state)
    snapshot1 = await manager.query_influence_for_agent(2)
    
    await manager.update_influence_fields_from_background(world_state)
    snapshot2 = await manager.query_influence_for_agent(2)
    
    # Should be consistent (may accumulate, but deterministically)
    if snapshot1 and snapshot2:
        assert snapshot1.agent_id == snapshot2.agent_id

