from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from backend.pfee.info_events import InformationEventManager, InfoEventType
from backend.persistence.models import InfoEventModel
from tests.pfee import factories


@pytest.mark.asyncio
async def test_information_event_persists_expected_fields(session):
    manager = InformationEventManager(session)
    event_id = await manager.create_info_event(
        event_type=InfoEventType.MESSAGE,
        content={"text": "Call me back"},
        sender_id=42,
        sender_type="agent",
        recipient_id=1,
        due_time=datetime(2025, 5, 1, 11, tzinfo=timezone.utc),
    )

    stored = (
        await session.execute(select(InfoEventModel).where(InfoEventModel.id == event_id))
    ).scalar_one()
    assert stored.type == InfoEventType.MESSAGE.value
    assert stored.content["text"] == "Call me back"
    assert stored.processed is False


@pytest.mark.asyncio
async def test_due_events_are_retrieved_and_marked_processed(session):
    manager = InformationEventManager(session)
    now = datetime(2025, 5, 1, 12, tzinfo=timezone.utc)

    due_event = await manager.create_info_event(
        event_type=InfoEventType.EMAIL,
        content={"subject": "Status update"},
        sender_id=7,
        sender_type="agent",
        recipient_id=1,
        due_time=now - timedelta(minutes=5),
    )
    await manager.create_info_event(
        event_type=InfoEventType.NOTIFICATION,
        content={"title": "Later"},
        sender_id=8,
        sender_type="system",
        recipient_id=1,
        due_time=now + timedelta(hours=1),
    )

    world_state = {"current_time": now}
    due_events = await manager.compute_due_information_events(world_state)

    assert len(due_events) == 1
    assert due_events[0].id == due_event

    await manager.mark_event_processed(due_event)
    await session.flush()

    repeat = await manager.compute_due_information_events(world_state)
    assert repeat == []

