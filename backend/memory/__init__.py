"""
Vector Memory Layer (Phase 9)

Qdrant-based semantic memory retrieval for:
- Episodic memory summaries
- Episodic memories from unexpected events
- Biographical memory summaries
- Stable personality summaries (optional)

Per MASTER_SPEC.md §3.3 (Memory System) and Plan.md §9.6.
"""

from backend.memory.qdrant_service import QdrantService

__all__ = ["QdrantService"]
