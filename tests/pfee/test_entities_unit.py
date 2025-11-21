import pytest
from sqlalchemy import select

from backend.pfee.entities import (
    EntityPersistenceManager,
    PersistenceLevel,
    EntityType,
)
from backend.persistence.models import AgentModel
from tests.pfee import factories


@pytest.mark.asyncio
async def test_single_encounter_entity_is_ephemeral(session):
    manager = EntityPersistenceManager(session)
    entity = {"id": 1, "salient_encounter_count": 1}
    context = {"user_routine_locations": []}

    level = await manager.classify_entity_persistence(
        entity, context, EntityType.PERSON
    )

    assert level == PersistenceLevel.EPHEMERAL


@pytest.mark.asyncio
async def test_multiple_encounters_promote_to_persistent(session):
    world = await factories.create_world(session)
    location = await factories.create_location(session, world)
    agent = await factories.create_agent(session, world, location, name="Ava")

    manager = EntityPersistenceManager(session)
    entity = {"id": agent.id, "salient_encounter_count": 5}
    context = {"user_routine_locations": []}

    level = await manager.classify_entity_persistence(
        entity, context, EntityType.PERSON
    )
    assert level == PersistenceLevel.PERSISTENT

    updated = await manager.promote_to_persistent(agent.id, EntityType.PERSON)
    assert updated is True

    refreshed = (
        await session.execute(select(AgentModel).where(AgentModel.id == agent.id))
    ).scalar_one()
    assert refreshed.status_flags["persistence_level"] == PersistenceLevel.PERSISTENT.value


@pytest.mark.asyncio
async def test_persistence_promotion_is_idempotent(session):
    world = await factories.create_world(session)
    location = await factories.create_location(session, world)
    agent = await factories.create_agent(
        session,
        world,
        location,
        name="Kai",
        status_flags={"persistence_level": PersistenceLevel.PERSISTENT.value},
    )

    manager = EntityPersistenceManager(session)
    result_first = await manager.promote_to_persistent(agent.id, EntityType.PERSON)
    result_second = await manager.promote_to_persistent(agent.id, EntityType.PERSON)

    assert result_first is True
    assert result_second is True

    refreshed = (
        await session.execute(select(AgentModel).where(AgentModel.id == agent.id))
    ).scalar_one()
    assert refreshed.status_flags["persistence_level"] == PersistenceLevel.PERSISTENT.value

