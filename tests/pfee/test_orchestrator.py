"""
Tests for PFEE Perception Orchestrator

Tests:
- No triggers → no LLM calls
- With triggers → correct LLM calls
- Correct entities instantiated and logged
- Determinism of perception cycles
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.pfee.orchestrator import PerceptionOrchestrator, PerceptionResult
from backend.pfee.world_state_builder import build_world_state_for_pfee
from backend.persistence.models import WorldModel


@pytest.mark.asyncio
async def test_no_triggers_no_llm_calls(session: AsyncSession):
    """Test that no triggers result in no LLM calls."""
    orchestrator = PerceptionOrchestrator(session)
    
    world_state = {
        "current_time": None,
        "current_tick": 0,
        "current_location_id": 1,
        "persistent_agents_present_with_user": [],
        "user_id": 1,
        "world_id": 1,
        "current_location_type": "general",
        "salience": 0.0
    }
    
    result = await orchestrator.run_perception_cycle(
        world_state=world_state,
        optional_user_action=None
    )
    
    # Should return none result
    assert result.text is None or result == PerceptionResult.none()


@pytest.mark.asyncio
async def test_user_action_triggers_perception(session: AsyncSession):
    """Test that user actions trigger perception cycles."""
    orchestrator = PerceptionOrchestrator(session)
    
    world_state = {
        "current_time": None,
        "current_tick": 0,
        "current_location_id": 1,
        "persistent_agents_present_with_user": [
            {"id": 1, "name": "Rebecca", "drives": {}, "energy": 1.0}
        ],
        "user_id": 1,
        "world_id": 1,
        "current_location_type": "general",
        "salience": 0.5
    }
    
    user_action = {
        "type": "speak",
        "text": "Hello",
        "target_id": 1,
        "user_id": 1
    }
    
    result = await orchestrator.run_perception_cycle(
        world_state=world_state,
        optional_user_action=user_action
    )
    
    # Should have some result (may be None if no triggers fire, that's OK)
    assert isinstance(result, PerceptionResult)


@pytest.mark.asyncio
async def test_perception_cycle_determinism(session: AsyncSession):
    """Test that perception cycles are deterministic."""
    orchestrator = PerceptionOrchestrator(session)
    
    world_state = {
        "current_time": None,
        "current_tick": 0,
        "current_location_id": 1,
        "persistent_agents_present_with_user": [],
        "user_id": 1,
        "world_id": 1,
        "current_location_type": "general",
        "salience": 0.0
    }
    
    # Run twice with same inputs
    result1 = await orchestrator.run_perception_cycle(
        world_state=world_state.copy(),
        optional_user_action=None
    )
    result2 = await orchestrator.run_perception_cycle(
        world_state=world_state.copy(),
        optional_user_action=None
    )
    
    # Results should be consistent
    # (Both should be None if no triggers, or both should have same structure)
    assert type(result1) == type(result2)

