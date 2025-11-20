"""
Redis Caching Service (Phase 9)

Provides non-authoritative caching layer for:
- LLM response caching
- Renderer perception context (last snapshots)
- Cognition cooldown and salience caches
- Recent unexpected-event triggers (short TTL)

**CRITICAL INVARIANTS:**
- Redis is NEVER the source of truth
- On Redis failure, system falls back to Postgres-only
- Core logic semantics unchanged with or without Redis
- All data is redundantly stored in Postgres

Per Plan.md §9.5: Redis caching constraints.
"""

import os
import json
import logging
from typing import Optional, Any, Dict
from datetime import datetime, timedelta
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class RedisService:
    """
    Non-authoritative caching service.
    
    Designed to fail silently and gracefully:
    - If Redis unavailable, all operations succeed (no caching)
    - Postgres queries used as fallback
    - No data loss if Redis restarted
    """
    
    # Cache key prefixes
    PREFIX_LLM_RESPONSE = "llm:cognition:"
    PREFIX_PERCEPTION = "perception:render:"
    PREFIX_COOLDOWN = "cooldown:cognition:"
    PREFIX_SALIENCE = "salience:context:"
    PREFIX_EVENT_TRIGGER = "event:trigger:"
    
    # Default TTLs (seconds)
    TTL_LLM_RESPONSE = 3600 * 24  # 24 hours
    TTL_PERCEPTION = 300  # 5 minutes (ephemeral)
    TTL_COOLDOWN = 3600  # 1 hour
    TTL_SALIENCE = 600  # 10 minutes
    TTL_EVENT_TRIGGER = 60  # 1 minute (very short)
    
    def __init__(self):
        """Initialize Redis connection (will be lazy-loaded)."""
        self.redis_url = os.environ.get("REDIS_URL")
        self.redis_client: Optional[redis.Redis] = None
        self.enabled = bool(self.redis_url)
        
        if self.enabled:
            logger.info(f"Redis caching enabled: {self.redis_url}")
        else:
            logger.warning("Redis not configured (REDIS_URL env var missing). Caching disabled.")
    
    async def connect(self) -> None:
        """
        Establish Redis connection.
        Failure here is non-fatal - system continues without caching.
        """
        if not self.enabled:
            return
        
        try:
            self.redis_client = await redis.from_url(
                self.redis_url,
                encoding="utf8",
                decode_responses=True,
                socket_keepalive=True,
                socket_connect_timeout=5
            )
            # Test connection
            await self.redis_client.ping()
            logger.info("✓ Redis connection established")
        except Exception as e:
            logger.warning(f"✗ Failed to connect to Redis: {e}. Caching disabled.")
            self.redis_client = None
            self.enabled = False
    
    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis connection closed")
    
    async def is_available(self) -> bool:
        """Check if Redis is currently available."""
        if not self.redis_client:
            return False
        
        try:
            await self.redis_client.ping()
            return True
        except Exception:
            return False
    
    # ========================================================================
    # LLM RESPONSE CACHING
    # ========================================================================
    
    async def cache_llm_cognition_response(
        self,
        agent_id: int,
        event_hash: str,
        response: Dict[str, Any],
        ttl: int = TTL_LLM_RESPONSE
    ) -> bool:
        """
        Cache LLM cognition response.
        
        Key: llm:cognition:{agent_id}:{event_hash}
        
        Args:
            agent_id: Agent ID
            event_hash: Hash of event (semantic + numeric signature)
            response: LLM response dict
            ttl: Cache TTL in seconds
            
        Returns:
            True if cached, False if caching unavailable
        """
        if not self.redis_client:
            return False
        
        try:
            key = f"{self.PREFIX_LLM_RESPONSE}{agent_id}:{event_hash}"
            value = json.dumps(response)
            await self.redis_client.setex(key, ttl, value)
            return True
        except Exception as e:
            logger.debug(f"Failed to cache LLM response: {e}")
            return False
    
    async def get_llm_cognition_response(
        self,
        agent_id: int,
        event_hash: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached LLM cognition response.
        
        Returns:
            Cached response dict, or None if not found/unavailable
        """
        if not self.redis_client:
            return None
        
        try:
            key = f"{self.PREFIX_LLM_RESPONSE}{agent_id}:{event_hash}"
            value = await self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.debug(f"Failed to retrieve cached LLM response: {e}")
            return None
    
    # ========================================================================
    # PERCEPTION CONTEXT CACHING (Ephemeral)
    # ========================================================================
    
    async def cache_perception_snapshot(
        self,
        user_id: int,
        snapshot: Dict[str, Any],
        ttl: int = TTL_PERCEPTION
    ) -> bool:
        """
        Cache recent perception snapshot for user.
        
        Very short TTL (5 min default) - meant for preventing redundant renders
        within same session.
        
        Key: perception:render:{user_id}
        """
        if not self.redis_client:
            return False
        
        try:
            key = f"{self.PREFIX_PERCEPTION}{user_id}"
            value = json.dumps(snapshot)
            await self.redis_client.setex(key, ttl, value)
            return True
        except Exception as e:
            logger.debug(f"Failed to cache perception snapshot: {e}")
            return False
    
    async def get_perception_snapshot(
        self,
        user_id: int
    ) -> Optional[Dict[str, Any]]:
        """Retrieve most recent perception snapshot for user."""
        if not self.redis_client:
            return None
        
        try:
            key = f"{self.PREFIX_PERCEPTION}{user_id}"
            value = await self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.debug(f"Failed to retrieve perception snapshot: {e}")
            return None
    
    # ========================================================================
    # COGNITION COOLDOWN CACHING
    # ========================================================================
    
    async def set_cognition_cooldown(
        self,
        agent_id: int,
        cooldown_until: datetime,
        ttl: int = TTL_COOLDOWN
    ) -> bool:
        """
        Cache agent's cognition cooldown timer.
        
        Key: cooldown:cognition:{agent_id}
        
        Value: ISO 8601 timestamp of when cooldown expires
        """
        if not self.redis_client:
            return False
        
        try:
            key = f"{self.PREFIX_COOLDOWN}{agent_id}"
            value = cooldown_until.isoformat()
            await self.redis_client.setex(key, ttl, value)
            return True
        except Exception as e:
            logger.debug(f"Failed to cache cooldown: {e}")
            return False
    
    async def get_cognition_cooldown(
        self,
        agent_id: int
    ) -> Optional[datetime]:
        """
        Get agent's cognition cooldown expiration time.
        
        Returns:
            datetime when cooldown expires, or None if not cooling down / unavailable
        """
        if not self.redis_client:
            return None
        
        try:
            key = f"{self.PREFIX_COOLDOWN}{agent_id}"
            value = await self.redis_client.get(key)
            if value:
                return datetime.fromisoformat(value)
            return None
        except Exception as e:
            logger.debug(f"Failed to retrieve cooldown: {e}")
            return None
    
    async def clear_cognition_cooldown(self, agent_id: int) -> bool:
        """Clear cooldown for agent."""
        if not self.redis_client:
            return False
        
        try:
            key = f"{self.PREFIX_COOLDOWN}{agent_id}"
            await self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.debug(f"Failed to clear cooldown: {e}")
            return False
    
    # ========================================================================
    # SALIENCE CONTEXT CACHING
    # ========================================================================
    
    async def cache_salience_context(
        self,
        agent_id: int,
        context: Dict[str, Any],
        ttl: int = TTL_SALIENCE
    ) -> bool:
        """
        Cache computed salience context for agent.
        
        Key: salience:context:{agent_id}
        
        Salience is quick to compute but contextualizes many downstream decisions.
        Light caching (10 min) helps with rapid UI refresh.
        """
        if not self.redis_client:
            return False
        
        try:
            key = f"{self.PREFIX_SALIENCE}{agent_id}"
            value = json.dumps(context)
            await self.redis_client.setex(key, ttl, value)
            return True
        except Exception as e:
            logger.debug(f"Failed to cache salience context: {e}")
            return False
    
    async def get_salience_context(
        self,
        agent_id: int
    ) -> Optional[Dict[str, Any]]:
        """Retrieve cached salience context."""
        if not self.redis_client:
            return None
        
        try:
            key = f"{self.PREFIX_SALIENCE}{agent_id}"
            value = await self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.debug(f"Failed to retrieve salience context: {e}")
            return None
    
    # ========================================================================
    # UNEXPECTED EVENT TRIGGER CACHING (Very short TTL)
    # ========================================================================
    
    async def cache_recent_event_trigger(
        self,
        event_id: int,
        trigger_info: Dict[str, Any],
        ttl: int = TTL_EVENT_TRIGGER
    ) -> bool:
        """
        Cache recently triggered unexpected event.
        
        Key: event:trigger:{event_id}
        
        Very short TTL (1 min) - prevents re-processing same event trigger
        within a short window.
        """
        if not self.redis_client:
            return False
        
        try:
            key = f"{self.PREFIX_EVENT_TRIGGER}{event_id}"
            value = json.dumps(trigger_info)
            await self.redis_client.setex(key, ttl, value)
            return True
        except Exception as e:
            logger.debug(f"Failed to cache event trigger: {e}")
            return False
    
    async def was_event_recently_triggered(
        self,
        event_id: int
    ) -> bool:
        """Check if event was recently triggered."""
        if not self.redis_client:
            return False
        
        try:
            key = f"{self.PREFIX_EVENT_TRIGGER}{event_id}"
            exists = await self.redis_client.exists(key)
            return bool(exists)
        except Exception as e:
            logger.debug(f"Failed to check event trigger: {e}")
            return False
    
    # ========================================================================
    # UTILITIES
    # ========================================================================
    
    async def clear_agent_caches(self, agent_id: int) -> bool:
        """Clear all caches for an agent (when state changes)."""
        if not self.redis_client:
            return False
        
        try:
            pattern_keys = [
                f"{self.PREFIX_COOLDOWN}{agent_id}",
                f"{self.PREFIX_SALIENCE}{agent_id}",
            ]
            for key in pattern_keys:
                await self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.debug(f"Failed to clear agent caches: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check Redis health.
        
        Returns:
            {
                "available": bool,
                "connected": bool,
                "url_configured": bool,
                "error": Optional[str]
            }
        """
        return {
            "available": await self.is_available(),
            "connected": self.redis_client is not None,
            "url_configured": self.enabled,
            "error": None if self.redis_client else "Redis not configured"
        }


# Global instance
_redis_service: Optional[RedisService] = None


async def get_redis_service() -> RedisService:
    """Get or create global Redis service instance."""
    global _redis_service
    if _redis_service is None:
        _redis_service = RedisService()
        await _redis_service.connect()
    return _redis_service
