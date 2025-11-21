"""
Perception-First Experience Engine (PFEE)

Implements:
- PFEE_ARCHITECTURE.md
- PFEE_LOGIC.md
- PFEE_PLAN.md

PFEE mediates between deterministic world state and LLM-based perception/cognition.
"""

from backend.pfee.orchestrator import PerceptionOrchestrator
from backend.pfee.triggers import TriggerEvaluator
from backend.pfee.entities import EntityPersistenceManager
from backend.pfee.potentials import PotentialResolver
from backend.pfee.consequences import ConsequenceIntegrator
from backend.pfee.time_continuity import TimeAndContinuityManager
from backend.pfee.influence_fields import InfluenceFieldManager
from backend.pfee.info_events import InformationEventManager
from backend.pfee.logging import PFEELogger

__all__ = [
    "PerceptionOrchestrator",
    "TriggerEvaluator",
    "EntityPersistenceManager",
    "PotentialResolver",
    "ConsequenceIntegrator",
    "TimeAndContinuityManager",
    "InfluenceFieldManager",
    "InformationEventManager",
    "PFEELogger",
]

