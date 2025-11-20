"""
Caching Layer (Phase 9)

Non-authoritative caches for performance optimization.
Redis is used as an optional cache layer; all data is backed by Postgres.

Per MASTER_SPEC.md and Plan.md §9.5.
"""

from backend.caching.redis_service import RedisService

__all__ = ["RedisService"]
