"""
Cognition Eligibility Checker Module

Implements the 4-factor check for cognition eligibility.
Per cognition_flow.md §3.4 and MASTER_SPEC.

For each agent A, cognition MUST ONLY be triggered if ALL are true:
1. M ≥ cognition_threshold.
2. Event type is not classified as trivial.
3. Cognition cooldown window for A has elapsed.
4. There exists at least one non-trivial behavioural choice to be made.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum
from datetime import datetime, timedelta


class EventTrivialityClassification(Enum):
    """Classification of event triviality."""
    TRIVIAL = "trivial"              # Small talk, background noise, routine actions
    MODERATE = "moderate"            # Regular interaction but not deeply relevant
    SIGNIFICANT = "significant"      # Emotionally or relationally meaningful
    CRITICAL = "critical"            # Arc-relevant, drive-relevant, high stakes


class BehavioralChoiceType(Enum):
    """Types of behavioral choices that matter for cognition eligibility."""
    RESPONSE_TO_DIRECT_ADDRESS = "response_to_direct_address"
    DISCRETIONARY_ACTION = "discretionary_action"
    CONFLICT_NAVIGATION = "conflict_navigation"
    RELATIONSHIP_BOUNDARY = "relationship_boundary"
    SELF_DISCLOSURE = "self_disclosure"
    ESCALATION_VS_DEESCALATION = "escalation_vs_deescalation"
    WITHDRAWAL_VS_ENGAGEMENT = "withdrawal_vs_engagement"
    ALLIANCE_FORMATION = "alliance_formation"


@dataclass
class BehavioralChoice:
    """Represents a significant behavioral choice point."""
    choice_type: BehavioralChoiceType
    description: str
    stakes: float  # [0, 1] - how much does this choice matter?
    
    def is_non_trivial(self, min_stakes: float = 0.3) -> bool:
        """Whether this choice is non-trivial (stakes above threshold)."""
        return self.stakes >= min_stakes


@dataclass
class CognitionEligibilityResult:
    """Full eligibility check result with component statuses."""
    is_eligible: bool                          # True if all 4 factors pass
    
    # Component checks
    factor_1_m_score_sufficient: bool         # M >= threshold
    factor_2_event_not_trivial: bool          # Event is non-trivial
    factor_3_cooldown_elapsed: bool           # Cooldown window has passed
    factor_4_behavioral_choice_exists: bool   # Non-trivial choice available
    
    # Metadata for reasoning/debugging
    m_score: Optional[float] = None
    event_triviality: Optional[EventTrivialityClassification] = None
    cooldown_remaining: Optional[timedelta] = None
    behavioral_choices: Optional[List[BehavioralChoice]] = None
    
    # Reason for ineligibility (if not eligible)
    rejection_reason: Optional[str] = None
    
    def __str__(self) -> str:
        """Human-readable eligibility summary."""
        if self.is_eligible:
            return f"✓ ELIGIBLE (M={self.m_score:.3f}, event={self.event_triviality.value}, choices={len(self.behavioral_choices or [])})"
        else:
            return f"✗ INELIGIBLE: {self.rejection_reason}"


class CognitionEligibilityChecker:
    """
    Determines whether cognition should be triggered for an agent.
    
    Per cognition_flow.md §3.4:
    "For each agent A, cognition MUST ONLY be triggered if ALL are true:
    1. M ≥ cognition_threshold.
    2. Event type is not classified as trivial.
    3. Cognition cooldown window for A has elapsed.
    4. There exists at least one non-trivial behavioural choice to be made.
    
    User presence MUST NOT be a separate rule.
    User actions influence variables that feed into M but do not bypass these checks."
    """
    
    # Default cooldown between cognition events for the same agent (minutes)
    DEFAULT_COGNITION_COOLDOWN_MINUTES = 5
    
    @staticmethod
    def check_factor_1_m_score(
        m_score_value: float,
        threshold: float
    ) -> bool:
        """
        Factor 1: M ≥ cognition_threshold
        
        Args:
            m_score_value: Computed M score [0, 1]
            threshold: Threshold for cognition
        
        Returns:
            True if M >= threshold
        """
        return m_score_value >= threshold
    
    @staticmethod
    def check_factor_2_event_triviality(
        triviality_classification: EventTrivialityClassification
    ) -> bool:
        """
        Factor 2: Event is not trivial
        
        Args:
            triviality_classification: Classification of the event
        
        Returns:
            True if event is NOT trivial (i.e., moderate, significant, or critical)
        """
        return triviality_classification != EventTrivialityClassification.TRIVIAL
    
    @staticmethod
    def check_factor_3_cooldown(
        last_cognition_time: Optional[datetime],
        current_time: datetime,
        cooldown_minutes: int = DEFAULT_COGNITION_COOLDOWN_MINUTES
    ) -> bool:
        """
        Factor 3: Cognition cooldown has elapsed
        
        Args:
            last_cognition_time: When cognition last ran for this agent (None if never)
            current_time: Current time
            cooldown_minutes: Cooldown duration in minutes
        
        Returns:
            True if cooldown has elapsed or agent has never had cognition
        """
        if last_cognition_time is None:
            return True
        
        cooldown_duration = timedelta(minutes=cooldown_minutes)
        return (current_time - last_cognition_time) >= cooldown_duration
    
    @staticmethod
    def check_factor_3_cooldown_remaining(
        last_cognition_time: Optional[datetime],
        current_time: datetime,
        cooldown_minutes: int = DEFAULT_COGNITION_COOLDOWN_MINUTES
    ) -> Optional[timedelta]:
        """
        Get remaining cooldown time (for debugging/UI).
        
        Args:
            last_cognition_time: When cognition last ran for this agent
            current_time: Current time
            cooldown_minutes: Cooldown duration in minutes
        
        Returns:
            Remaining timedelta if cooling down, None if cooled or never ran
        """
        if last_cognition_time is None:
            return None
        
        cooldown_duration = timedelta(minutes=cooldown_minutes)
        elapsed = current_time - last_cognition_time
        remaining = cooldown_duration - elapsed
        
        if remaining.total_seconds() <= 0:
            return None
        return remaining
    
    @staticmethod
    def check_factor_4_behavioral_choice(
        behavioral_choices: List[BehavioralChoice],
        min_choice_stakes: float = 0.3
    ) -> bool:
        """
        Factor 4: At least one non-trivial behavioral choice exists
        
        Args:
            behavioral_choices: List of available choices
            min_choice_stakes: Minimum stakes for a choice to be non-trivial
        
        Returns:
            True if at least one choice is non-trivial
        """
        if not behavioral_choices:
            return False
        
        for choice in behavioral_choices:
            if choice.stakes >= min_choice_stakes:
                return True
        
        return False
    
    @staticmethod
    def check_eligibility(
        m_score_value: float,
        m_threshold: float,
        event_triviality: EventTrivialityClassification,
        last_cognition_time: Optional[datetime],
        current_time: datetime,
        cooldown_minutes: int,
        behavioral_choices: List[BehavioralChoice],
        min_choice_stakes: float = 0.3
    ) -> CognitionEligibilityResult:
        """
        Comprehensive eligibility check (all 4 factors).
        
        Args:
            m_score_value: Computed M score
            m_threshold: M threshold for eligibility
            event_triviality: Event classification
            last_cognition_time: Last cognition execution time
            current_time: Current time
            cooldown_minutes: Cooldown duration
            behavioral_choices: Available choices
            min_choice_stakes: Minimum stakes threshold for non-trivial choice
        
        Returns:
            CognitionEligibilityResult with all components and verdict
        """
        factor_1 = CognitionEligibilityChecker.check_factor_1_m_score(
            m_score_value, m_threshold
        )
        factor_2 = CognitionEligibilityChecker.check_factor_2_event_triviality(
            event_triviality
        )
        factor_3 = CognitionEligibilityChecker.check_factor_3_cooldown(
            last_cognition_time, current_time, cooldown_minutes
        )
        factor_4 = CognitionEligibilityChecker.check_factor_4_behavioral_choice(
            behavioral_choices, min_choice_stakes
        )
        
        cooldown_remaining = CognitionEligibilityChecker.check_factor_3_cooldown_remaining(
            last_cognition_time, current_time, cooldown_minutes
        )
        
        # All factors must pass
        is_eligible = factor_1 and factor_2 and factor_3 and factor_4
        
        # Determine rejection reason if ineligible
        rejection_reason = None
        if not is_eligible:
            reasons = []
            if not factor_1:
                reasons.append(f"M score insufficient ({m_score_value:.3f} < {m_threshold:.3f})")
            if not factor_2:
                reasons.append(f"Event is trivial ({event_triviality.value})")
            if not factor_3:
                reasons.append(f"Cooldown not elapsed (remaining: {cooldown_remaining})")
            if not factor_4:
                reasons.append(f"No non-trivial behavioral choice (max stakes: {max([c.stakes for c in behavioral_choices]) if behavioral_choices else 0:.2f})")
            rejection_reason = "; ".join(reasons)
        
        return CognitionEligibilityResult(
            is_eligible=is_eligible,
            factor_1_m_score_sufficient=factor_1,
            factor_2_event_not_trivial=factor_2,
            factor_3_cooldown_elapsed=factor_3,
            factor_4_behavioral_choice_exists=factor_4,
            m_score=m_score_value,
            event_triviality=event_triviality,
            cooldown_remaining=cooldown_remaining,
            behavioral_choices=behavioral_choices,
            rejection_reason=rejection_reason
        )
