"""
Cognition Module

Complete cognition service for agent psychology processing.
Includes salience calculation, meaningfulness scoring, eligibility checking,
LLM integration, and deterministic numeric state updates.

Per cognition_flow.md and MASTER_SPEC.
"""

from backend.cognition.salience import (
    SalienceCalculator,
    AgentSalienceContext,
    SalienceScore,
    SalienceCategory
)

from backend.cognition.meaningfulness import (
    MeaningfulnessCalculator,
    MeaningfulnessScore,
    MEANINGFULNESS_WEIGHTS,
    DEFAULT_COGNITION_THRESHOLD
)

from backend.cognition.eligibility import (
    CognitionEligibilityChecker,
    CognitionEligibilityResult,
    EventTrivialityClassification,
    BehavioralChoice,
    BehavioralChoiceType
)

from backend.cognition.llm_wrapper import (
    LLMCognitionWrapper,
    LLMResponseValidator,
    CognitionLLMResponse,
    StanceShiftOutput,
    IntentionUpdateOutput,
    CognitionLLMModel
)

from backend.cognition.numeric_updates import (
    StanceShiftMapper,
    IntentionUpdateMapper,
    IntentionOperationType,
    IntentionType,
    IntentionHorizon,
    StanceShiftMapping,
    IntentionUpdateEffect
)

from backend.cognition.service import (
    CognitionService,
    CognitionInput,
    CognitionOutput
)

__all__ = [
    # Salience
    "SalienceCalculator",
    "AgentSalienceContext",
    "SalienceScore",
    "SalienceCategory",
    
    # Meaningfulness
    "MeaningfulnessCalculator",
    "MeaningfulnessScore",
    "MEANINGFULNESS_WEIGHTS",
    "DEFAULT_COGNITION_THRESHOLD",
    
    # Eligibility
    "CognitionEligibilityChecker",
    "CognitionEligibilityResult",
    "EventTrivialityClassification",
    "BehavioralChoice",
    "BehavioralChoiceType",
    
    # LLM Wrapper
    "LLMCognitionWrapper",
    "LLMResponseValidator",
    "CognitionLLMResponse",
    "StanceShiftOutput",
    "IntentionUpdateOutput",
    "CognitionLLMModel",
    
    # Numeric Updates
    "StanceShiftMapper",
    "IntentionUpdateMapper",
    "IntentionOperationType",
    "IntentionType",
    "IntentionHorizon",
    "StanceShiftMapping",
    "IntentionUpdateEffect",
    
    # Service
    "CognitionService",
    "CognitionInput",
    "CognitionOutput"
]
