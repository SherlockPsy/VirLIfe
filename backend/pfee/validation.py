"""
PFEE Validation Result

Structured result for LLM output validation.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List

from backend.cognition.llm_wrapper import CognitionLLMResponse


OBJECT_KEYWORDS = ["uses", "picks up", "grabs", "takes", "holds", "opens", "wears"]
LOCATION_KEYWORDS = ["goes to", "moves to", "runs to", "drives to", "walks to", "enters"]
IMPOSSIBLE_ACTION_KEYWORDS = ["teleports", "time travels", "becomes invisible", "phase shifts"]
RELATIONSHIP_CONTRADICTION_PHRASES = ["never met", "don't know you", "stranger to me"]


@dataclass
class ValidationResult:
    """Result of LLM output validation against world state."""
    is_valid: bool
    reason: Optional[str] = None
    corrected_output: Optional[Dict[str, Any]] = None
    
    @classmethod
    def valid(cls) -> "ValidationResult":
        """Valid output."""
        return cls(is_valid=True)
    
    @classmethod
    def invalid(cls, reason: str, corrected_output: Optional[Dict[str, Any]] = None) -> "ValidationResult":
        """Invalid output."""
        return cls(is_valid=False, reason=reason, corrected_output=corrected_output or _default_fallback())


def _default_fallback() -> Dict[str, Any]:
    """Deterministic fallback that results in no action."""
    return {
        "utterance": None,
        "action": None,
        "stance_shifts": [],
        "intention_updates": []
    }


def _normalize_token(token: str) -> str:
    return token.strip().lower().strip(".,!?")


def _extract_keyword_target(text: str, keyword: str) -> Optional[str]:
    if keyword not in text:
        return None
    after = text.split(keyword, 1)[1].strip()
    if not after:
        return None
    return _normalize_token(after.split()[0])


def validate_llm_output_against_world(
    llm_output: Any,
    world_state: Dict[str, Any],
    context: Dict[str, Any]
) -> ValidationResult:
    """
    Validate LLM output against authoritative world state.
    
    Checks:
    - Agent presence (stance shifts & intention targets)
    - Object existence in the current location
    - Physical plausibility keywords (teleport/time travel)
    - Location consistency (movement requires explicit allowance)
    - Relationship contradictions (e.g., "never met" vs. high familiarity)
    """
    if not isinstance(llm_output, CognitionLLMResponse):
        return ValidationResult.invalid("invalid_output_type")
    
    agents_present_ids = [
        agent.get("id")
        for agent in world_state.get("persistent_agents_present_with_user", [])
        if agent.get("id") is not None
    ]
    objects_in_location = world_state.get("objects_in_location", [])
    object_names = {_normalize_token(obj.get("name", "")) for obj in objects_in_location if obj.get("name")}
    current_location = world_state.get("current_location", "")
    
    # 1. Agent presence checks
    for shift in llm_output.stance_shifts or []:
        target = getattr(shift, "target", "") or ""
        if target.startswith("agent:"):
            try:
                agent_id = int(target.split(":")[1])
            except (IndexError, ValueError):
                return ValidationResult.invalid(f"invalid_stance_shift_target: {target}")
            if agent_id not in agents_present_ids:
                return ValidationResult.invalid(f"stance_shift_target_not_present: {target}")
    
    for update in llm_output.intention_updates or []:
        target = getattr(update, "target", None)
        if target and target.startswith("agent:"):
            try:
                agent_id = int(target.split(":")[1])
            except (IndexError, ValueError):
                return ValidationResult.invalid(f"invalid_intention_update_target: {target}")
            if agent_id not in agents_present_ids:
                return ValidationResult.invalid(f"intention_update_target_not_present: {target}")
    
    action_lower = (llm_output.action or "").lower()
    
    # 2. Object existence checks
    for keyword in OBJECT_KEYWORDS:
        referenced = _extract_keyword_target(action_lower, keyword)
        if referenced and referenced not in object_names:
            return ValidationResult.invalid(
                f"action_references_nonexistent_object:{referenced}"
            )
    
    # 3. Physical plausibility
    for impossible in IMPOSSIBLE_ACTION_KEYWORDS:
        if impossible in action_lower:
            return ValidationResult.invalid(f"physically_impossible_action:{impossible}")
    
    # 4. Location consistency
    allow_location_change = context.get("allow_location_change", False)
    for keyword in LOCATION_KEYWORDS:
        if keyword in action_lower and not allow_location_change:
            destination = _extract_keyword_target(action_lower, keyword) or "unknown"
            if destination and destination not in (_normalize_token(current_location), "unknown"):
                return ValidationResult.invalid(f"location_transition_without_trigger:{destination}")
    
    # 5. Relationship contradictions
    utterance_lower = (llm_output.utterance or "").lower()
    numeric_relationships = context.get("_eligibility_numeric_state", {}).get("relationships", {})
    high_familiarity = any(
        rel.get("familiarity", 0) >= 0.7 or rel.get("warmth", 0) >= 0.6
        for rel in numeric_relationships.values()
    )
    if high_familiarity:
        for phrase in RELATIONSHIP_CONTRADICTION_PHRASES:
            if phrase in utterance_lower:
                return ValidationResult.invalid("relationship_contradiction_detected")
    
    return ValidationResult.valid()

