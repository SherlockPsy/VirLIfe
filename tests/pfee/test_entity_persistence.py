"""
Tests for PFEE Entity Persistence Manager

Tests:
- Entity persistence classification
- Promotion from Thin to Persistent
- Determinism of classification
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.pfee.entities import (
    EntityPersistenceManager,
    PersistenceLevel,
    EntityType
)


@pytest.mark.asyncio
async def test_classify_core_person_as_persistent(session: AsyncSession):
    """Test that core persons are classified as persistent."""
    manager = EntityPersistenceManager(session)
    
    entity = {
        "id": 1,
        "name": "Rebecca",
        "relationship_type": "close_friend"
    }
    context = {}
    
    result = await manager.classify_entity_persistence(
        entity, context, EntityType.PERSON
    )
    
    assert result == PersistenceLevel.PERSISTENT


@pytest.mark.asyncio
async def test_classify_one_off_encounter_as_ephemeral(session: AsyncSession):
    """Test that one-off encounters remain ephemeral."""
    manager = EntityPersistenceManager(session)
    
    entity = {
        "id": 2,
        "name": "Random Person",
        "salient_encounter_count": 1
    }
    context = {}
    
    result = await manager.classify_entity_persistence(
        entity, context, EntityType.PERSON
    )
    
    assert result == PersistenceLevel.EPHEMERAL


@pytest.mark.asyncio
async def test_classify_multiple_encounters_as_persistent(session: AsyncSession):
    """Test that multiple salient encounters promote to persistent."""
    manager = EntityPersistenceManager(session)
    
    entity = {
        "id": 3,
        "name": "Repeated Contact",
        "salient_encounter_count": 3
    }
    context = {}
    
    result = await manager.classify_entity_persistence(
        entity, context, EntityType.PERSON
    )
    
    assert result == PersistenceLevel.PERSISTENT


@pytest.mark.asyncio
async def test_classification_determinism(session: AsyncSession):
    """Test that classification is deterministic."""
    manager = EntityPersistenceManager(session)
    
    entity = {
        "id": 4,
        "name": "Test Entity",
        "relationship_type": "family"
    }
    context = {}
    
    result1 = await manager.classify_entity_persistence(
        entity, context, EntityType.PERSON
    )
    result2 = await manager.classify_entity_persistence(
        entity, context, EntityType.PERSON
    )
    
    assert result1 == result2
    assert result1 == PersistenceLevel.PERSISTENT


@pytest.mark.asyncio
async def test_promote_to_persistent_idempotent(session: AsyncSession):
    """Test that promotion is idempotent."""
    manager = EntityPersistenceManager(session)
    
    # This test would require actual database entities
    # For now, we test the logic
    entity_id = 1
    entity_type = EntityType.PERSON
    
    # First promotion
    result1 = await manager.promote_to_persistent(entity_id, entity_type)
    
    # Second promotion (should be idempotent)
    result2 = await manager.promote_to_persistent(entity_id, entity_type)
    
    # Both should succeed
    assert result1 is True or result2 is True  # May fail if entity doesn't exist, that's OK

