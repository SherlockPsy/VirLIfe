"""
PRODUCTION TEST CONFIGURATION

This overrides conftest.py to use the production Railway database.
ONLY USE FOR DESTRUCTIVE TESTING - tests will wipe and reseed production.
"""

import pytest
import asyncio
import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, create_async_engine, async_sessionmaker

from backend.persistence.database import Base
from backend.persistence.models import (
    WorldModel, AgentModel, LocationModel, RelationshipModel,
    MemoryModel, ArcModel, IntentionModel, ObjectModel,
    CalendarModel, InfluenceFieldModel, UserModel
)
from backend.seeding.seed_baseline_world import seed_baseline_world

# PRODUCTION DATABASE URL
PRODUCTION_DATABASE_URL = os.getenv(
    "PRODUCTION_DATABASE_URL",
    "postgresql://postgres:rUaCGawjVEoluMBJZzZgAerZfKPmTbQu@interchange.proxy.rlwy.net:50418/railway"
)

# Convert to asyncpg format
if PRODUCTION_DATABASE_URL.startswith("postgresql://"):
    PRODUCTION_DATABASE_URL = PRODUCTION_DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
elif PRODUCTION_DATABASE_URL.startswith("postgres://"):
    PRODUCTION_DATABASE_URL = PRODUCTION_DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    """
    Create a test database engine using PRODUCTION database.
    
    WARNING: This uses the production Railway database.
    Tests will wipe and reseed this database.
    """
    engine = create_async_engine(
        PRODUCTION_DATABASE_URL,
        echo=False,
        pool_size=5,
        max_overflow=5,
        pool_recycle=3600,
        pool_pre_ping=True
    )
    
    # Create all tables (if they don't exist)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # NOTE: We do NOT drop tables - this is production
    await engine.dispose()


@pytest.fixture
async def test_session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a test database session using PRODUCTION database.
    """
    async_session_maker = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session_maker() as session:
        yield session
        # NOTE: We commit changes in production tests (they're meant to be destructive)


@pytest.fixture
async def seeded_world(test_session: AsyncSession, test_engine: AsyncEngine) -> dict:
    """
    Seed the baseline world in PRODUCTION database and return world metadata.
    
    WARNING: This will WIPE and reseed the production database.
    """
    # Wipe and reseed production
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

