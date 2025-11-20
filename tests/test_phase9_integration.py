"""
Phase 9 Integration Tests: Caching and Vector Memory

Test suite for Phase 9 enhancements:
- Redis caching (cognition LLM responses, cooldown, renderer perception)
- Qdrant vector memory (episodic/biographical memory search)
- Graceful degradation when services unavailable
- Cache determinism and correctness

Per Plan.md §9 and PHASE9_INFRASTRUCTURE.md.
"""

import pytest
from datetime import datetime


class _FakeRedisClient:
    """Minimal async Redis stand-in for cache API tests."""

    def __init__(self):
        self.store = {}
        self.ttl = {}

    async def setex(self, key, ttl, value):
        self.store[key] = value
        self.ttl[key] = ttl

    async def get(self, key):
        return self.store.get(key)

    async def exists(self, key):
        return 1 if key in self.store else 0

    async def delete(self, key):
        self.store.pop(key, None)


class TestPhase9CachingIntegration:
    """Tests for Phase 9 caching integration."""
    
    def test_cognition_event_hash_deterministic(self):
        """
        Event hash computation should be deterministic.
        Same context always produces same hash (for caching).
        """
        from backend.cognition.service import CognitionService
        
        context1 = {
            "event_description": "Bob arrives",
            "personality": {"trait1": "value1"},
            "mood": "happy",
            "drives": {"autonomy": 0.5},
            "relationships": {"bob": {"warmth": 0.7}},
            "arcs": {},
            "energy": "moderate",
            "participants": [{"bob": {"name": "Bob"}}]
        }
        
        context2 = {
            "event_description": "Bob arrives",
            "personality": {"trait1": "value1"},
            "mood": "happy",
            "drives": {"autonomy": 0.5},
            "relationships": {"bob": {"warmth": 0.7}},
            "arcs": {},
            "energy": "moderate",
            "participants": [{"bob": {"name": "Bob"}}]
        }
        
        hash1 = CognitionService._compute_event_hash(context1)
        hash2 = CognitionService._compute_event_hash(context2)
        
        assert hash1 == hash2
        assert isinstance(hash1, str)
        assert len(hash1) == 64  # SHA256 hex string
    
    def test_cognition_event_hash_different_for_different_contexts(self):
        """
        Different event contexts should produce different hashes.
        """
        from backend.cognition.service import CognitionService
        
        context1 = {
            "event_description": "Bob arrives",
            "personality": {"trait1": "value1"},
            "mood": "happy",
            "drives": {"autonomy": 0.5},
            "relationships": {"bob": {"warmth": 0.7}},
            "arcs": {},
            "energy": "moderate",
            "participants": [{"bob": {"name": "Bob"}}]
        }
        
        context2 = {
            "event_description": "Alice arrives",  # Different event
            "personality": {"trait1": "value1"},
            "mood": "happy",
            "drives": {"autonomy": 0.5},
            "relationships": {"bob": {"warmth": 0.7}},
            "arcs": {},
            "energy": "moderate",
            "participants": [{"bob": {"name": "Bob"}}]
        }
        
        hash1 = CognitionService._compute_event_hash(context1)
        hash2 = CognitionService._compute_event_hash(context2)
        
        assert hash1 != hash2
    
    def test_renderer_context_hash_deterministic(self):
        """
        Perception context hash should be deterministic.
        Same perception context always produces same hash.
        """
        from backend.renderer.llm_wrapper import LLMRendererWrapper
        from backend.mapping.renderer_context import RendererContext
        
        context1 = RendererContext(
            perceiver_name="You",
            perceiver_type="user",
            location="living_room",
            visible_entities=["Rebecca", "Bob"],
            agent_personalities={},
            event_description="Rebecca smiles at you",
            event_type="speech",
            sensory_snapshot="You feel a warm presence nearby",
            scene_mode="normal"
        )
        
        context2 = RendererContext(
            perceiver_name="You",
            perceiver_type="user",
            location="living_room",
            visible_entities=["Rebecca", "Bob"],
            agent_personalities={},
            event_description="Rebecca smiles at you",
            event_type="speech",
            sensory_snapshot="You feel a warm presence nearby",
            scene_mode="normal"
        )
        
        hash1 = LLMRendererWrapper._compute_context_hash(context1)
        hash2 = LLMRendererWrapper._compute_context_hash(context2)
        
        assert hash1 == hash2
        assert isinstance(hash1, str)
        assert len(hash1) == 64  # SHA256 hex string
    
    def test_renderer_context_hash_different_for_different_contexts(self):
        """
        Different perception contexts should produce different hashes.
        """
        from backend.renderer.llm_wrapper import LLMRendererWrapper
        from backend.mapping.renderer_context import RendererContext
        
        context1 = RendererContext(
            perceiver_name="You",
            perceiver_type="user",
            location="living_room",
            visible_entities=["Rebecca", "Bob"],
            agent_personalities={},
            event_description="Rebecca smiles at you",
            event_type="speech",
            sensory_snapshot="You feel a warm presence nearby",
            scene_mode="normal"
        )
        
        context2 = RendererContext(
            perceiver_name="You",
            perceiver_type="user",
            location="bedroom",  # Different location
            visible_entities=["Rebecca", "Bob"],
            agent_personalities={},
            event_description="Rebecca smiles at you",
            event_type="speech",
            sensory_snapshot="You feel a warm presence nearby",
            scene_mode="normal"
        )
        
        hash1 = LLMRendererWrapper._compute_context_hash(context1)
        hash2 = LLMRendererWrapper._compute_context_hash(context2)
        
        assert hash1 != hash2


class TestPhase9ServiceIntegration:
    """Tests for Phase 9 service integration and imports."""
    
    def test_redis_service_importable_in_cognition(self):
        """Verify Redis service imports work in Cognition."""
        from backend.cognition.service import get_redis_service
        from backend.caching import get_redis_service as get_redis_direct
        
        assert get_redis_service is not None
        assert get_redis_direct is not None
    
    def test_qdrant_service_importable_in_cognition(self):
        """Verify Qdrant service imports work in Cognition."""
        from backend.cognition.service import get_qdrant_service
        from backend.memory import get_qdrant_service as get_qdrant_direct
        
        assert get_qdrant_service is not None
        assert get_qdrant_direct is not None
    
    def test_redis_service_importable_in_renderer(self):
        """Verify Redis service imports work in Renderer."""
        from backend.renderer.llm_wrapper import get_redis_service
        
        assert get_redis_service is not None
    
    def test_cognition_has_both_sync_and_async_methods(self):
        """Verify Cognition has both sync and async processing methods."""
        from backend.cognition.service import CognitionService
        
        # Should have both for backward compatibility and new functionality
        assert hasattr(CognitionService, 'process_cognition')
        assert hasattr(CognitionService, 'process_cognition_async')
        assert callable(CognitionService.process_cognition)
        assert callable(CognitionService.process_cognition_async)
    
    def test_cognition_has_event_hash_utility(self):
        """Verify Cognition service has event hash computation."""
        from backend.cognition.service import CognitionService
        
        assert hasattr(CognitionService, '_compute_event_hash')
        assert callable(CognitionService._compute_event_hash)
    
    def test_renderer_has_context_hash_utility(self):
        """Verify Renderer service has context hash computation."""
        from backend.renderer.llm_wrapper import LLMRendererWrapper
        
        assert hasattr(LLMRendererWrapper, '_compute_context_hash')
        assert callable(LLMRendererWrapper._compute_context_hash)
    
    def test_cache_service_has_ttl_constants(self):
        """Verify Redis service has proper TTL definitions."""
        from backend.caching import RedisService
        
        assert hasattr(RedisService, 'TTL_LLM_RESPONSE')
        assert hasattr(RedisService, 'TTL_PERCEPTION')
        assert hasattr(RedisService, 'TTL_COOLDOWN')
        assert hasattr(RedisService, 'TTL_SALIENCE')
        assert hasattr(RedisService, 'TTL_EVENT_TRIGGER')
        
        # Verify TTLs are reasonable (in seconds)
        assert RedisService.TTL_LLM_RESPONSE == 3600 * 24  # 24 hours
        assert RedisService.TTL_PERCEPTION == 300  # 5 minutes
        assert RedisService.TTL_COOLDOWN == 3600  # 1 hour
        assert RedisService.TTL_SALIENCE == 600  # 10 minutes
        assert RedisService.TTL_EVENT_TRIGGER == 60  # 1 minute


class TestPhase9MemoryServices:
    """Tests for Qdrant and memory service integration."""
    
    def test_memory_service_has_search_methods(self):
        """Verify Qdrant service has memory search methods."""
        from backend.memory import QdrantService
        
        assert hasattr(QdrantService, 'search_episodic_memories')
        assert hasattr(QdrantService, 'search_biographical_memories')
        assert hasattr(QdrantService, 'search_all_memories')
        assert hasattr(QdrantService, 'index_episodic_memory')
        assert hasattr(QdrantService, 'index_biographical_memory')
    
    def test_memory_hit_dataclass_exists(self):
        """Verify MemoryHit dataclass is available."""
        from backend.memory import MemoryHit
        
        # Create a test instance
        hit = MemoryHit(
            memory_id=1,
            agent_id=1,
            memory_type="episodic",
            description="test memory",
            similarity_score=0.95
        )
        
        assert hit.memory_id == 1
        assert hit.similarity_score == 0.95


@pytest.mark.asyncio
class TestRedisCacheApi:
    """Additional Redis cache API coverage for perception and cooldown utilities."""

    async def test_perception_cache_scoped_by_context_hash(self):
        """Caching perception snapshots should respect context hashes."""
        from backend.caching import RedisService

        service = RedisService()
        service.redis_client = _FakeRedisClient()
        service.enabled = True

        await service.cache_perception_snapshot(
            user_id="user-1",
            context_hash="ctx-a",
            snapshot={"value": "first"},
        )
        await service.cache_perception_snapshot(
            user_id="user-1",
            context_hash="ctx-b",
            snapshot={"value": "second"},
        )

        snap_a = await service.get_perception_snapshot("user-1", context_hash="ctx-a")
        snap_b = await service.get_perception_snapshot("user-1", context_hash="ctx-b")

        assert snap_a != snap_b
        assert snap_a["value"] == "first"
        assert snap_b["value"] == "second"

    async def test_cognition_cooldown_accepts_minutes(self):
        """Cooldown helper should accept minutes and store ISO timestamps."""
        from backend.caching import RedisService

        service = RedisService()
        service.redis_client = _FakeRedisClient()
        service.enabled = True

        await service.set_cognition_cooldown(agent_id=99, cooldown_minutes=1)

        cooldown_until = await service.get_cognition_cooldown(agent_id=99)
        assert cooldown_until is not None
        assert isinstance(cooldown_until, datetime)
