from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.persistence.models import (
    WorldModel,
    LocationModel,
    AgentModel,
    RelationshipModel,
    MemoryModel,
    IntentionModel,
)

DEFAULT_TIME = datetime(2025, 5, 1, 9, 0, tzinfo=timezone.utc)


async def create_world(
    session: AsyncSession,
    *,
    current_time: datetime = DEFAULT_TIME,
    current_tick: int = 0,
) -> WorldModel:
    world = WorldModel(current_time=current_time, current_tick=current_tick)
    session.add(world)
    await session.flush()
    return world


async def create_location(
    session: AsyncSession,
    world: WorldModel,
    *,
    name: str = "Loft",
    description: str = "A sunlit loft with wide windows.",
    attributes: Optional[Dict[str, Any]] = None,
) -> LocationModel:
    location = LocationModel(
        name=name,
        description=description,
        world_id=world.id,
        attributes=attributes or {"persistence_level": "persistent"},
        adjacency=[],
    )
    session.add(location)
    await session.flush()
    return location


async def create_agent(
    session: AsyncSession,
    world: WorldModel,
    location: Optional[LocationModel],
    *,
    name: str,
    mood: Optional[Dict[str, float]] = None,
    drives: Optional[Dict[str, Any]] = None,
    energy: float = 0.9,
    personality_kernel: Optional[Dict[str, Any]] = None,
    status_flags: Optional[Dict[str, Any]] = None,
    last_cognition_timestamp: Optional[datetime] = None,
) -> AgentModel:
    agent = AgentModel(
        name=name,
        world_id=world.id,
        location_id=location.id if location else None,
        energy=energy,
        mood=mood or {"valence": 0.0, "arousal": 0.0},
        drives=drives or {},
        personality_kernel=personality_kernel or {"traits": {"warmth": 0.5}},
        personality_summaries={},
        domain_summaries={},
        cached_context_fragments={},
        status_flags=status_flags or {"persistence_level": "persistent"},
        last_cognition_timestamp=last_cognition_timestamp,
    )
    session.add(agent)
    await session.flush()
    return agent


async def create_relationship(
    session: AsyncSession,
    source_agent: AgentModel,
    *,
    target_agent: Optional[AgentModel] = None,
    target_user_id: Optional[int] = None,
    warmth: float = 0.6,
    trust: float = 0.5,
    tension: float = 0.2,
    familiarity: float = 0.7,
    comfort: float = 0.6,
) -> RelationshipModel:
    relationship = RelationshipModel(
        source_agent_id=source_agent.id,
        target_agent_id=target_agent.id if target_agent else None,
        target_user_id=target_user_id,
        warmth=warmth,
        trust=trust,
        tension=tension,
        attraction=0.2,
        familiarity=familiarity,
        comfort=comfort,
        volatility=0.1,
    )
    session.add(relationship)
    await session.flush()
    return relationship


async def create_memory(
    session: AsyncSession,
    agent: AgentModel,
    *,
    description: str,
    memory_type: str = "episodic",
    salience: float = 0.6,
    timestamp: Optional[datetime] = None,
) -> MemoryModel:
    memory = MemoryModel(
        agent_id=agent.id,
        type=memory_type,
        description=description,
        timestamp=timestamp or DEFAULT_TIME,
        salience=salience,
        semantic_tags=["test"],
    )
    session.add(memory)
    await session.flush()
    return memory


async def create_intention(
    session: AsyncSession,
    agent: AgentModel,
    *,
    description: str,
    priority: float = 0.6,
    horizon: str = "short",
    intention_type: str = "support",
    stability: float = 0.5,
) -> IntentionModel:
    intention = IntentionModel(
        agent_id=agent.id,
        description=description,
        priority=priority,
        horizon=horizon,
        type=intention_type,
        stability=stability,
    )
    session.add(intention)
    await session.flush()
    return intention

