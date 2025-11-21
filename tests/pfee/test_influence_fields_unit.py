import pytest
from sqlalchemy import select

from backend.pfee.influence_fields import InfluenceFieldManager
from backend.persistence.models import InfluenceFieldModel
from tests.pfee import factories


@pytest.mark.asyncio
async def test_influence_field_created_with_baseline(session):
    world = await factories.create_world(session)
    location = await factories.create_location(session, world)
    agent = await factories.create_agent(session, world, location, name="Ava")

    manager = InfluenceFieldManager(session)
    await manager.update_influence_fields_from_background(
        {"persistent_agents": [{"id": agent.id}]}
    )

    stored = (
        await session.execute(
            select(InfluenceFieldModel).where(InfluenceFieldModel.agent_id == agent.id)
        )
    ).scalar_one()
    assert stored.mood_offset == {"valence_delta": 0.0, "arousal_delta": 0.0}
    assert stored.drive_pressures == {}
    assert stored.pending_contact_probability == {}
    assert stored.unresolved_tension_topics == []


@pytest.mark.asyncio
async def test_influence_field_updates_are_deterministic(session):
    world = await factories.create_world(session)
    location = await factories.create_location(session, world)
    agent = await factories.create_agent(
        session,
        world,
        location,
        name="Kai",
        drives={"relatedness": {"level": 0.9}},
        mood={"valence": 0.1, "arousal": 0.2},
    )

    manager = InfluenceFieldManager(session)
    world_state = {
        "persistent_agents": [
            {
                "id": agent.id,
                "drives": {"relatedness": {"level": 0.9}},
                "arcs": {
                    "conflict": {
                        "intensity": 0.8,
                        "valence_bias": -0.5,
                        "topic_vector": ["tour"],
                    }
                },
            }
        ]
    }

    await manager.update_influence_fields_from_background(world_state)
    await manager.update_influence_fields_from_background(world_state)

    stored = (
        await session.execute(
            select(InfluenceFieldModel).where(InfluenceFieldModel.agent_id == agent.id)
        )
    ).scalar_one()
    # Drive pressure accumulates deterministically
    # Background update keeps deterministic pressure
    assert stored.drive_pressures["relatedness"] == pytest.approx(0.09, rel=1e-3)
    # Tension topics are deduplicated even after multiple updates
    assert stored.unresolved_tension_topics.count("tour") == 1


@pytest.mark.asyncio
async def test_influence_field_persists_across_sessions(session, session_factory):
    world = await factories.create_world(session)
    location = await factories.create_location(session, world)
    agent = await factories.create_agent(session, world, location, name="Mara")

    manager = InfluenceFieldManager(session)
    await manager.update_influence_fields_from_background(
        {"persistent_agents": [{"id": agent.id}]}
    )

    await session.flush()

    async with session_factory() as new_session:
        manager2 = InfluenceFieldManager(new_session)
        snapshot = await manager2.query_influence_for_agent(agent.id)

        assert snapshot is not None
        assert snapshot.agent_id == agent.id
        assert snapshot.mood_offset == {"valence_delta": 0.0, "arousal_delta": 0.0}
        assert snapshot.drive_pressures == {}

