from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from backend.pfee.info_events import InformationEventManager, InfoEventType
from backend.pfee.orchestrator import PerceptionOrchestrator
from backend.pfee.triggers import TriggerReason
from backend.persistence.database import Base
from backend.persistence.models import (
    InfoEventModel,
    IntentionModel,
    MemoryModel,
    PFEELogModel,
)
from tests.pfee import factories
from tests.pfee.fakes import FakeCognitionService, FakeRenderEngine


def _make_orchestrator(session, cognition_scenario="simple_dialogue", renderer_text="Rendered."):
    return PerceptionOrchestrator(
        session,
        cognition_service=FakeCognitionService(cognition_scenario),
        render_engine=FakeRenderEngine(renderer_text),
    )


@pytest.mark.asyncio
async def test_simple_dialogue_perception_cycle(session, seeded_world, world_state_builder):
    orchestrator = _make_orchestrator(session, renderer_text="Ava smiles back.")
    co_agent = seeded_world["other_agent"]
    user_agent = seeded_world["user_agent"]
    world_state = world_state_builder(
        world=seeded_world["world"],
        location=seeded_world["location"],
        user_agent=user_agent,
        co_agents=[co_agent],
        salience=0.7,
    )
    user_action = {"type": "speak", "text": "How are you?", "target_id": co_agent.id}

    result = await orchestrator.run_perception_cycle(world_state, optional_user_action=user_action)

    assert result.text == "Ava smiles back."
    if result.cognition_output and result.cognition_output.get("utterance"):
        assert result.cognition_output["utterance"].startswith("She smiles")
    memories = (await session.execute(select(MemoryModel))).scalars().all()
    assert len(memories) >= 1
    logs = (await session.execute(select(PFEELogModel).where(PFEELogModel.log_type == "cycle"))).scalars().all()
    assert len(logs) == 1


@pytest.mark.asyncio
async def test_time_jump_instruction_advances_world_time(session, seeded_world, world_state_builder):
    orchestrator = _make_orchestrator(session)
    info_manager = InformationEventManager(session)
    world = seeded_world["world"]
    co_agent = seeded_world["other_agent"]
    user_agent = seeded_world["user_agent"]
    now = world.current_time

    await info_manager.create_info_event(
        event_type=InfoEventType.MESSAGE,
        content={"text": "Reminder"},
        sender_id=co_agent.id,
        sender_type="agent",
        recipient_id=user_agent.id,
        due_time=now,
    )
    world_state = world_state_builder(
        world=world,
        location=seeded_world["location"],
        user_agent=user_agent,
        co_agents=[co_agent],
        salience=0.4,
    )
    user_action = {"type": "sleep", "duration_seconds": 3 * 3600}

    result = await orchestrator.run_perception_cycle(world_state, optional_user_action=user_action)

    assert result.world_state["current_time"] == world.current_time
    assert world.current_time == now + timedelta(hours=3)


@pytest.mark.asyncio
async def test_information_event_triggers_perception_cycle(session, seeded_world, world_state_builder):
    orchestrator = _make_orchestrator(session)
    info_manager = InformationEventManager(session)
    world = seeded_world["world"]
    co_agent = seeded_world["other_agent"]
    user_agent = seeded_world["user_agent"]
    now = datetime(2025, 5, 1, 11, tzinfo=timezone.utc)
    world.current_time = now

    event_id = await info_manager.create_info_event(
        event_type=InfoEventType.EMAIL,
        content={"subject": "Update"},
        sender_id=co_agent.id,
        sender_type="agent",
        recipient_id=user_agent.id,
        due_time=now,
    )
    world_state = world_state_builder(
        world=world,
        location=seeded_world["location"],
        user_agent=user_agent,
        co_agents=[co_agent],
        salience=0.65,
    )

    result = await orchestrator.run_perception_cycle(world_state)

    assert any(decision.reason == TriggerReason.INFO_EVENT for decision in result.triggers_fired)
    stored_event = (
        await session.execute(select(InfoEventModel).where(InfoEventModel.id == event_id))
    ).scalar_one()
    assert stored_event.processed is True
    memories = (await session.execute(select(MemoryModel))).scalars().all()
    assert memories, "Information event should create a memory of the interaction."


@pytest.mark.asyncio
async def test_perception_cycle_is_deterministic(async_engine, session_factory, world_state_builder):
    async def run_cycle():
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        async with session_factory() as local_session:
            world = await factories.create_world(local_session)
            location = await factories.create_location(local_session, world)
            user_agent = await factories.create_agent(local_session, world, location, name="Rebecca")
            co_agent = await factories.create_agent(
                local_session,
                world,
                location,
                name="Ava",
                drives={"relatedness": {"level": 0.85}},
            )
            await factories.create_relationship(
                local_session,
                co_agent,
                target_user_id=user_agent.id,
                warmth=0.9,
                trust=0.8,
                familiarity=0.95,
            )

            orchestrator = _make_orchestrator(local_session)
            world_state = world_state_builder(
                world=world,
                location=location,
                user_agent=user_agent,
                co_agents=[co_agent],
                salience=0.7,
            )
            user_action = {"type": "speak", "target_id": co_agent.id, "text": "Test"}
            result = await orchestrator.run_perception_cycle(world_state, optional_user_action=user_action)

            memories = (
                await local_session.execute(select(MemoryModel).order_by(MemoryModel.id))
            ).scalars().all()
            logs = (
                await local_session.execute(select(PFEELogModel).order_by(PFEELogModel.id))
            ).scalars().all()

            return {
                "text": result.text,
                "cognition": result.cognition_output,
                "memories": [m.description for m in memories],
                "log_types": [log.log_type for log in logs],
            }

    summary_one = await run_cycle()
    summary_two = await run_cycle()
    assert summary_one == summary_two


@pytest.mark.asyncio
async def test_invalid_cognition_output_is_rejected(session, seeded_world, world_state_builder):
    orchestrator = _make_orchestrator(session, cognition_scenario="invalid_action")
    co_agent = seeded_world["other_agent"]
    user_agent = seeded_world["user_agent"]
    world_state = world_state_builder(
        world=seeded_world["world"],
        location=seeded_world["location"],
        user_agent=user_agent,
        co_agents=[co_agent],
        salience=0.8,
    )
    user_action = {"type": "speak", "text": "Try something wild", "target_id": co_agent.id}

    result = await orchestrator.run_perception_cycle(world_state, optional_user_action=user_action)

    assert result.cognition_output is None or result.cognition_output["action"] is None
    error_logs = (
        await session.execute(select(PFEELogModel).where(PFEELogModel.log_type == "error"))
    ).scalars().all()
    assert error_logs, "Validation failure should produce an error log."


@pytest.mark.asyncio
async def test_numeric_state_not_exposed_to_cognition(session, seeded_world, world_state_builder):
    fake_cognition = FakeCognitionService("relationship_update")
    renderer = FakeRenderEngine("Narrative.")
    orchestrator = PerceptionOrchestrator(
        session,
        cognition_service=fake_cognition,
        render_engine=renderer,
    )

    co_agent = seeded_world["other_agent"]
    user_agent = seeded_world["user_agent"]
    world_state = world_state_builder(
        world=seeded_world["world"],
        location=seeded_world["location"],
        user_agent=user_agent,
        co_agents=[co_agent],
        salience=0.75,
    )
    user_action = {"type": "speak", "text": "Let's check semantic mapping", "target_id": co_agent.id}

    result = await orchestrator.run_perception_cycle(world_state, optional_user_action=user_action)

    semantic_input = fake_cognition.calls[0]
    assert isinstance(semantic_input.mood_summary, str)
    assert isinstance(semantic_input.personality_activation, str)
    drives_str = str(semantic_input.drives_summary)
    assert "level" not in drives_str
    assert "0." not in drives_str
    assert all(isinstance(item, str) for item in semantic_input.intentions_summary)

