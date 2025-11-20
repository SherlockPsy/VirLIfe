"""
Numeric ↔ Semantic Mapping Layer
Phase 4 Implementation

This module provides deterministic conversion from numeric internal state
to semantic summaries for LLM consumption.

Implements:
- MASTER_SPEC §SECTION 12 — NUMERIC → SEMANTIC MAPPING
- docs/numeric_semantic_mapping.md
- Plan.md Phase 4

Key Principle:
- LLMs MUST NEVER receive raw numeric state
- All mappings MUST be deterministic
- All mappings MUST be rule-based, not LLM-generated
"""

from .semantic_mappers import (
    MoodMapper,
    DriveMapper,
    RelationshipMapper,
    ArcMapper,
    EnergyMapper,
    IntentionMapper,
    PersonalityMapper,
    MemoryMapper,
)
from .cognition_context import CognitionContext, CognitionContextBuilder
from .renderer_context import RendererContext, RendererContextBuilder

__all__ = [
    # Semantic Mappers
    "MoodMapper",
    "DriveMapper",
    "RelationshipMapper",
    "ArcMapper",
    "EnergyMapper",
    "IntentionMapper",
    "PersonalityMapper",
    "MemoryMapper",
    # Context Builders
    "CognitionContext",
    "CognitionContextBuilder",
    "RendererContext",
    "RendererContextBuilder",
]
