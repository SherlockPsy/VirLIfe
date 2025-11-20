import datetime
import asyncio
from typing import List, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from backend.persistence.repo import WorldRepo, AgentRepo
from backend.persistence.models import WorldModel, EventModel, AgentModel, CalendarModel

class WorldEngine:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.world_repo = WorldRepo(session)
        self.agent_repo = AgentRepo(session)
        self.world_id = 1 # Assuming single world for now

    async def get_or_create_world(self) -> WorldModel:
        world = await self.world_repo.get_world(self.world_id)
        if not world:
            world = await self.world_repo.create_world()
            self.world_id = world.id
        
        # Ensure timezone awareness immediately
        if world.current_time.tzinfo is None:
            world.current_time = world.current_time.replace(tzinfo=datetime.timezone.utc)
            
        return world

    async def tick(self, seconds: int = 60) -> WorldModel:
        """
        Advances the world clock by `seconds`.
        Processes events, schedules, and continuity.
        """
        world = await self.get_or_create_world()
        
        # 1. Advance Time
        world.current_tick += 1
        
        new_time = world.current_time + datetime.timedelta(seconds=seconds)
        world.current_time = new_time
        
        # 2. Process Calendar & Obligations (Appendix J)
        await self._process_calendars(world)
        
        # 3. Generate Unexpected Events (Appendix I)
        await self._generate_incursions(world)
        
        # 4. Process Event Queue (Basic FIFO for now)
        # In a real loop, we might process pending events here.
        
        await self.world_repo.save_world(world)
        return world

    async def _process_calendars(self, world: WorldModel):
        """
        Checks all agents' calendars.
        Generates events for starting/upcoming items.
        """
        # Define window: [current_time - tick_duration, current_time] for "started now"
        # But simpler: just check what starts in the next minute?
        # Let's assume tick is called every minute or we pass the delta.
        # We'll check for items starting between now and now + 1 minute (if tick is 1 min).
        # Or better: check for items that started <= current_time and are still "pending".
        
        # 1. Find pending items that have started
        # We need a repo method for this.
        # For now, let's use the get_upcoming_calendar_items for reminders.
        
        # Check for reminders (e.g. 15 mins before)
        reminder_window_start = world.current_time + datetime.timedelta(minutes=15)
        reminder_window_end = reminder_window_start + datetime.timedelta(seconds=60) # 1 min window
        
        upcoming = await self.agent_repo.get_upcoming_calendar_items(reminder_window_start, reminder_window_end)
        
        for item in upcoming:
            # Generate reminder event
            await self.world_repo.add_event({
                "world_id": world.id,
                "type": "calendar_reminder",
                "description": f"Reminder: {item.agent.name} has '{item.title}' in 15 minutes.",
                "tick": world.current_tick,
                "timestamp": world.current_time,
                "source_entity_id": "system",
                "target_entity_id": f"agent:{item.agent_id}",
                "payload": {"calendar_id": item.id, "minutes_remaining": 15}
            })

        # Check for items starting NOW
        start_window_end = world.current_time
        start_window_start = world.current_time - datetime.timedelta(seconds=60)
        
        starting = await self.agent_repo.get_upcoming_calendar_items(start_window_start, start_window_end)
        
        for item in starting:
            if item.status == "pending":
                item.status = "active"
                self.session.add(item)
                
                await self.world_repo.add_event({
                    "world_id": world.id,
                    "type": "calendar_start",
                    "description": f"{item.agent.name}'s event '{item.title}' is starting.",
                    "tick": world.current_tick,
                    "timestamp": world.current_time,
                    "source_entity_id": "system",
                    "target_entity_id": f"agent:{item.agent_id}",
                    "payload": {"calendar_id": item.id}
                })

    async def _generate_incursions(self, world: WorldModel):
        """
        Generates unexpected events based on world state.
        """
        # Deterministic check for random incursions (e.g. ambient noise)
        # Seeded by tick + world_id
        import random
        random.seed(world.current_tick + self.world_id)
        
        if random.random() < 0.01: # 1% chance per tick of ambient event
            await self.world_repo.add_event({
                "world_id": world.id,
                "type": "ambient",
                "description": "A distant siren wails.",
                "tick": world.current_tick,
                "timestamp": world.current_time,
                "source_entity_id": "system",
                "target_entity_id": "all"
            })

    async def move_agent(self, agent_id: int, target_location_id: int):
        agent = await self.agent_repo.get_agent_by_id(agent_id)
        if not agent:
            raise ValueError("Agent not found")
            
        old_location_id = agent.location_id
        agent.location_id = target_location_id
        await self.agent_repo.save_agent(agent)
        
        # Generate movement event
        world = await self.get_or_create_world()
        await self.world_repo.add_event({
            "world_id": world.id,
            "type": "movement",
            "description": f"{agent.name} moved from location {old_location_id} to {target_location_id}.",
            "tick": world.current_tick,
            "timestamp": world.current_time,
            "source_entity_id": f"agent:{agent.id}",
            "payload": {"from": old_location_id, "to": target_location_id}
        })

    async def schedule_event(self, agent_id: int, title: str, start_time: datetime.datetime, type: str = "appointment"):
        """
        Adds a calendar item.
        """
        await self.agent_repo.add_calendar_item({
            "agent_id": agent_id,
            "title": title,
            "start_time": start_time,
            "type": type,
            "status": "pending"
        })
