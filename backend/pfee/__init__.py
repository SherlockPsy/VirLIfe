"""
Perception-First Experience Engine (PFEE)

Implements:
- PFEE_ARCHITECTURE.md
- PFEE_LOGIC.md
- PFEE_PLAN.md (Phases P0-P9)

PFEE mediates between deterministic world state and LLM-based perception/cognition.
All perception and cognition MUST go through PFEE.
"""

from backend.pfee.entities import EntityPersistenceManager, PersistenceLevel, EntityType
from backend.pfee.potentials import PotentialResolver, ResolvedPotential
from backend.pfee.influence_fields import InfluenceFieldManager
from backend.pfee.triggers import TriggerEvaluator, TriggerDecision, TriggerReason
from backend.pfee.orchestrator import PerceptionOrchestrator, PerceptionResult, run_perception_cycle
from backend.pfee.consequences import ConsequenceIntegrator
from backend.pfee.time_continuity import TimeAndContinuityManager
from backend.pfee.info_events import InformationEventManager, InfoEvent
from backend.pfee.logging import PFEELogger
from backend.pfee.semantic_mapping import PFEESemanticMapper
from backend.pfee.validation import ValidationResult

__all__ = [
    # Entity Persistence (P1)
    "EntityPersistenceManager",
    "PersistenceLevel",
    "EntityType",
    # Potentials and Influence Fields (P2)
    "PotentialResolver",
    "ResolvedPotential",
    "InfluenceFieldManager",
    # Triggers (P3)
    "TriggerEvaluator",
    "TriggerDecision",
    "TriggerReason",
    # Orchestrator (P4)
    "PerceptionOrchestrator",
    "PerceptionResult",
    "run_perception_cycle",  # C.2: Top-level entry point
    # Consequences (P5)
    "ConsequenceIntegrator",
    # Time Continuity (P6)
    "TimeAndContinuityManager",
    # Information Events (P7)
    "InformationEventManager",
    "InfoEvent",
    # Logging (P8)
    "PFEELogger",
    # Semantic Mapping
    "PFEESemanticMapper",
    # Validation
    "ValidationResult",
]

