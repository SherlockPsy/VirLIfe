import pytest
from sqlalchemy import select

from backend.pfee.logging import PFEELogger
from backend.persistence.models import PFEELogModel


@pytest.mark.asyncio
async def test_cycle_logging_contains_required_metadata(session):
    logger = PFEELogger(session)
    logger.start_perception_cycle("cycle-1")
    logger.log_trigger_firing("user_action", metadata={"action_type": "speak"})
    logger.log_perception_cycle(
        triggers=[{"reason": "user_action"}],
        resolved_potentials=[],
        entities=[],
        cognition_output={"utterance": "Hello"},
        renderer_output={"text": "Rendered."},
    )
    await session.flush()

    logs = (
        await session.execute(select(PFEELogModel).where(PFEELogModel.log_type == "cycle"))
    ).scalars().all()
    assert len(logs) == 1
    metadata = logs[0].log_metadata
    assert metadata["triggers"] == [{"reason": "user_action"}]
    assert metadata["cognition_called"] is True
    assert metadata["renderer_called"] is True


@pytest.mark.asyncio
async def test_error_logging_captures_stack_information(session):
    logger = PFEELogger(session)
    logger.start_perception_cycle("cycle-err")

    try:
        raise ValueError("boom")
    except ValueError as exc:
        logger.log_error("PerceptionOrchestrator", "test_error", "failure", exc)

    await session.flush()
    error_log = (
        await session.execute(select(PFEELogModel).where(PFEELogModel.log_type == "error"))
    ).scalar_one()

    assert error_log.log_metadata["error_type"] == "test_error"
    assert error_log.log_metadata["exception_type"] == "ValueError"
    assert error_log.log_metadata["exception_message"] == "boom"

