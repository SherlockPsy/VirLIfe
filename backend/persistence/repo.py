from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from backend.persistence.models import (
    AgentModel, WorldModel, LocationModel, RelationshipModel, 
    MemoryModel, ArcModel, IntentionModel, EventModel, UserModel, CalendarModel
)
from typing import List, Optional
import datetime

class AgentRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_agent(self, agent_data: dict) -> AgentModel:
        agent = AgentModel(**agent_data)
        self.session.add(agent)
        await self.session.flush()
        return agent

    async def get_agent_by_id(self, agent_id: int) -> Optional[AgentModel]:
        stmt = select(AgentModel).options(
            selectinload(AgentModel.memories),
            selectinload(AgentModel.arcs),
            selectinload(AgentModel.intentions),
            selectinload(AgentModel.relationships),
            selectinload(AgentModel.location)
        ).where(AgentModel.id == agent_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_agent_by_name(self, name: str) -> Optional[AgentModel]:
        stmt = select(AgentModel).options(
            selectinload(AgentModel.memories),
            selectinload(AgentModel.arcs),
            selectinload(AgentModel.intentions),
            selectinload(AgentModel.relationships),
            selectinload(AgentModel.location)
        ).where(AgentModel.name == name)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def save_agent(self, agent: AgentModel):
        # In SQLAlchemy, if the object is attached to the session, 
        # changes are tracked automatically. 
        # This method is explicit to ensure flush/commit if needed by the caller context,
        # or to re-add detached instances.
        self.session.add(agent)
        await self.session.flush()

    async def add_memory(self, agent_id: int, memory_data: dict) -> MemoryModel:
        memory = MemoryModel(agent_id=agent_id, **memory_data)
        self.session.add(memory)
        await self.session.flush()
        return memory

    async def get_relationships(self, agent_id: int) -> List[RelationshipModel]:
        stmt = select(RelationshipModel).where(RelationshipModel.source_agent_id == agent_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def list_agents_in_location(self, location_id: int) -> List[AgentModel]:
        stmt = select(AgentModel).where(AgentModel.location_id == location_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_calendar_items(self, agent_id: int, start_time: datetime.datetime = None, end_time: datetime.datetime = None) -> List[CalendarModel]:
        stmt = select(CalendarModel).where(CalendarModel.agent_id == agent_id)
        if start_time:
            stmt = stmt.where(CalendarModel.start_time >= start_time)
        if end_time:
            stmt = stmt.where(CalendarModel.start_time <= end_time)
        stmt = stmt.order_by(CalendarModel.start_time.asc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def add_calendar_item(self, item_data: dict) -> CalendarModel:
        item = CalendarModel(**item_data)
        self.session.add(item)
        await self.session.flush()
        return item

    async def get_upcoming_calendar_items(self, start_time: datetime.datetime, end_time: datetime.datetime) -> List[CalendarModel]:
        """
        Global query for calendar items across all agents in a time window.
        """
        stmt = select(CalendarModel).where(
            CalendarModel.start_time >= start_time,
            CalendarModel.start_time <= end_time
        ).options(selectinload(CalendarModel.agent))
        result = await self.session.execute(stmt)
        return result.scalars().all()

class WorldRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_world(self) -> WorldModel:
        world = WorldModel()
        self.session.add(world)
        await self.session.flush()
        return world

    async def get_world(self, world_id: int = 1) -> Optional[WorldModel]:
        stmt = select(WorldModel).options(
            selectinload(WorldModel.locations),
            selectinload(WorldModel.agents)
        ).where(WorldModel.id == world_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def save_world(self, world: WorldModel):
        self.session.add(world)
        await self.session.flush()

    async def add_event(self, event_data: dict) -> EventModel:
        event = EventModel(**event_data)
        self.session.add(event)
        await self.session.flush()
        return event
    
    async def get_recent_events(self, world_id: int, limit: int = 10) -> List[EventModel]:
        stmt = select(EventModel).where(EventModel.world_id == world_id).order_by(EventModel.timestamp.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

class UserRepo:
    def __init__(self, session: AsyncSession):
        self.session = session
        
    async def create_user(self, name: str) -> UserModel:
        user = UserModel(name=name)
        self.session.add(user)
        await self.session.flush()
        return user
        
    async def get_user_by_name(self, name: str) -> Optional[UserModel]:
        stmt = select(UserModel).where(UserModel.name == name)
        result = await self.session.execute(stmt)
        return result.scalars().first()
