"""
Tests for Trigger Evaluator

Implements PFEE_PLAN.md Phase P9 test requirements for triggers.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.pfee.triggers import TriggerEvaluator, TriggerReason


@pytest.mark.asyncio
async def test_trivial_actions_do_not_trigger(session: AsyncSession):
    """Test that trivial actions do NOT trigger LLM."""
    evaluator = TriggerEvaluator(session)
    
    trivial_action = {
        "type": "minor_movement",
        "description": "shifts slightly"
    }
    world_state = {}
    
    decision = await evaluator.evaluate_user_action_trigger(
        trivial_action, world_state
    )
    
    assert not decision.should_trigger
    assert decision.reason == TriggerReason.NONE


@pytest.mark.asyncio
async def test_meaningful_speech_triggers(session: AsyncSession):
    """Test that meaningful speech/actions DO trigger."""
    evaluator = TriggerEvaluator(session)
    
    meaningful_action = {
        "type": "speech",
        "description": "Hello, how are you?",
        "target": "agent:1"
    }
    world_state = {
        "agents": [{"id": 1, "name": "Rebecca"}]
    }
    
    decision = await evaluator.evaluate_user_action_trigger(
        meaningful_action, world_state
    )
    
    assert decision.should_trigger
    assert decision.reason == TriggerReason.USER_ACTION_SOCIAL


@pytest.mark.asyncio
async def test_agent_initiative_triggers(session: AsyncSession):
    """Test that agent initiative triggers fire under correct conditions."""
    evaluator = TriggerEvaluator(session)
    
    world_state = {
        "persistent_agents_present_with_user": [
            {
                "id": 1,
                "name": "Rebecca",
                "drives": {
                    "relatedness": {"level": 0.8}  # High unmet need
                },
                "intentions": []
            }
        ]
    }
    
    decisions = await evaluator.evaluate_agent_initiative_triggers(world_state)
    
    assert len(decisions) > 0
    assert any(d.reason == TriggerReason.AGENT_INITIATIVE for d in decisions)

