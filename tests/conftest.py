"""
Pytest configuration and shared fixtures for test suite.

Implements Section F.0: Test suite structure with async database fixtures.
"""

import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from backend.persistence.database import Base
from backend.persistence.models import (
    WorldModel, AgentModel, LocationModel, RelationshipModel,
    MemoryModel, ArcModel, IntentionModel, ObjectModel,
    CalendarModel, InfluenceFieldModel, UserModel
)
from backend.seeding.seed_baseline_world import seed_baseline_world


# Test database URL (in-memory SQLite for tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    """
    Create a test database engine.
    Uses in-memory SQLite for fast, isolated tests.
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
async def test_session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a test database session.
    Resets DB between tests (per Section F.0).
    """
    async_session_maker = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def seeded_world(test_session: AsyncSession, test_engine: AsyncEngine) -> dict:
    """
    Seed the baseline world and return world metadata.
    
    Returns:
        dict with keys: world_id, george_agent_id, rebecca_agent_id, etc.
    """
    await seed_baseline_world(test_engine)
    
    # Query to get IDs
    from sqlalchemy import select
    
    # Get world
    stmt = select(WorldModel)
    result = await test_session.execute(stmt)
    world = result.scalars().first()
    
    # Get agents
    stmt = select(AgentModel)
    result = await test_session.execute(stmt)
    agents = result.scalars().all()
    
    agent_map = {agent.name: agent for agent in agents}
    
    return {
        "world_id": world.id if world else None,
        "george_agent_id": agent_map.get("George").id if "George" in agent_map else None,
        "rebecca_agent_id": agent_map.get("Rebecca Ferguson").id if "Rebecca Ferguson" in agent_map else None,
        "lucy_agent_id": agent_map.get("Lucy").id if "Lucy" in agent_map else None,
        "nadine_agent_id": agent_map.get("Nadine").id if "Nadine" in agent_map else None,
        "agents": agent_map
    }

