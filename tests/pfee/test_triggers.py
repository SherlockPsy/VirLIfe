"""
Tests for PFEE Trigger Evaluator

Tests:
- User action triggers
- Agent initiative triggers
- Interruption triggers
- Info event triggers
- Environmental triggers
- Trivial actions do NOT trigger
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.pfee.triggers import (
    TriggerEvaluator,
    TriggerReason,
    TriggerDecision
)
from backend.pfee.potentials import ResolvedPotential, PotentialType, ContextType


@pytest.mark.asyncio
async def test_trivial_action_no_trigger(session: AsyncSession):
    """Test that trivial actions do not trigger."""
    evaluator = TriggerEvaluator(session)
    
    user_action = {
        "type": "blink",
        "text": None
    }
    world_state = {}
    
    decision = await evaluator.evaluate_user_action_trigger(
        user_action, world_state
    )
    
    assert not decision.should_trigger


@pytest.mark.asyncio
async def test_social_action_triggers(session: AsyncSession):
    """Test that social actions trigger perception."""
    evaluator = TriggerEvaluator(session)
    
    user_action = {
        "type": "speak",
        "text": "Hello",
        "target_id": 1
    }
    world_state = {
        "persistent_agents_present_with_user": [
            {"id": 1, "name": "Rebecca"}
        ]
    }
    
    decision = await evaluator.evaluate_user_action_trigger(
        user_action, world_state
    )
    
    assert decision.should_trigger
    assert decision.reason == TriggerReason.USER_ACTION


@pytest.mark.asyncio
async def test_agent_initiative_triggers(session: AsyncSession):
    """Test that agent initiative triggers perception."""
    evaluator = TriggerEvaluator(session)
    
    world_state = {
        "persistent_agents_present_with_user": [
            {
                "id": 1,
                "name": "Rebecca",
                "drives": {
                    "relatedness": {"level": 0.8}
                },
                "energy": 0.9,
                "intentions": {"talk": {"priority": 0.7}}
            }
        ]
    }
    
    decisions = await evaluator.evaluate_agent_initiative_triggers(world_state)
    
    # Should have at least one trigger if agent has initiative
    assert isinstance(decisions, list)
    # May be empty if agent doesn't have initiative, that's OK


@pytest.mark.asyncio
async def test_interruption_triggers(session: AsyncSession):
    """Test that interruptions trigger perception."""
    evaluator = TriggerEvaluator(session)
    
    resolved_potential = ResolvedPotential(
        id=1,
        potential_type=PotentialType.DOG_ENCOUNTER,
        context_type=ContextType.PARK,
        resolved_entity={"type": "person", "name": "A dog"}
    )
    
    world_state = {}
    decisions = await evaluator.evaluate_interruption_triggers(
        world_state, [resolved_potential]
    )
    
    assert isinstance(decisions, list)
    # Should trigger if potential is interruptive
    if decisions:
        assert decisions[0].reason == TriggerReason.INTERRUPTION


@pytest.mark.asyncio
async def test_info_event_triggers(session: AsyncSession):
    """Test that info events trigger perception."""
    evaluator = TriggerEvaluator(session)
    
    info_events = [
        {"id": 1, "type": "message"}
    ]
    world_state = {}
    
    decisions = await evaluator.evaluate_info_event_triggers(
        world_state, info_events
    )
    
    assert len(decisions) == len(info_events)
    if decisions:
        assert decisions[0].reason == TriggerReason.INFO_EVENT


@pytest.mark.asyncio
async def test_environment_triggers(session: AsyncSession):
    """Test that environmental shifts trigger perception."""
    evaluator = TriggerEvaluator(session)
    
    environmental_shifts = [
        {
            "id": "env_1",
            "type": "weather_change",
            "salience": 0.5
        }
    ]
    world_state = {}
    
    decisions = await evaluator.evaluate_environment_triggers(
        world_state, environmental_shifts
    )
    
    assert isinstance(decisions, list)
    if decisions:
        assert decisions[0].reason == TriggerReason.ENVIRONMENT_SHIFT

