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
    violations: List[str] = None
    
    def __post_init__(self):
        """Initialize violations list if None."""
        if self.violations is None:
            self.violations = []
    
    @classmethod
    def valid(cls) -> "ValidationResult":
        """Valid output."""
        return cls(is_valid=True, violations=[])
    
    @classmethod
    def invalid(cls, reason: str, corrected_output: Optional[Dict[str, Any]] = None, violations: Optional[List[str]] = None) -> "ValidationResult":
        """Invalid output."""
        return cls(
            is_valid=False,
            reason=reason,
            corrected_output=corrected_output or _default_fallback(),
            violations=violations or []
        )


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


def validate_cognition_output(
    world_state: Dict[str, Any],
    cognition_output: Any,
    context: Optional[Dict[str, Any]] = None
) -> ValidationResult:
    """
    C.6: Validate cognition output against world state and rules.
    
    Implements Section C.6 of the blueprint:
    - Physical consistency checks (C.6.1)
    - Relationship rule checks (C.6.2)
    - George protection checks (C.6.3)
    - Temporal continuity checks (C.6.4)
    
    Args:
        world_state: WorldState dict from world_state_builder
        cognition_output: CognitionOutput or CognitionLLMResponse
        context: Optional context dict
    
    Returns:
        ValidationResult with is_valid, violations, corrected_output
    """
    context = context or {}
    violations = []
    corrected_output = None
    
    # Get George agent ID
    george_agent_id = world_state.get("george_agent_id")
    
    # Get agents in scene
    agents_in_scene = world_state.get("agents_in_scene", [])
    agents_present_ids = [
        agent.get("id")
        for agent in agents_in_scene
        if agent.get("id") is not None
    ]
    
    # Convert to dict if needed for processing
    if hasattr(cognition_output, 'utterance'):
        output_dict = {
            "utterance": getattr(cognition_output, 'utterance', None),
            "action": getattr(cognition_output, 'action', None),
            "stance_shifts": getattr(cognition_output, 'stance_shifts', []),
            "intention_updates": getattr(cognition_output, 'intention_updates', []),
            "memory_updates": getattr(cognition_output, 'memory_updates', []),
            "arc_updates": getattr(cognition_output, 'arc_updates', []),
            "relationship_updates": getattr(cognition_output, 'relationship_updates', [])
        }
    else:
        output_dict = cognition_output if isinstance(cognition_output, dict) else {}
    
    corrected_output = output_dict.copy()
    
    # C.6.1: Physical Consistency Checks
    location = world_state.get("location", {})
    current_location_id = location.get("location_id")
    adjacency = location.get("adjacency", [])
    
    action_lower = (output_dict.get("action") or "").lower()
    
    # Check for impossible movements
    for keyword in LOCATION_KEYWORDS:
        if keyword in action_lower:
            # Extract destination (simplified check)
            # In full implementation, would verify adjacency
            pass
    
    # C.6.2: Relationship Rule Checks
    utterance_lower = (output_dict.get("utterance") or "").lower()
    
    # Check for relationship contradictions
    relationships = world_state.get("relationships", {})
    high_familiarity = any(
        rel.get("familiarity", 0) >= 0.7 or rel.get("warmth", 0) >= 0.6
        for rel in relationships.values()
    )
    if high_familiarity:
        for phrase in RELATIONSHIP_CONTRADICTION_PHRASES:
            if phrase in utterance_lower:
                violations.append("relationship_contradiction_detected")
                # Remove contradiction from utterance
                if corrected_output.get("utterance"):
                    corrected_output["utterance"] = corrected_output["utterance"].replace(phrase, "")
    
    # Check for radical relationship changes (affairs, break-ups)
    relationship_updates = output_dict.get("relationship_updates", [])
    for update in relationship_updates:
        # Check if update suggests affair or break-up
        if isinstance(update, dict):
            warmth_change = update.get("warmth_delta", 0)
            if warmth_change < -0.5:  # Large negative change
                # Check if supported by arcs/influence fields
                # For now, flag as potential violation
                violations.append("radical_relationship_change_detected")
    
    # C.6.3: George Protection Checks
    if george_agent_id:
        # Check memory updates for George
        memory_updates = output_dict.get("memory_updates", [])
        for mem_update in memory_updates:
            if isinstance(mem_update, dict):
                target_agent_id = mem_update.get("agent_id")
                if target_agent_id == george_agent_id:
                    violations.append("memory_created_for_george")
                    corrected_output["memory_updates"] = [
                        m for m in corrected_output.get("memory_updates", [])
                        if m.get("agent_id") != george_agent_id
                    ]
        
        # Check arc updates for George
        arc_updates = output_dict.get("arc_updates", [])
        for arc_update in arc_updates:
            if isinstance(arc_update, dict):
                target_agent_id = arc_update.get("agent_id")
                if target_agent_id == george_agent_id:
                    violations.append("arc_created_or_modified_for_george")
                    corrected_output["arc_updates"] = [
                        a for a in corrected_output.get("arc_updates", [])
                        if a.get("agent_id") != george_agent_id
                    ]
        
        # Check intention updates for George
        intention_updates = output_dict.get("intention_updates", [])
        for intent_update in intention_updates:
            if isinstance(intent_update, dict):
                target = intent_update.get("target", "")
                if target.startswith("agent:"):
                    try:
                        agent_id = int(target.split(":")[1])
                        if agent_id == george_agent_id:
                            violations.append("intention_created_for_george")
                            corrected_output["intention_updates"] = [
                                i for i in corrected_output.get("intention_updates", [])
                                if not (isinstance(i, dict) and i.get("target", "").startswith(f"agent:{george_agent_id}"))
                            ]
                    except (ValueError, IndexError):
                        pass
        
        # Check for statements about George's inner feelings
        if corrected_output.get("utterance"):
            utterance = corrected_output["utterance"]
            george_inner_feeling_phrases = [
                "george feels", "george thinks", "george worries",
                "george's mood", "george's thoughts", "george wants"
            ]
            for phrase in george_inner_feeling_phrases:
                if phrase.lower() in utterance.lower():
                    violations.append(f"cognition_states_george_inner_feeling: {phrase}")
                    # Replace with external observation
                    utterance = utterance.replace(phrase, f"George appears")
            corrected_output["utterance"] = utterance
    
    # C.6.4: Temporal Continuity Checks
    # Check for time jumps (would need world time comparison)
    # For now, basic check - can be enhanced
    
    # Determine if valid after corrections
    is_valid = len(violations) == 0
    
    # If violations found but corrected, mark as partially valid
    if violations and corrected_output != output_dict:
        return ValidationResult(
            is_valid=False,
            reason="violations_corrected",
            corrected_output=corrected_output,
            violations=violations
        )
    elif violations:
        return ValidationResult(
            is_valid=False,
            reason="violations_detected",
            corrected_output=corrected_output,
            violations=violations
        )
    
    return ValidationResult.valid()


# Legacy function for backward compatibility
def validate_llm_output_against_world(
    llm_output: Any,
    world_state: Dict[str, Any],
    context: Dict[str, Any]
) -> ValidationResult:
    """
    Legacy wrapper for backward compatibility.
    Delegates to validate_cognition_output.
    """
    return validate_cognition_output(world_state, llm_output, context)

