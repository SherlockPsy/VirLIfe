"""
Tests for Entity Persistence Manager

Implements PFEE_PLAN.md Phase P9 test requirements for entity persistence.
"""

import pytest
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from backend.pfee.entities import (
    EntityPersistenceManager, PersistenceLevel, EntityType
)


@pytest.mark.asyncio
async def test_repeated_encounters_promote_entities(session: AsyncSession):
    """Test that repeated encounters promote entities from Thin to Persistent."""
    manager = EntityPersistenceManager(session)
    
    # Create a thin entity
    entity = {
        "id": 1,
        "name": "Test Person",
        "salient_encounter_count": 0,
        "persistence_level": "ephemeral"
    }
    context = {}
    
    # First encounter - should be ephemeral
    level1 = await manager.classify_entity_persistence(
        entity, context, EntityType.PERSON
    )
    assert level1 == PersistenceLevel.EPHEMERAL
    
    # After multiple encounters - should promote
    entity["salient_encounter_count"] = 3
    level2 = await manager.classify_entity_persistence(
        entity, context, EntityType.PERSON
    )
    assert level2 == PersistenceLevel.PERSISTENT


@pytest.mark.asyncio
async def test_one_off_encounters_remain_thin(session: AsyncSession):
    """Test that one-off encounters remain Thin."""
    manager = EntityPersistenceManager(session)
    
    entity = {
        "id": 2,
        "name": "One-off Person",
        "salient_encounter_count": 1,
        "persistence_level": "ephemeral"
    }
    context = {}
    
    level = await manager.classify_entity_persistence(
        entity, context, EntityType.PERSON
    )
    assert level == PersistenceLevel.EPHEMERAL


@pytest.mark.asyncio
async def test_promotion_is_idempotent(session: AsyncSession):
    """Test that promotion is idempotent and deterministic."""
    manager = EntityPersistenceManager(session)
    
    entity_id = 3
    entity_type = EntityType.PERSON
    
    # First promotion
    result1 = await manager.promote_to_persistent(entity_id, entity_type)
    
    # Second promotion (should be idempotent)
    result2 = await manager.promote_to_persistent(entity_id, entity_type)
    
    assert result1 == result2 or result2 is True  # Idempotent


@pytest.mark.asyncio
async def test_core_person_is_persistent(session: AsyncSession):
    """Test that core persons (family, close friend) are Persistent."""
    manager = EntityPersistenceManager(session)
    
    entity = {
        "id": 4,
        "name": "Family Member",
        "relationship_type": "family"
    }
    context = {}
    
    level = await manager.classify_entity_persistence(
        entity, context, EntityType.PERSON
    )
    assert level == PersistenceLevel.PERSISTENT

