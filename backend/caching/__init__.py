"""
Caching Layer (Phase 9)

Non-authoritative caches for performance optimization.
Redis is used as an optional cache layer; all data is backed by Postgres.

Per MASTER_SPEC.md and Plan.md §9.5.
"""

from backend.caching.redis_service import RedisService, get_redis_service

__all__ = ["RedisService", "get_redis_service"]
