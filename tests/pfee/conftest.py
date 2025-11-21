import asyncio
from datetime import datetime, timezone
from typing import Callable, Dict, List

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.persistence.database import Base
from backend.persistence.models import AgentModel

# Ensure models are registered with SQLAlchemy metadata
import backend.persistence.models  # noqa: F401
import backend.pfee.potentials  # noqa: F401
import backend.pfee.influence_fields  # noqa: F401
import backend.pfee.info_events  # noqa: F401
import backend.pfee.logging  # noqa: F401

from tests.pfee import factories


DEFAULT_TIME = datetime(2025, 5, 1, 9, 0, tzinfo=timezone.utc)


@pytest.fixture(scope="session")
def event_loop():
    """Create a dedicated event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def async_engine():
    """Create an in-memory SQLite engine shared across tests."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture(scope="session")
def session_factory(async_engine):
    """Return a sessionmaker bound to the shared engine."""
    return sessionmaker(async_engine, expire_on_commit=False, class_=AsyncSession)


@pytest_asyncio.fixture
async def session(async_engine):
    """Provide a clean database for every test."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(
        async_engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )
    async with async_session() as db_session:
        yield db_session
        await db_session.rollback()


@pytest.fixture
def fixed_time() -> datetime:
    return DEFAULT_TIME


@pytest_asyncio.fixture
async def seeded_world(session: AsyncSession):
    """
    Create a minimal but non-trivial world state that includes:
    - world
    - shared location
    - protagonist agent (user proxy)
    - another persistent agent with relationships, memories, intentions
    """
    world = await factories.create_world(session, current_time=DEFAULT_TIME)
    location = await factories.create_location(session, world)

    protagonist = await factories.create_agent(
        session,
        world,
        location,
        name="Rebecca",
        drives={
            "relatedness": {"level": 0.4, "sensitivity": 1.0},
            "autonomy": {"level": 0.5, "sensitivity": 1.0},
        },
    )

    counterpart = await factories.create_agent(
        session,
        world,
        location,
        name="Ava",
        drives={
            "relatedness": {"level": 0.8, "sensitivity": 1.0},
            "competence": {"level": 0.6, "sensitivity": 1.0},
        },
        mood={"valence": 0.2, "arousal": 0.4},
    )

    await factories.create_relationship(
        session,
        counterpart,
        target_user_id=1,
        warmth=0.8,
        trust=0.75,
        tension=0.15,
        familiarity=0.9,
    )

    await factories.create_memory(
        session,
        counterpart,
        description="Shared coffee with the user earlier this morning.",
    )
    await factories.create_intention(
        session,
        counterpart,
        description="Offer the user support about their upcoming rehearsal.",
        intention_type="support",
        priority=0.7,
    )

    return {
        "world": world,
        "location": location,
        "user_agent": protagonist,
        "other_agent": counterpart,
    }


@pytest.fixture
def world_state_builder():
    """
    Helper to build PFEE world_state dictionaries that include
    agents, location, and semantic context.
    """

    def _build(
        *,
        world,
        location,
        user_agent,
        co_agents: List[AgentModel],
        salience: float = 0.6,
        weather: str = "clear",
    ) -> Dict[str, any]:
        agents_payload = []
        for agent in co_agents:
            agents_payload.append(
                {
                    "id": agent.id,
                    "name": agent.name,
                    "location_id": agent.location_id,
                    "mood": agent.mood,
                    "drives": agent.drives,
                    "energy": agent.energy,
                    "intentions": {},
                    "arcs": {},
                }
            )

        world_state = {
            "current_time": world.current_time,
            "current_tick": world.current_tick,
            "current_location_id": location.id,
            "current_location": location.name,
            "current_location_type": location.attributes.get("type", "general") if location.attributes else "general",
            "world_id": world.id,
            "user_id": user_agent.id,
            "salience": salience,
            "persistent_agents_present_with_user": agents_payload,
            "persistent_agents": agents_payload,
            "objects_in_location": [
                {"id": 1, "name": "ceramic mug"},
                {"id": 2, "name": "warm lamp"},
            ],
            "weather": weather,
        }
        return world_state

    return _build

