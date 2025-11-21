import pytest

from backend.pfee.triggers import (
    TriggerDecision,
    TriggerEvaluator,
    TriggerReason,
)
from backend.pfee.potentials import ResolvedPotential, PotentialType, ContextType


@pytest.mark.asyncio
async def test_trivial_user_action_does_not_trigger(session):
    evaluator = TriggerEvaluator(session)

    decision = await evaluator.evaluate_user_action_trigger(
        {"type": "blink"}, world_state={}
    )

    assert decision.should_trigger is False
    assert decision.reason == TriggerReason.NONE


@pytest.mark.asyncio
async def test_social_action_triggers_with_reason(session):
    evaluator = TriggerEvaluator(session)
    world_state = {
        "persistent_agents_present_with_user": [{"id": 200, "name": "Ava"}]
    }
    user_action = {"type": "speak", "text": "Hi", "target_id": 200}

    decision = await evaluator.evaluate_user_action_trigger(user_action, world_state)

    assert decision.should_trigger is True
    assert decision.reason == TriggerReason.USER_ACTION
    assert decision.metadata["action_type"] == "speak"
    assert decision.metadata["text"] == "Hi"


@pytest.mark.asyncio
async def test_instruction_like_action_triggers_as_context_change(session):
    evaluator = TriggerEvaluator(session)
    world_state = {}
    user_action = {
        "type": "move",
        "metadata": {"instruction": True},
        "text": "System requested relocation.",
    }

    decision = await evaluator.evaluate_user_action_trigger(user_action, world_state)

    assert decision.should_trigger is True
    assert decision.reason == TriggerReason.USER_ACTION
    assert decision.metadata["action_type"] == "move"


@pytest.mark.asyncio
async def test_due_info_event_triggers_perception(session):
    evaluator = TriggerEvaluator(session)
    due_events = [{"id": 10, "type": "message"}]

    decisions = await evaluator.evaluate_info_event_triggers({}, due_events)

    assert len(decisions) == 1
    assert decisions[0].reason == TriggerReason.INFO_EVENT
    assert decisions[0].metadata["info_event_id"] == 10


@pytest.mark.asyncio
async def test_environmental_shift_threshold(session):
    evaluator = TriggerEvaluator(session)
    shifts = [
        {"id": "storm", "type": "weather_change", "salience": 0.55},
        {"id": "ambient", "type": "lighting", "salience": 0.1},
    ]

    decisions = await evaluator.evaluate_environment_triggers({}, shifts)

    assert len(decisions) == 1
    assert decisions[0].reason == TriggerReason.ENVIRONMENT_SHIFT
    assert decisions[0].metadata["shift_id"] == "storm"


@pytest.mark.asyncio
async def test_interruptive_resolved_potential_triggers(session):
    evaluator = TriggerEvaluator(session)
    resolved = ResolvedPotential(
        id=5,
        potential_type=PotentialType.DOG_ENCOUNTER,
        context_type=ContextType.PARK,
        resolved_entity={"type": "person"},
    )

    decisions = await evaluator.evaluate_interruption_triggers({}, [resolved])

    assert len(decisions) == 1
    assert decisions[0].reason == TriggerReason.INTERRUPTION
    assert decisions[0].metadata["potential_type"] == PotentialType.DOG_ENCOUNTER.value

