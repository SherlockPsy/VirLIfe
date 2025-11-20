# Phase 9: Hardening, Caching, and Vector Memory

**Status:** In Progress  
**Date:** 2025-11-20  
**Completed Components:** Redis, Qdrant infrastructure  
**Remaining:** Integration, testing, optimization

---

## Overview

Phase 9 implements non-authoritative caching and vector memory layers to improve system performance while maintaining determinism and data integrity. Per Plan.md §9 and MASTER_SPEC.md.

---

## 1. Caching Layer (Redis)

### Implementation: `backend/caching/redis_service.py`

**Purpose:** Non-authoritative caching for performance optimization.

**Key Invariants:**
- Redis is NEVER the source of truth
- System falls back to Postgres-only if Redis unavailable
- Core logic unchanged with/without Redis
- Deterministic behavior regardless of cache state

**Cache Types Implemented:**

#### 1.1 LLM Response Caching (24h TTL)
```
Key: llm:cognition:{agent_id}:{event_hash}
Value: Cached LLM response JSON
Usage: Avoid re-computing identical cognition scenarios
```

#### 1.2 Perception Context Caching (5 min TTL)
```
Key: perception:render:{user_id}
Value: Last rendered perception snapshot
Usage: Prevent redundant rendering within short window
Ephemeral: Very short TTL (perception changes frequently)
```

#### 1.3 Cognition Cooldown Caching (1h TTL)
```
Key: cooldown:cognition:{agent_id}
Value: ISO 8601 timestamp of cooldown expiration
Usage: Quick lookup of agent cognition cooldown state
Fallback: Query Postgres if unavailable
```

#### 1.4 Salience Context Caching (10 min TTL)
```
Key: salience:context:{agent_id}
Value: Computed salience context for agent
Usage: Contextualizes rapid decisions without recomputation
Fallback: Recalculate from Postgres if needed
```

#### 1.5 Event Trigger Caching (1 min TTL)
```
Key: event:trigger:{event_id}
Value: Recent unexpected event trigger info
Usage: Prevent duplicate trigger processing
Very short TTL: Events move through quickly
```

### Graceful Degradation

```python
# Example: If Redis unavailable, system continues
redis_service = await get_redis_service()
cached = await redis_service.cache_llm_response(...)
if not cached:
    # Redis unavailable, continue normally
    # Postgres will handle all queries
    pass

# Health check available
health = await redis_service.health_check()
# Returns: {available, connected, url_configured, error}
```

### Configuration

```bash
# In environment (Railway or local):
REDIS_URL=redis://user:pass@host:port/db
# or
REDIS_URL=redis://redis-service:6379

# If not set: caching disabled, Postgres-only mode
```

---

## 2. Vector Memory Layer (Qdrant)

### Implementation: `backend/memory/qdrant_service.py`

**Purpose:** Semantic similarity search for memory retrieval.

**Key Invariants:**
- Postgres is authoritative store for ALL memories
- Qdrant used ONLY for retrieval ranking and similarity
- No unique information exists only in Qdrant
- System falls back to Postgres-only retrieval if Qdrant unavailable

**Collections Managed:**

#### 2.1 Episodic Memories
```
Collection: episodic_memories
Vector: Embedding of memory description
Payload: {
  "agent_id": int,
  "type": "episodic",
  "description": str,
  "timestamp": ISO 8601
}
```

#### 2.2 Biographical Memories
```
Collection: biographical_memories
Vector: Embedding of biographical fact
Payload: {
  "agent_id": int,
  "type": "biographical",
  "description": str
}
```

#### 2.3 Personality Summaries (Optional)
```
Collection: personality_summaries
Vector: Embedding of personality summary
Payload: {
  "agent_id": int,
  "type": "personality",
  "summary": str
}
```

### Retrieval API

```python
# Search episodic memories
hits = await qdrant.search_episodic_memories(
    agent_id=1,
    query_text="conversation with Bob",
    limit=10,
    threshold=0.3  # Minimum similarity score
)
# Returns: List[MemoryHit] sorted by similarity

# Search biographical facts
hits = await qdrant.search_biographical_memories(
    agent_id=1,
    query_text="occupation",
    limit=5
)

# Search all memory types
hits = await qdrant.search_all_memories(
    agent_id=1,
    query_text="relationship conflict",
    limit=20
)
# Returns: Combined results, sorted by similarity
```

### Embeddings

Currently uses **deterministic hash-based embeddings** for guaranteed reproducibility:
- Same text → same vector always
- No model randomness
- Portable (no external embeddings service)

**Production migration path:**
```python
# Replace with real embeddings:
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')  # 384 dims
vector = model.encode(description).tolist()
```

### Graceful Degradation

```python
# If Qdrant unavailable:
qdrant = await get_qdrant_service()
hits = await qdrant.search_all_memories(...)
# Returns: []  (empty)
# Fallback: Postgres-only retrieval used instead
```

### Configuration

```bash
# In environment:
QDRANT_URL=http://qdrant-service:6333
QDRANT_API_KEY=your-api-key  # Optional, if auth enabled

# If not set: vector memory disabled, Postgres list retrieval only
```

---

## 3. Current Status

### ✅ Completed
- Redis caching service with 5 cache types
- Qdrant vector memory service with episodic/biographical search
- Graceful degradation for both services
- Comprehensive docstrings and type hints
- Environment variable configuration
- Health check endpoints

### 🔄 In Progress
- Integration tests for caching behavior
- Integration tests for vector memory
- Production Railway deployment (Redis + Qdrant services)
- Environment variable setup on Railway

### ⏳ Pending
- Actual embedding model integration (SentenceTransformer)
- Performance benchmarking
- Prompt and context size optimization (Phase 9.4)
- Long-duration stability tests (Phase 9.3)
- Regression test suite refinement

---

## 4. Integration Points

### Redis Integration Locations

```python
# Cognition Service (Phase 5)
# - Cache LLM responses by event hash
# - Check/set cognition cooldown before processing
# - Cache salience context for quick access

# Renderer Service (Phase 6)
# - Cache perception snapshots (ephemeral)
# - Check for duplicate render requests

# Gateway API (Phase 7)
# - Check Redis health in /health endpoint
```

### Qdrant Integration Locations

```python
# Cognition Service (Phase 5)
# - Search related memories when processing events
# - Use biographical facts to contextualize interpretation
# - Retrieve episodic memories for emotional continuity

# Renderer Service (Phase 6)
# - Search memories for narrative context
# - Retrieve biographical facts for background information
```

---

## 5. Testing Strategy

### Unit Tests
- Cache hit/miss behavior
- Correct cache key generation
- TTL enforcement
- Vector similarity calculations

### Integration Tests
- Full workflow: event → cache → query → result
- Fallback behavior when service unavailable
- Postgres-only correctness
- Determinism with/without caches

### Production Tests
- Load testing with concurrent cache operations
- Memory usage monitoring
- Network reliability testing
- Performance profiling

---

## 6. Deployment Checklist

### Before Production

- [ ] Deploy Redis service to Railway
- [ ] Deploy Qdrant service to Railway
- [ ] Set REDIS_URL environment variable
- [ ] Set QDRANT_URL and QDRANT_API_KEY environment variables
- [ ] Verify services are accessible from backend
- [ ] Run integration tests in production environment
- [ ] Monitor logs for caching behavior
- [ ] Verify fallback to Postgres-only works
- [ ] Performance baseline metrics established

### Rollback Plan

If issues arise:
1. Set `REDIS_URL=""` to disable Redis
2. Set `QDRANT_URL=""` to disable Qdrant
3. System continues with Postgres-only mode
4. Restart backend containers
5. All functionality intact, performance may decrease

---

## 7. Next Steps

1. **Integration (this week)**
   - Integrate Redis into Cognition Service
   - Integrate Redis into Renderer Service
   - Integrate Qdrant into Cognition Service
   - Add integration tests

2. **Testing**
   - Run long-duration simulations (50-100 ticks)
   - Verify determinism with/without caches
   - Load testing under concurrent requests

3. **Optimization**
   - Analyze LLM prompt sizes
   - Reduce semantic context redundancy
   - Profile Redis vs Postgres latencies

4. **Production Deployment**
   - Add to Railway infrastructure
   - Monitor performance improvements
   - Establish SLA for cache hit rates

---

## 8. References

- Plan.md §9.5: Redis caching requirements
- Plan.md §9.6: Qdrant vector memory requirements
- MASTER_SPEC.md §3.3: Memory system
- Architecture.md: Data stores and usage patterns

---

## Code Files

- `backend/caching/__init__.py` - Module exports
- `backend/caching/redis_service.py` - Redis implementation (335 lines)
- `backend/memory/__init__.py` - Module exports
- `backend/memory/qdrant_service.py` - Qdrant implementation (515 lines)

**Total: ~850 lines of caching and memory infrastructure**

---

**Phase 9 Implementation:** Redis + Qdrant Infrastructure Complete  
**Phase 9 Remaining:** Integration, testing, optimization, deployment
