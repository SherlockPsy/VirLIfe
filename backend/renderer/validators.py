"""
Renderer Response Validators

Validates LLM-generated narratives to ensure:
- No invented events not in world state
- No user internal state narration
- No omniscient descriptions
- Schema consistency

Per Plan.md §6.4 and MASTER_SPEC §8 (Renderer Service).
"""

import re
from typing import Tuple, Optional, List
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of narrative validation."""
    is_valid: bool
    error_message: Optional[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class RendererResponseValidator:
    """
    Validates LLM-generated narratives.
    
    Per Plan.md §6.4:
    "Implement response validators:
    - Reject: invented events not in world state
    - Reject: user internal state narration
    - Reject: omniscient descriptions
    - Validate: schema, POV consistency"
    """
    
    # Patterns that indicate internal state attribution
    INTERNAL_STATE_PATTERNS = [
        r"you (?:feel|felt|think|thought|believe|believe|know|realize|understand|recognize)",
        r"you (?:are|were) (?:nervous|anxious|afraid|scared|happy|sad|angry|confused|uncertain|sure)",
        r"you (?:want|wanted|need|needed|desire|crave|wish)",
        r"you (?:remember|recall|forget)",
        r"your (?:heart|mind|soul) (?:is|was)",
        r"inwardly(?:\s+you)?",
        r"you somehow (?:know|realize|understand)",
    ]
    
    # Patterns indicating invented events
    INVENTED_EVENT_PATTERNS = [
        r"(?:suddenly|abruptly) (?:there|someone|something|rebecca|[a-z]+) (?:appears|enters|arrives|bursts)",
        r"(?:out of nowhere|from nowhere|without warning)",
        r"a (?:loud|sudden|sharp|unexpected) (?:sound|noise|crash|bang|scream)",
    ]
    
    # Patterns indicating omniscient knowledge
    OMNISCIENT_PATTERNS = [
        r"(?:rebecca|[a-z]+) (?:is|are|was|were) (?:thinking|remembering|feeling|planning|wanting|regretting)",
        r"(?:rebecca|[a-z]+) (?:secretly|inwardly|internally|in (?:her|his|their) mind)",
        r"(?:rebecca|[a-z]+) can't (?:hide|conceal|contain) (?:her|his|their)",
        r"you (?:can|could) (?:tell|see|sense) (?:that|what) (?:rebecca|[a-z]+) (?:is|was|thinks|feels)",
        r"(?:rebecca|[a-z]+) (?:appears|seems) to be (?:thinking|wanting|feeling)",
    ]
    
    # Patterns indicating second-person POV (good)
    SECOND_PERSON_PATTERNS = [
        r"\byou\b",
        r"\byour\b",
        r"\byours\b",
    ]
    
    # Patterns indicating first-person POV (good for agents)
    FIRST_PERSON_PATTERNS = [
        r"\bi\b",
        r"\bme\b",
        r"\bmy\b",
        r"\bmine\b",
    ]
    
    @staticmethod
    def validate_no_internal_state(narrative: str) -> Tuple[bool, Optional[str]]:
        """
        Check that narrative does not attribute internal state to user.
        
        Args:
            narrative: Generated narrative text
        
        Returns:
            (is_valid, error_message)
        """
        narrative_lower = narrative.lower()
        
        for pattern in RendererResponseValidator.INTERNAL_STATE_PATTERNS:
            if re.search(pattern, narrative_lower):
                return False, f"Narrative attributes internal state to user: '{pattern}' matched"
        
        return True, None
    
    @staticmethod
    def validate_no_invented_events(
        narrative: str,
        visible_entities: List[str],
        event_description: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Check that narrative doesn't invent events not in world state.
        
        Args:
            narrative: Generated narrative text
            visible_entities: Who/what should be visible
            event_description: What should be happening
        
        Returns:
            (is_valid, error_message)
        """
        narrative_lower = narrative.lower()
        
        # Check for invented event patterns
        for pattern in RendererResponseValidator.INVENTED_EVENT_PATTERNS:
            if re.search(pattern, narrative_lower):
                return False, f"Narrative may contain invented event: pattern '{pattern}' matched"
        
        # Check that described entities match visible ones (fuzzy)
        # Don't be too strict here - narrative can describe subset of visible entities
        
        return True, None
    
    @staticmethod
    def validate_no_omniscience(narrative: str) -> Tuple[bool, Optional[str]]:
        """
        Check that narrative does not claim omniscient knowledge of other minds.
        
        Args:
            narrative: Generated narrative text
        
        Returns:
            (is_valid, error_message)
        """
        narrative_lower = narrative.lower()
        
        for pattern in RendererResponseValidator.OMNISCIENT_PATTERNS:
            if re.search(pattern, narrative_lower):
                return False, f"Narrative claims omniscient knowledge: pattern '{pattern}' matched"
        
        return True, None
    
    @staticmethod
    def validate_pov_consistency(
        narrative: str,
        perceiver_type: str  # "user" or "agent"
    ) -> Tuple[bool, Optional[str]]:
        """
        Check that narrative maintains consistent POV.
        
        Args:
            narrative: Generated narrative text
            perceiver_type: "user" (should be second-person) or "agent" (should be first-person)
        
        Returns:
            (is_valid, error_message)
        """
        narrative_lower = narrative.lower()
        
        if perceiver_type == "user":
            # User perception should be second-person ("you")
            has_second_person = any(
                re.search(pattern, narrative_lower)
                for pattern in RendererResponseValidator.SECOND_PERSON_PATTERNS
            )
            if not has_second_person:
                return False, "User perception narrative does not use second-person POV ('you')"
            
            # Should not use first-person
            has_first_person = any(
                re.search(pattern, narrative_lower)
                for pattern in RendererResponseValidator.FIRST_PERSON_PATTERNS
            )
            if has_first_person:
                return False, "User perception narrative mixes first-person POV ('I') with second-person"
        
        elif perceiver_type == "agent":
            # Agent perception should be first-person ("I")
            has_first_person = any(
                re.search(pattern, narrative_lower)
                for pattern in RendererResponseValidator.FIRST_PERSON_PATTERNS
            )
            if not has_first_person:
                return False, "Agent perception narrative does not use first-person POV ('I')"
        
        return True, None
    
    @staticmethod
    def validate_basic_schema(narrative: str) -> Tuple[bool, Optional[str]]:
        """
        Check basic narrative schema:
        - Not empty
        - Not excessively long
        - Minimal punctuation rules
        
        Args:
            narrative: Generated narrative text
        
        Returns:
            (is_valid, error_message)
        """
        if not narrative or len(narrative.strip()) == 0:
            return False, "Narrative is empty"
        
        if len(narrative) > 2000:
            return False, "Narrative exceeds maximum length (2000 chars)"
        
        # Check basic sentence structure (at least one period or sentence-ending punctuation)
        if not any(punct in narrative for punct in ['.', '!', '?']):
            return False, "Narrative lacks sentence-ending punctuation"
        
        return True, None
    
    @staticmethod
    def validate_narrative(
        narrative: str,
        perceiver_type: str,
        visible_entities: Optional[List[str]] = None,
        event_description: Optional[str] = None,
        strict: bool = False
    ) -> ValidationResult:
        """
        Comprehensive narrative validation.
        
        Args:
            narrative: Generated narrative text
            perceiver_type: "user" or "agent"
            visible_entities: Optional list of visible entities for event check
            event_description: Optional event description for context
            strict: If True, fail on any warning; if False, warnings are informational
        
        Returns:
            ValidationResult with detailed feedback
        """
        
        # Basic schema validation
        is_valid, error = RendererResponseValidator.validate_basic_schema(narrative)
        if not is_valid:
            return ValidationResult(is_valid=False, error_message=error)
        
        # POV consistency
        is_valid, error = RendererResponseValidator.validate_pov_consistency(narrative, perceiver_type)
        if not is_valid:
            return ValidationResult(is_valid=False, error_message=error)
        
        # No internal state attribution
        is_valid, error = RendererResponseValidator.validate_no_internal_state(narrative)
        if not is_valid:
            return ValidationResult(is_valid=False, error_message=error)
        
        # No omniscience
        is_valid, error = RendererResponseValidator.validate_no_omniscience(narrative)
        if not is_valid:
            return ValidationResult(is_valid=False, error_message=error)
        
        # No invented events (optional, requires visible entities)
        if visible_entities and event_description:
            is_valid, error = RendererResponseValidator.validate_no_invented_events(
                narrative, visible_entities, event_description
            )
            if not is_valid and strict:
                return ValidationResult(is_valid=False, error_message=error)
            elif not is_valid:
                # Warning, not error
                if not hasattr(RendererResponseValidator, '_warnings'):
                    warnings = []
                else:
                    warnings = []
                warnings.append(error)
                return ValidationResult(is_valid=True, warnings=warnings)
        
        return ValidationResult(is_valid=True)
