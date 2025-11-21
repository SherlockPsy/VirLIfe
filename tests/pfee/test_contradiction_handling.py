"""
Tests for PFEE Contradiction Handling

Tests:
- LLM output validation against world state
- Contradiction detection
- Rejection of impossible outputs
- Deterministic handling of contradictions
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from backend.cognition.llm_wrapper import (
    CognitionLLMResponse,
    StanceShiftOutput,
    IntentionUpdateOutput
)
from backend.pfee.orchestrator import PerceptionOrchestrator
from backend.pfee.validation import ValidationResult


@pytest.mark.asyncio
async def test_validate_stance_shift_target_not_present(session: AsyncSession):
    """Test that stance shifts to non-existent agents are rejected."""
    orchestrator = PerceptionOrchestrator(session)
    
    # Create LLM output with invalid target
    llm_output = CognitionLLMResponse(
        utterance="Hello",
        action=None,
        stance_shifts=[
            StanceShiftOutput(target="agent:999", description="feels closer")  # Agent 999 doesn't exist
        ],
        intention_updates=[]
    )
    
    world_state = {
        "persistent_agents_present_with_user": [
            {"id": 1, "name": "Rebecca"}
        ],
        "current_location_id": 1
    }
    
    context = {}
    
    result = await orchestrator._validate_llm_output_against_world(
        llm_output, world_state, context
    )
    
    assert isinstance(result, ValidationResult)
    assert not result.is_valid
    assert "not_present" in result.reason or "invalid" in result.reason


@pytest.mark.asyncio
async def test_validate_intention_update_target_not_present(session: AsyncSession):
    """Test that intention updates to non-existent agents are rejected."""
    orchestrator = PerceptionOrchestrator(session)
    
    llm_output = CognitionLLMResponse(
        utterance=None,
        action=None,
        stance_shifts=[],
        intention_updates=[
            IntentionUpdateOutput(
                operation="create",
                type="be_supportive",
                target="agent:999",  # Non-existent
                horizon="short",
                description="Be supportive to agent 999"
            )
        ]
    )
    
    world_state = {
        "persistent_agents_present_with_user": [
            {"id": 1, "name": "Rebecca"}
        ],
        "current_location_id": 1
    }
    
    context = {}
    
    result = await orchestrator._validate_llm_output_against_world(
        llm_output, world_state, context
    )
    
    assert isinstance(result, ValidationResult)
    assert not result.is_valid
    assert "not_present" in result.reason or "invalid" in result.reason


@pytest.mark.asyncio
async def test_validate_valid_output_accepted(session: AsyncSession):
    """Test that valid outputs are accepted."""
    orchestrator = PerceptionOrchestrator(session)
    
    llm_output = CognitionLLMResponse(
        utterance="Hello there",
        action=None,
        stance_shifts=[
            StanceShiftOutput(target="agent:1", description="feels closer")  # Valid agent
        ],
        intention_updates=[]
    )
    
    world_state = {
        "persistent_agents_present_with_user": [
            {"id": 1, "name": "Rebecca"}
        ],
        "current_location_id": 1
    }
    
    context = {}
    
    result = await orchestrator._validate_llm_output_against_world(
        llm_output, world_state, context
    )
    
    assert isinstance(result, ValidationResult)
    assert result.is_valid


@pytest.mark.asyncio
async def test_validate_object_existence(session: AsyncSession):
    """Test that actions referencing non-existent objects are rejected."""
    orchestrator = PerceptionOrchestrator(session)
    
    llm_output = CognitionLLMResponse(
        utterance=None,
        action="picks up the magic wand",  # Object doesn't exist
        stance_shifts=[],
        intention_updates=[]
    )
    
    world_state = {
        "persistent_agents_present_with_user": [
            {"id": 1, "name": "Rebecca"}
        ],
        "current_location_id": 1,
        "objects_in_location": [
            {"name": "book", "id": 1}
        ]
    }
    
    context = {}
    
    result = await orchestrator._validate_llm_output_against_world(
        llm_output, world_state, context
    )
    
    assert isinstance(result, ValidationResult)
    assert not result.is_valid
    assert "object" in (result.reason or "")


@pytest.mark.asyncio
async def test_validate_location_consistency(session: AsyncSession):
    """Test that location-changing actions are validated."""
    orchestrator = PerceptionOrchestrator(session)
    
    llm_output = CognitionLLMResponse(
        utterance=None,
        action="goes to the park",  # Location change
        stance_shifts=[],
        intention_updates=[]
    )
    
    world_state = {
        "persistent_agents_present_with_user": [
            {"id": 1, "name": "Rebecca"}
        ],
        "current_location_id": 1,
        "current_location": "home"
    }
    
    context = {}
    
    result = await orchestrator._validate_llm_output_against_world(
        llm_output, world_state, context
    )
    
    assert isinstance(result, ValidationResult)
    assert not result.is_valid
    assert "location" in (result.reason or "")


@pytest.mark.asyncio
async def test_validate_relationship_contradiction(session: AsyncSession):
    """Contradictions with high-familiarity relationships are rejected."""
    orchestrator = PerceptionOrchestrator(session)
    
    llm_output = CognitionLLMResponse(
        utterance="We have never met before.",
        action=None,
        stance_shifts=[],
        intention_updates=[]
    )
    
    world_state = {
        "persistent_agents_present_with_user": [
            {"id": 1, "name": "Rebecca"}
        ],
        "current_location_id": 1
    }
    
    context = {
        "_eligibility_numeric_state": {
            "relationships": {
                "agent:1": {"familiarity": 0.92, "warmth": 0.75}
            }
        }
    }
    
    result = await orchestrator._validate_llm_output_against_world(
        llm_output, world_state, context
    )
    
    assert isinstance(result, ValidationResult)
    assert not result.is_valid
    assert "relationship" in (result.reason or "")


@pytest.mark.asyncio
async def test_validate_physical_impossibility(session: AsyncSession):
    """Impossible physics actions are rejected deterministically."""
    orchestrator = PerceptionOrchestrator(session)
    
    llm_output = CognitionLLMResponse(
        utterance=None,
        action="teleports across the city",
        stance_shifts=[],
        intention_updates=[]
    )
    
    world_state = {
        "persistent_agents_present_with_user": [
            {"id": 1, "name": "Rebecca"}
        ],
        "current_location_id": 1
    }
    
    context = {}
    
    result = await orchestrator._validate_llm_output_against_world(
        llm_output, world_state, context
    )
    
    assert isinstance(result, ValidationResult)
    assert not result.is_valid
    assert "physically_impossible" in (result.reason or "")
    assert result.corrected_output is not None

