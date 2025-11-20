"""
Phase 7 - Gateway API Tests

Tests for the three main endpoints:
- POST /user/action
- POST /world/advance
- GET /render
"""

import pytest
from backend.main import app


@pytest.mark.asyncio
async def test_user_action_required_fields():
    """Test /user/action requires user_id and action_type."""
    from backend.gateway.models import UserActionRequest

    # Valid request
    valid = UserActionRequest(user_id=1, action_type="speak")
    assert valid.user_id == 1
    assert valid.action_type == "speak"

    # Test with pytest.raises for invalid
    with pytest.raises(Exception):
        UserActionRequest(action_type="speak")  # Missing user_id


@pytest.mark.asyncio
async def test_world_advance_default_ticks():
    """Test /world/advance defaults to 1 tick."""
    from backend.gateway.models import WorldAdvanceRequest

    request = WorldAdvanceRequest()
    assert request.ticks == 1

    request_custom = WorldAdvanceRequest(ticks=5)
    assert request_custom.ticks == 5


@pytest.mark.asyncio
async def test_render_default_pov():
    """Test /render defaults to second_person POV."""
    from backend.gateway.models import RenderRequest

    request = RenderRequest(user_id=1)
    assert request.pov == "second_person"

    request_custom = RenderRequest(user_id=1, pov="omniscient")
    assert request_custom.pov == "omniscient"


@pytest.mark.asyncio
async def test_endpoint_exists():
    """Verify all required endpoints are registered."""
    endpoints = {}
    for route in app.routes:
        endpoints[route.path] = route.methods

    assert "/user/action" in endpoints
    assert "/world/advance" in endpoints
    assert "/render" in endpoints
    assert "/status" in endpoints
    assert "POST" in endpoints["/user/action"]
    assert "POST" in endpoints["/world/advance"]
    assert "GET" in endpoints["/render"]
    assert "GET" in endpoints["/status"]
