import pytest
import datetime
from backend.world.engine import WorldEngine
from backend.persistence.repo import WorldRepo, AgentRepo
from backend.persistence.models import LocationModel

@pytest.mark.asyncio
async def test_world_tick(db_session):
    engine = WorldEngine(db_session)
    world = await engine.get_or_create_world()
    initial_tick = world.current_tick
    initial_time = world.current_time
    
    # Tick
    await engine.tick(seconds=60)
    
    assert world.current_tick == initial_tick + 1
    assert world.current_time > initial_time
    assert (world.current_time - initial_time).total_seconds() == 60

@pytest.mark.asyncio
async def test_movement(db_session):
    engine = WorldEngine(db_session)
    world = await engine.get_or_create_world()
    
    # Create locations
    loc1 = LocationModel(name="Loc1", description="Loc1", world_id=world.id)
    loc2 = LocationModel(name="Loc2", description="Loc2", world_id=world.id)
    db_session.add_all([loc1, loc2])
    await db_session.flush()
    
    # Create agent
    agent_repo = AgentRepo(db_session)
    agent = await agent_repo.create_agent({
        "name": "Mover",
        "world_id": world.id,
        "location_id": loc1.id
    })
    
    # Move
    await engine.move_agent(agent.id, loc2.id)
    
    # Verify
    fetched_agent = await agent_repo.get_agent_by_id(agent.id)
    assert fetched_agent.location_id == loc2.id
    
    # Verify event
    world_repo = WorldRepo(db_session)
    events = await world_repo.get_recent_events(world.id)
    assert len(events) > 0
    assert events[0].type == "movement"
    assert events[0].payload["from"] == loc1.id
    assert events[0].payload["to"] == loc2.id

@pytest.mark.asyncio
async def test_calendar_events(db_session):
    engine = WorldEngine(db_session)
    world = await engine.get_or_create_world()
    
    # Create agent
    agent_repo = AgentRepo(db_session)
    agent = await agent_repo.create_agent({
        "name": "Planner",
        "world_id": world.id
    })
    
    # Schedule event starting in 16 mins (so after 1 min tick, it is 15 mins away)
    start_time = world.current_time + datetime.timedelta(minutes=16)
    await engine.schedule_event(agent.id, "Meeting", start_time)
    
    # Tick to trigger reminder
    # Tick advances time by 1 min. New time = T0 + 1m.
    # Reminder check: (T0 + 1m) + 15m = T0 + 16m.
    # Our event is at T0 + 16m. It should match.
    await engine.tick(seconds=60)
    
    # Check events
    world_repo = WorldRepo(db_session)
    events = await world_repo.get_recent_events(world.id)
    
    # We might need to filter for calendar_reminder
    reminder_events = [e for e in events if e.type == "calendar_reminder"]
    assert len(reminder_events) == 1
    assert "Meeting" in reminder_events[0].description

@pytest.mark.asyncio
async def test_incursion_generation(db_session):
    # This is probabilistic, so we might need to force it or mock random.
    # But for now, let's just verify the method exists and runs without error.
    engine = WorldEngine(db_session)
    world = await engine.get_or_create_world()
    
    await engine._generate_incursions(world)
    # No assertion on event creation since it's 1% chance, but ensures no crash.
