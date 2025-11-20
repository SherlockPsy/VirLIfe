"""
LLM Cognition Wrapper Module

Handles calls to the reasoning LLM for cognition, with strict schema validation.
Per cognition_flow.md §5 and MASTER_SPEC.

"Cognition LLM is called with CognitionContext(A, E) and MUST respond with structured data.

LLM MUST NOT output numeric values.
LLM MUST NOT talk about 'setting trust to X' or similar.
LLM MUST NOT redefine stable personality in one step; any long-term change MUST be mediated by deterministic mapping."
"""

import re
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum


class CognitionLLMModel(Enum):
    """LLM models for cognition (reasoning, not adult)."""
    CLAUDE_3_7_SONNET_REASONING = "claude-3-7-sonnet-20250219"
    CLAUDE_3_7_SONNET = "claude-3-7-sonnet-20250219"
    # Extended thinking model (preferred for reasoning)
    CLAUDE_3_OPUS = "claude-3-opus-20250514"


@dataclass
class StanceShiftOutput:
    """Single stance shift from LLM output."""
    target: str              # person_id or agent name
    description: str         # "gives benefit of doubt", "escalates distrust", etc.


@dataclass
class IntentionUpdateOutput:
    """Single intention update from LLM output."""
    operation: str           # "create", "boost", "lower", "drop"
    type: str                # "avoid", "raise", "support", "protect", "distance"
    target: Optional[str] = None  # person_id, topic, or null
    horizon: str = "medium"  # "short", "medium", "long"
    description: str = ""    # Textual description of the intention


@dataclass
class CognitionLLMResponse:
    """Parsed and validated LLM response for cognition."""
    utterance: Optional[str] = None      # What the agent says now
    action: Optional[str] = None         # What the agent does now
    stance_shifts: List[StanceShiftOutput] = field(default_factory=list)
    intention_updates: List[IntentionUpdateOutput] = field(default_factory=list)
    
    # Metadata for validation
    is_valid: bool = True
    validation_errors: List[str] = field(default_factory=list)


class LLMResponseValidator:
    """
    Validates LLM responses for cognition.
    
    Per cognition_flow.md §5:
    "LLM MUST NOT output numeric values.
    LLM MUST NOT talk about 'setting trust to X' or similar.
    LLM MUST NOT redefine stable personality in one step."
    """
    
    # Regex patterns for forbidden numeric content
    NUMERIC_PATTERN = re.compile(r'\b\d+(?:\.\d+)?\b')  # Any number
    NUMERIC_STATE_PATTERN = re.compile(
        r'(?:set|adjust|change|modify|update)\s+(?:(?:her|his|their)\s+)?(?:trust|warmth|tension|drive|energy|arousal|valence|mood)\s+to\s+(?:a\s+)?[\d.]+',
        re.IGNORECASE
    )  # "set trust to 0.8" or "set her trust to 0.8"
    PERSONALITY_REDEFINITION_PATTERN = re.compile(
        r'(?:she|he|they)?(?:is|are)?\s+now\s+(?:a|an)?\s*(?:completely|totally|entirely)?\s*(?:different|new)\s+person',
        re.IGNORECASE
    )  # "is now a completely different person"
    
    @staticmethod
    def validate_no_numeric_values(text: str) -> Optional[str]:
        """
        Check that response doesn't contain numeric state setting.
        
        Args:
            text: Text to validate
        
        Returns:
            Error message if forbidden, None if OK
        """
        if not text:
            return None
        
        # Check for "set X to N" pattern
        if LLMResponseValidator.NUMERIC_STATE_PATTERN.search(text):
            return "Response contains numeric state assignment (forbidden)"
        
        # Note: We allow numbers in general context ("at 2pm", "group of 3"),
        # but reject mathematical assignments to psychology
        
        return None
    
    @staticmethod
    def validate_no_personality_redefinition(text: str) -> Optional[str]:
        """
        Check that response doesn't redefine personality in one step.
        
        Args:
            text: Text to validate
        
        Returns:
            Error message if forbidden, None if OK
        """
        if not text:
            return None
        
        if LLMResponseValidator.PERSONALITY_REDEFINITION_PATTERN.search(text):
            return "Response redefines personality in a single step (forbidden)"
        
        return None
    
    @staticmethod
    def validate_cognition_response(
        response_dict: Dict[str, Any]
    ) -> CognitionLLMResponse:
        """
        Validate and parse a complete cognition LLM response.
        
        Args:
            response_dict: Raw JSON response from LLM
        
        Returns:
            CognitionLLMResponse with validation status
        """
        validation_errors = []
        
        try:
            # Extract fields with defaults
            utterance = response_dict.get("utterance")
            action = response_dict.get("action")
            stance_shifts_raw = response_dict.get("stance_shifts", [])
            intention_updates_raw = response_dict.get("intention_updates", [])
            
            # Validate utterance and action
            if utterance is not None and isinstance(utterance, str):
                error = LLMResponseValidator.validate_no_numeric_values(utterance)
                if error:
                    validation_errors.append(f"utterance: {error}")
                
                error = LLMResponseValidator.validate_no_personality_redefinition(utterance)
                if error:
                    validation_errors.append(f"utterance: {error}")
            
            if action is not None and isinstance(action, str):
                error = LLMResponseValidator.validate_no_numeric_values(action)
                if error:
                    validation_errors.append(f"action: {error}")
            
            # Parse stance shifts
            stance_shifts = []
            for i, shift in enumerate(stance_shifts_raw):
                if not isinstance(shift, dict):
                    validation_errors.append(f"stance_shifts[{i}]: not a dict")
                    continue
                
                target = shift.get("target")
                description = shift.get("description")
                
                if not target:
                    validation_errors.append(f"stance_shifts[{i}]: missing target")
                    continue
                
                if not description:
                    validation_errors.append(f"stance_shifts[{i}]: missing description")
                    continue
                
                if not isinstance(description, str):
                    validation_errors.append(f"stance_shifts[{i}]: description not string")
                    continue
                
                error = LLMResponseValidator.validate_no_numeric_values(description)
                if error:
                    validation_errors.append(f"stance_shifts[{i}].description: {error}")
                
                stance_shifts.append(
                    StanceShiftOutput(target=str(target), description=str(description))
                )
            
            # Parse intention updates
            intention_updates = []
            for i, update in enumerate(intention_updates_raw):
                if not isinstance(update, dict):
                    validation_errors.append(f"intention_updates[{i}]: not a dict")
                    continue
                
                operation = update.get("operation", "").lower()
                intent_type = update.get("type", "").lower()
                
                if operation not in ["create", "boost", "lower", "drop"]:
                    validation_errors.append(f"intention_updates[{i}]: invalid operation '{operation}'")
                    continue
                
                if intent_type not in ["avoid", "raise", "support", "protect", "distance"]:
                    validation_errors.append(f"intention_updates[{i}]: invalid type '{intent_type}'")
                    continue
                
                target = update.get("target")
                horizon = update.get("horizon", "medium").lower()
                description = update.get("description", "")
                
                if horizon not in ["short", "medium", "long"]:
                    validation_errors.append(f"intention_updates[{i}]: invalid horizon '{horizon}'")
                    horizon = "medium"  # Default
                
                intention_updates.append(
                    IntentionUpdateOutput(
                        operation=operation,
                        type=intent_type,
                        target=target,
                        horizon=horizon,
                        description=str(description) if description else ""
                    )
                )
            
            is_valid = len(validation_errors) == 0
            
            return CognitionLLMResponse(
                utterance=utterance,
                action=action,
                stance_shifts=stance_shifts,
                intention_updates=intention_updates,
                is_valid=is_valid,
                validation_errors=validation_errors
            )
        
        except Exception as e:
            return CognitionLLMResponse(
                is_valid=False,
                validation_errors=[f"Parse error: {str(e)}"]
            )


class LLMCognitionWrapper:
    """
    Wrapper for calling the reasoning LLM for cognition.
    
    Per cognition_flow.md §5:
    "Cognition LLM is called with CognitionContext(A, E) and MUST respond with structured data."
    
    This is a stubbed interface for actual LLM integration.
    In production, this would call Claude or similar via API.
    """
    
    COGNITION_SYSTEM_PROMPT = """You are Rebecca's psychology engine. For the given event and current state context, determine:
1. What Rebecca says NOW (if anything)
2. What Rebecca does NOW (if anything non-trivial)
3. How Rebecca's stance toward specific people shifts (if at all)
4. What intentions Rebecca creates, boosts, lowers, or drops (if any)

CRITICAL CONSTRAINTS:
- DO NOT output numeric values. Never say "set trust to 0.8" or similar.
- Describe only what happens, not why the numbers are what they are.
- Personality context (stable summary, domain summaries, activation) is FIXED for this moment. Do not claim Rebecca "becomes a different person."
- Stance shifts are SMALL moves (±0.1 to ±0.3 on relationship dimensions), not wholesale relationship redefinitions.
- Intentions are HIGH-LEVEL goals (avoid topic X, protect Y, support Z) not micro-behaviors.

Respond ONLY with valid JSON in this structure (utterance and action can be null):
{
  "utterance": "what Rebecca says, or null",
  "action": "what Rebecca does, or null",
  "stance_shifts": [
    {
      "target": "person_id or name",
      "description": "canonical stance description (e.g., 'gives benefit of doubt', 'escalates distrust')"
    }
  ],
  "intention_updates": [
    {
      "operation": "create|boost|lower|drop",
      "type": "avoid|raise|support|protect|distance",
      "target": "person_id, topic, or null",
      "horizon": "short|medium|long",
      "description": "what the intention is about"
    }
  ]
}"""
    
    @staticmethod
    def call_cognition_llm(
        context_packet: Dict[str, Any],
        model: CognitionLLMModel = CognitionLLMModel.CLAUDE_3_7_SONNET_REASONING
    ) -> CognitionLLMResponse:
        """
        Call the reasoning LLM with a cognition context packet.
        
        STUBBED: In production, this would make an API call to Claude.
        For testing, this returns a mock response.
        
        Args:
            context_packet: Semantic CognitionContext (JSON-compatible)
            model: Which LLM model to use
        
        Returns:
            Parsed and validated CognitionLLMResponse
        """
        # STUB: In production, this would call Claude API
        # For testing, we return a placeholder
        return CognitionLLMResponse()
    
    @staticmethod
    def validate_and_parse_response(response_json: Dict[str, Any]) -> CognitionLLMResponse:
        """
        Validate and parse a raw JSON response from the LLM.
        
        Args:
            response_json: Raw JSON dict from LLM
        
        Returns:
            Validated CognitionLLMResponse
        """
        return LLMResponseValidator.validate_cognition_response(response_json)
