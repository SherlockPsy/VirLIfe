import pytest
import datetime
from backend.world.engine import WorldEngine
from backend.persistence.repo import AgentRepo, WorldRepo
from backend.persistence.models import CalendarModel

@pytest.mark.asyncio
async def test_calendar_edge_cases(db_session):
    engine = WorldEngine(db_session)
    world = await engine.get_or_create_world()
    agent_repo = AgentRepo(db_session)
    agent = await agent_repo.create_agent({"name": "CalTest", "world_id": world.id})
    
    # 1. No upcoming items
    # Tick should run fine
    await engine.tick(60)
    
    # 2. Multiple overlapping items
    # Event A: Starts T+10m
    # Event B: Starts T+10m
    t_plus_10 = world.current_time + datetime.timedelta(minutes=10)
    
    await engine.schedule_event(agent.id, "Event A", t_plus_10)
    await engine.schedule_event(agent.id, "Event B", t_plus_10)
    
    # Tick until T+10m
    # We need to advance time to T+10m.
    # Current implementation checks for "starting now" (last 60s).
    
    # Advance world time manually close to target
    world.current_time = t_plus_10 - datetime.timedelta(seconds=30)
    await engine.tick(60) # Crosses the threshold
    
    # Check events
    world_repo = WorldRepo(db_session)
    events = await world_repo.get_recent_events(world.id)
    start_events = [e for e in events if e.type == "calendar_start"]
    
    # Should have 2 start events
    assert len(start_events) == 2
    titles = [e.description for e in start_events]
    assert any("Event A" in t for t in titles)
    assert any("Event B" in t for t in titles)

@pytest.mark.asyncio
async def test_calendar_reminders_timing(db_session):
    engine = WorldEngine(db_session)
    world = await engine.get_or_create_world()
    agent_repo = AgentRepo(db_session)
    agent = await agent_repo.create_agent({"name": "RemindTest", "world_id": world.id})
    
    # Reminder is at T-15m.
    # Schedule for T+16m.
    target_time = world.current_time + datetime.timedelta(minutes=16)
    await engine.schedule_event(agent.id, "Future Event", target_time)
    
    # Tick 1 min. Time becomes T+1m.
    # Reminder check: (T+1m) + 15m = T+16m. Match.
    await engine.tick(60)
    
    world_repo = WorldRepo(db_session)
    events = await world_repo.get_recent_events(world.id)
    reminders = [e for e in events if e.type == "calendar_reminder"]
    
    assert len(reminders) == 1
    assert reminders[0].payload["minutes_remaining"] == 15
    
    # Tick again. Time becomes T+2m.
    # Reminder check: (T+2m) + 15m = T+17m. No match (Event is at T+16m).
    # Should NOT generate another 15m reminder.
    await engine.tick(60)
    
    events_new = await world_repo.get_recent_events(world.id)
    reminders_new = [e for e in events_new if e.type == "calendar_reminder"]
    # Should still be 1 total (from previous tick) if we fetch all, 
    # or 0 if we fetch only recent since last tick (but get_recent_events is limit based).
    # Since we limit=10, we see the old one.
    # But we want to ensure no NEW one was added.
    assert len(reminders_new) == 1 # Count didn't increase
