import pytest

from backend.cognition.llm_wrapper import CognitionLLMResponse
from backend.pfee.validation import validate_llm_output_against_world


def _base_world_state():
    return {
        "persistent_agents_present_with_user": [{"id": 200, "name": "Ava"}],
        "objects_in_location": [{"id": 1, "name": "ceramic mug"}],
        "current_location": "Loft",
    }


def test_missing_object_reference_causes_validation_failure():
    world_state = _base_world_state()
    context = {}
    llm_output = CognitionLLMResponse(
        utterance="She looks for a weapon.",
        action="She grabs the crystal sword from the table.",
    )

    result = validate_llm_output_against_world(llm_output, world_state, context)

    assert result.is_valid is False
    assert "action_references_nonexistent_object" in (result.reason or "")


def test_physically_impossible_action_rejected():
    world_state = _base_world_state()
    context = {"allow_location_change": False}
    llm_output = CognitionLLMResponse(
        utterance="She claims she can do the impossible.",
        action="She teleports through the apartment wall.",
    )

    result = validate_llm_output_against_world(llm_output, world_state, context)

    assert result.is_valid is False
    assert "physically_impossible_action" in (result.reason or "")


def test_relationship_contradiction_flagged():
    world_state = _base_world_state()
    context = {
        "_eligibility_numeric_state": {
            "relationships": {
                "agent:200": {
                    "warmth": 0.9,
                    "trust": 0.85,
                    "tension": 0.1,
                    "attraction": 0.3,
                    "familiarity": 0.95,
                    "comfort": 0.8,
                }
            }
        }
    }
    llm_output = CognitionLLMResponse(
        utterance="I never met you before, stranger.",
        action="She shrugs.",
    )

    result = validate_llm_output_against_world(llm_output, world_state, context)

    assert result.is_valid is False
    assert result.reason == "relationship_contradiction_detected"

