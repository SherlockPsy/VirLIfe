import pytest
from backend.persistence.repo import AgentRepo, WorldRepo, UserRepo
from backend.persistence.models import AgentModel, LocationModel

@pytest.mark.asyncio
async def test_create_world_and_location(db_session):
    world_repo = WorldRepo(db_session)
    world = await world_repo.create_world()
    assert world.id is not None
    assert world.current_tick == 0

    # Create location manually since we don't have a LocationRepo yet (it's simple enough to add to WorldRepo or just use session)
    location = LocationModel(
        name="Living Room",
        description="A cozy living room.",
        world_id=world.id,
        attributes={"type": "indoor"}
    )
    db_session.add(location)
    await db_session.flush()
    
    assert location.id is not None
    
    # Test retrieval
    fetched_world = await world_repo.get_world(world.id)
    assert len(fetched_world.locations) == 1
    assert fetched_world.locations[0].name == "Living Room"

@pytest.mark.asyncio
async def test_create_agent_full_schema(db_session):
    world_repo = WorldRepo(db_session)
    world = await world_repo.create_world()
    
    location = LocationModel(name="Kitchen", description="A kitchen", world_id=world.id)
    db_session.add(location)
    await db_session.flush()

    agent_repo = AgentRepo(db_session)
    agent_data = {
        "name": "Rebecca",
        "world_id": world.id,
        "location_id": location.id,
        "energy": 0.8,
        "mood": {"valence": 0.5, "arousal": 0.2},
        "drives": {
            "relatedness": {"level": 0.6, "sensitivity": 1.0},
            "autonomy": {"level": 0.7, "sensitivity": 0.9}
        },
        "personality_kernel": {
            "sociability": 0.8,
            "openness": 0.9
        },
        "personality_summaries": {
            "stable": "A friendly AI.",
            "domain": {}
        },
        "status_flags": {"is_busy": False}
    }
    
    agent = await agent_repo.create_agent(agent_data)
    assert agent.id is not None
    assert agent.mood["valence"] == 0.5
    assert agent.drives["relatedness"]["level"] == 0.6
    
    # Test retrieval
    fetched_agent = await agent_repo.get_agent_by_id(agent.id)
    assert fetched_agent.name == "Rebecca"
    assert fetched_agent.location.name == "Kitchen"
    assert fetched_agent.personality_kernel["sociability"] == 0.8

@pytest.mark.asyncio
async def test_relationships_and_memories(db_session):
    world_repo = WorldRepo(db_session)
    world = await world_repo.create_world()
    agent_repo = AgentRepo(db_session)
    user_repo = UserRepo(db_session)
    
    # Create Agent
    agent = await agent_repo.create_agent({"name": "Rebecca", "world_id": world.id})
    
    # Create User
    user = await user_repo.create_user("George")
    assert user.id is not None
    
    # Create Relationship (Agent -> User)
    # Note: We need to handle the target_user_id manually in the repo or model creation
    from backend.persistence.models import RelationshipModel
    rel = RelationshipModel(
        source_agent_id=agent.id,
        target_user_id=user.id,
        warmth=0.5,
        trust=0.8
    )
    db_session.add(rel)
    await db_session.flush()
    
    rels = await agent_repo.get_relationships(agent.id)
    assert len(rels) == 1
    assert rels[0].target_user_id == user.id
    assert rels[0].trust == 0.8
    
    # Add Memory
    memory = await agent_repo.add_memory(agent.id, {
        "type": "episodic",
        "description": "Met George.",
        "salience": 0.9,
        "semantic_tags": ["meeting", "george"]
    })
    
    assert memory.id is not None
    
    # Verify agent has memory
    fetched_agent = await agent_repo.get_agent_by_id(agent.id)
    assert len(fetched_agent.memories) == 1
    assert fetched_agent.memories[0].description == "Met George."

@pytest.mark.asyncio
async def test_user_non_simulation(db_session):
    """
    Verify that the User model does NOT have psychological fields.
    """
    user_repo = UserRepo(db_session)
    user = await user_repo.create_user("TestUser")
    
    # Check that attributes do not exist
    assert not hasattr(user, "mood")
    assert not hasattr(user, "drives")
    assert not hasattr(user, "personality_kernel")
    assert not hasattr(user, "arcs")
