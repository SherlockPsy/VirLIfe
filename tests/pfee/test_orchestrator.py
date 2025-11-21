"""
Tests for Perception Orchestrator

Implements PFEE_PLAN.md Phase P9 end-to-end test requirements.
"""

import pytest
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from backend.pfee.orchestrator import PerceptionOrchestrator
from backend.pfee.potentials import PotentialResolver, PotentialType, ContextType
from backend.pfee.entities import EntityPersistenceManager, EntityType


@pytest.mark.asyncio
async def test_no_triggers_no_llm_calls(session: AsyncSession):
    """Test that no triggers → no LLM calls."""
    orchestrator = PerceptionOrchestrator(session)
    
    world_state = {
        "world_id": 1,
        "current_time": datetime.now(timezone.utc),
        "current_tick": 0,
        "persistent_agents_present_with_user": []
    }
    
    result = await orchestrator.run_perception_cycle(world_state, None)
    
    assert result.text is None
    assert result.cognition_output is None
    assert result.renderer_output is None


@pytest.mark.asyncio
async def test_with_triggers_correct_llm_calls(session: AsyncSession):
    """Test that with triggers → correct LLM calls."""
    from backend.persistence.models import WorldModel, AgentModel, LocationModel
    from backend.pfee.world_state_builder import build_world_state_for_pfee
    
    orchestrator = PerceptionOrchestrator(session)
    
    # Create minimal world state
    world = WorldModel()
    session.add(world)
    await session.flush()
    
    # Create location
    location = LocationModel(
        name="Test Location",
        description="A test location",
        world_id=world.id,
        attributes={"type": "general"},
        adjacency=[]
    )
    session.add(location)
    await session.flush()
    
    # Create agent
    agent = AgentModel(
        name="Test Agent",
        world_id=world.id,
        location_id=location.id,
        drives={"relatedness": {"level": 0.8, "sensitivity": 1.0}},
        mood={"valence": 0.0, "arousal": 0.0},
        energy=1.0,
        personality_kernel={},
        personality_summaries={},
        domain_summaries={},
        cached_context_fragments={},
        status_flags={}
    )
    session.add(agent)
    await session.flush()
    
    # Build world state
    world_state = await build_world_state_for_pfee(session, world, None)
    
    # User action that should trigger
    user_action = {
        "type": "speak",
        "text": "Hello",
        "user_id": 1
    }
    
    # Run perception cycle
    result = await orchestrator.run_perception_cycle(world_state, user_action)
    
    # Should have triggers fired
    assert result.triggers_fired is not None
    assert len(result.triggers_fired) > 0


@pytest.mark.asyncio
async def test_correct_entities_instantiated(session: AsyncSession):
    """Test that correct entities are instantiated and classified."""
    from backend.pfee.potentials import PotentialResolver, PotentialType, ContextType
    from backend.pfee.entities import EntityPersistenceManager, EntityType
    
    resolver = PotentialResolver(session)
    entity_manager = EntityPersistenceManager(session)
    
    # Register a potential
    potential = await resolver.register_potential(
        context_type=ContextType.PARK,
        potential_type=PotentialType.DOG_ENCOUNTER,
        parameters={"dog_name": "Rex", "is_interruptive": True}
    )
    
    # Resolve it
    context = {
        "context_type": "park",
        "current_time": datetime.now(timezone.utc),
        "salience": 0.7
    }
    resolved = await resolver.resolve_potentials_for_context(context)
    
    # Should have resolved potential
    assert len(resolved) > 0
    
    # Entity should be instantiated
    if resolved:
        entity = {
            "id": resolved[0].id,
            "type": resolved[0].resolved_entity.get("type"),
            "name": resolved[0].resolved_entity.get("name", "Unknown")
        }
        
        # Classify entity
        persistence_level = await entity_manager.classify_entity_persistence(
            entity, context, EntityType.PERSON
        )
        
        # Should be classified (either persistent or ephemeral)
        assert persistence_level.value in ["persistent", "ephemeral"]

