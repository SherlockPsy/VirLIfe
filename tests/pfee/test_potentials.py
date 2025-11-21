"""
Tests for Potential Resolver

Implements PFEE_PLAN.md Phase P9 test requirements for potentials.
"""

import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from backend.pfee.potentials import (
    PotentialResolver, PotentialType, ContextType
)


@pytest.mark.asyncio
async def test_potentials_are_deterministic(session: AsyncSession):
    """Test that potentials are deterministic given same inputs."""
    resolver = PotentialResolver(session)
    
    # Register a potential
    potential = await resolver.register_potential(
        context_type=ContextType.PARK,
        potential_type=PotentialType.DOG_ENCOUNTER,
        parameters={"dog_name": "Rex", "behavior": "approaching"}
    )
    
    # Resolve with same context twice
    context1 = {
        "context_type": "park",
        "current_time": datetime.now(timezone.utc),
        "salience": 0.7
    }
    context2 = {
        "context_type": "park",
        "current_time": context1["current_time"],
        "salience": 0.7
    }
    
    resolved1 = await resolver.resolve_potentials_for_context(context1)
    resolved2 = await resolver.resolve_potentials_for_context(context2)
    
    # Should produce same results (deterministic)
    assert len(resolved1) == len(resolved2)


@pytest.mark.asyncio
async def test_potential_resolution_criteria(session: AsyncSession):
    """Test that potentials only resolve when criteria are met."""
    resolver = PotentialResolver(session)
    
    # Register potential with time window
    now = datetime.now(timezone.utc)
    await resolver.register_potential(
        context_type=ContextType.PARK,
        potential_type=PotentialType.DOG_ENCOUNTER,
        parameters={
            "time_window": {
                "start": now - timedelta(hours=1),
                "end": now + timedelta(hours=1)
            },
            "salience_threshold": 0.5
        }
    )
    
    # Context with low salience - should not resolve
    context_low = {
        "context_type": "park",
        "current_time": now,
        "salience": 0.3
    }
    resolved_low = await resolver.resolve_potentials_for_context(context_low)
    assert len(resolved_low) == 0
    
    # Context with high salience - should resolve
    context_high = {
        "context_type": "park",
        "current_time": now,
        "salience": 0.7
    }
    resolved_high = await resolver.resolve_potentials_for_context(context_high)
    assert len(resolved_high) > 0

