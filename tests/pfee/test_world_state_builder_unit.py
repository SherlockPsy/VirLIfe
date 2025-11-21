import pytest

from backend.pfee.world_state_builder import build_world_state_for_pfee
from tests.pfee import factories


@pytest.mark.asyncio
async def test_world_state_builder_includes_user_and_present_agents(session):
    world = await factories.create_world(session)
    location = await factories.create_location(session, world, name="Loft")
    user_agent = await factories.create_agent(session, world, location, name="Rebecca")
    other_agent = await factories.create_agent(session, world, location, name="Ava")

    world_state = await build_world_state_for_pfee(session, world, user_agent.id)

    assert world_state["user_id"] == user_agent.id
    assert world_state["current_location_id"] == 1
    present_ids = [agent["id"] for agent in world_state["persistent_agents_present_with_user"]]
    assert user_agent.id in present_ids
    assert other_agent.id in present_ids


@pytest.mark.asyncio
async def test_world_state_builder_filters_agents_by_location(session):
    world = await factories.create_world(session)
    location_one = await factories.create_location(session, world, name="Studio")
    location_two = await factories.create_location(session, world, name="Cafe")

    user_agent = await factories.create_agent(session, world, location_one, name="Rebecca")
    await factories.create_agent(session, world, location_one, name="Ava")
    distant_agent = await factories.create_agent(session, world, location_two, name="Lina")

    world_state = await build_world_state_for_pfee(session, world, user_agent.id)
    present_ids = [agent["id"] for agent in world_state["persistent_agents_present_with_user"]]

    assert distant_agent.id not in present_ids
    assert len(present_ids) == 2  # user + co-present agent

