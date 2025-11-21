from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from backend.pfee.potentials import (
    PotentialResolver,
    PotentialType,
)
from backend.persistence.models import PotentialModel


@pytest.mark.asyncio
async def test_potentials_below_threshold_remain_unresolved(session):
    resolver = PotentialResolver(session)
    await resolver.register_potential(
        context={"context_type": "general"},
        potential_type=PotentialType.DOG_ENCOUNTER,
        parameters={"min_salience": 0.9},
    )

    resolved = await resolver.resolve_potentials_for_context(
        {"context_type": "general", "salience": 0.2}
    )

    assert resolved == []
    stored = (await session.execute(select(PotentialModel))).scalars().all()
    assert stored[0].is_resolved is False


@pytest.mark.asyncio
async def test_potentials_meeting_criteria_resolve_once(session):
    resolver = PotentialResolver(session)
    potential_id = await resolver.register_potential(
        context={"context_type": "park"},
        potential_type=PotentialType.CLIENT_MESSAGE,
        parameters={"min_salience": 0.1},
    )

    context = {"context_type": "park", "salience": 0.5}
    first_run = await resolver.resolve_potentials_for_context(context)
    second_run = await resolver.resolve_potentials_for_context(context)

    assert len(first_run) == 1
    assert first_run[0].id == potential_id
    assert first_run[0].resolved_entity["type"] == "information_source"
    assert second_run == []

    potential = (
        await session.execute(
            select(PotentialModel).where(PotentialModel.id == potential_id)
        )
    ).scalar_one()
    assert potential.is_resolved is True
    assert potential.resolved_at is not None


@pytest.mark.asyncio
async def test_future_scheduled_potentials_wait_until_due(session):
    resolver = PotentialResolver(session)
    await resolver.register_potential(
        context={"context_type": "cafe"},
        potential_type=PotentialType.DELIVERY,
        parameters={"time_constraints": {"allowed_hours": [18]}},
    )

    morning_context = {
        "context_type": "cafe",
        "salience": 0.6,
        "current_time": datetime(2025, 5, 1, 9, tzinfo=timezone.utc),
    }
    evening_context = {
        "context_type": "cafe",
        "salience": 0.6,
        "current_time": datetime(2025, 5, 1, 18, tzinfo=timezone.utc),
    }

    early_resolution = await resolver.resolve_potentials_for_context(morning_context)
    assert early_resolution == []

    later_resolution = await resolver.resolve_potentials_for_context(evening_context)
    assert len(later_resolution) == 1

