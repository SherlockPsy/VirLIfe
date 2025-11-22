"""
F.4 TEST_PFEE_COGNITION_CYCLE

Purpose: Test that PFEE orchestrator runs a complete cycle from world_state → cognition → validation → integration.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.pfee.world_state_builder import build_world_state
from backend.pfee.cognition_input_builder import build_cognition_input
from backend.pfee.validation import validate_cognition_output


class TestPFEECognitionCycle:
    """F.4: Test PFEE cognition cycle"""
    
    @pytest.mark.asyncio
    async def test_user_triggered_cycle(
        self, test_session: AsyncSession, seeded_world: dict
    ):
        """F.4.1: Test user-triggered PFEE cycle"""
        world_id = seeded_world["world_id"]
        george_id = seeded_world["george_agent_id"]
        
        world_state = await build_world_state(
            test_session,
            world_id=world_id
        )
        world_state["george_agent_id"] = george_id
        
        # Simulate user action
        trigger = {
            "trigger_type": "user_action",
            "actor_agent_id": george_id,
            "user_input": "Hello"
        }
        
        cognition_input = await build_cognition_input(
            test_session,
            world_state=world_state,
            trigger=trigger
        )
        
        # F.4.1: Vantage should not be George
        assert cognition_input.vantage_agent_id != george_id
        assert cognition_input.vantage_agent_id is not None
        
        # Check no internal George data
        input_text = str(cognition_input)
        assert "george's mood" not in input_text.lower()
        assert "george feels" not in input_text.lower()
    
    @pytest.mark.asyncio
    async def test_cognition_output_validation_removes_illegal_updates(
        self, test_session: AsyncSession, seeded_world: dict
    ):
        """F.4.3: Test validation removes illegal George updates"""
        world_id = seeded_world["world_id"]
        george_id = seeded_world["george_agent_id"]
        
        world_state = await build_world_state(
            test_session,
            world_id=world_id
        )
        world_state["george_agent_id"] = george_id
        
        # Create illegal output
        illegal_output = {
            "memories": [{"agent_id": george_id, "content": "Test"}],
            "mood": {str(george_id): {"valence": 0.5}}
        }
        
        validation_result = await validate_cognition_output(
            test_session,
            world_state=world_state,
            cognition_output=illegal_output
        )
        
        # Should be invalid or partially valid
        assert not validation_result.is_valid or validation_result.partially_valid
        
        # Illegal parts should be removed
        corrected = validation_result.corrected_output
        if "memories" in corrected:
            george_mems = [m for m in corrected["memories"] if m.get("agent_id") == george_id]
            assert len(george_mems) == 0

