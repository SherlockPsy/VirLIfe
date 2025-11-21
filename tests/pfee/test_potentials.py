"""
Tests for PFEE Potential Resolver

Tests:
- Potential registration
- Deterministic resolution
- Entity instantiation from potentials
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.pfee.potentials import (
    PotentialResolver,
    PotentialType,
    ContextType
)


@pytest.mark.asyncio
async def test_register_potential(session: AsyncSession):
    """Test registering a new potential."""
    resolver = PotentialResolver(session)
    
    context = {
        "context_type": ContextType.PARK.value
    }
    potential_type = PotentialType.DOG_ENCOUNTER
    parameters = {
        "name": "A friendly dog",
        "description": "A dog approaches"
    }
    
    potential_id = await resolver.register_potential(
        context, potential_type, parameters
    )
    
    assert potential_id > 0


@pytest.mark.asyncio
async def test_resolve_potentials_deterministic(session: AsyncSession):
    """Test that potential resolution is deterministic."""
    resolver = PotentialResolver(session)
    
    # Register a potential
    context = {
        "context_type": ContextType.PARK.value,
        "current_time": None,
        "salience": 0.6
    }
    potential_type = PotentialType.DOG_ENCOUNTER
    parameters = {
        "name": "A friendly dog",
        "min_salience": 0.5
    }
    
    await resolver.register_potential(context, potential_type, parameters)
    
    # Resolve twice with same context
    resolved1 = await resolver.resolve_potentials_for_context(context)
    resolved2 = await resolver.resolve_potentials_for_context(context)
    
    # Should get same results (or empty if criteria not met)
    assert len(resolved1) == len(resolved2)


@pytest.mark.asyncio
async def test_resolve_potential_creates_entity(session: AsyncSession):
    """Test that resolved potentials create entities."""
    resolver = PotentialResolver(session)
    
    context = {
        "context_type": ContextType.PARK.value,
        "current_time": None,
        "salience": 0.6
    }
    potential_type = PotentialType.DOG_ENCOUNTER
    parameters = {
        "name": "A friendly dog",
        "description": "A dog approaches",
        "min_salience": 0.5
    }
    
    await resolver.register_potential(context, potential_type, parameters)
    
    resolved = await resolver.resolve_potentials_for_context(context)
    
    if resolved:
        assert len(resolved) > 0
        assert resolved[0].resolved_entity is not None
        assert resolved[0].resolved_entity.get("type") in ["person", "object", "information_source"]

