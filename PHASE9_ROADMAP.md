# Phase 9 Roadmap — Hardening, Caching, and Vector Memory

**Current Status:** Ready to begin  
**Date:** 2025-11-20

Per Plan.md §9, Phase 9 focuses on:
1. Full test coverage and stability
2. Long-duration world simulations
3. Optimization (prompt size, context size)
4. Redis caching layer (non-authoritative)
5. Qdrant vector memory layer (episodic + biographical retrieval)

**Critical Constraints:**
- Core logic semantics MUST remain identical with or without caching
- Redis is NEVER authoritative (Postgres always is)
- Qdrant is used ONLY for retrieval ranking/similarity
- No unique information can exist only in Redis or Qdrant
- System must fallback gracefully if caches fail

## 9.1 Full Test Coverage Implementation

### Status: NOT STARTED

Per `docs/test_suite_outline.md`, implement every test category:

**Categories to add:**
- [ ] Unit tests for each service module
- [ ] Integration tests for full pipelines
- [ ] End-to-end scenario tests
- [ ] Stress tests (many agents, many ticks)
- [ ] Determinism tests (same state → same output)
- [ ] Regression tests (for any bugs found)

**Expected Outcomes:**
- 100+ additional test cases
- Coverage >85% of backend code
- Clear test organization by phase

## 9.2 Add Regression Tests

### Status: NOT STARTED

For any bugs found during Phase 8 testing or Phase 9 development:
- [ ] Create regression test before fixing bug
- [ ] Ensure fix passes regression test
- [ ] Keep test in suite to prevent future regressions

## 9.3 Long-Duration World Simulations

### Status: NOT STARTED

Run extended simulations to test:
- [ ] Determinism over 1000+ ticks
- [ ] Memory accumulation (do agents' memories grow sensibly?)
- [ ] Relationship drift (do relationships evolve realistically?)
- [ ] Arc progression (do narrative arcs develop?)
- [ ] Intention completion/failure cycles
- [ ] Calendar/obligation system stability
- [ ] Incursion generation patterns
- [ ] Performance under load

**Success Criteria:**
- No crashes or data corruption
- Deterministic behavior (same seed → same output)
- Memory usage stays within bounds
- Database query performance acceptable

## 9.4 Optimization Phase

### Status: NOT STARTED

#### 9.4.1 Prompt Size Reduction
- [ ] Audit all LLM prompts (cognition + renderer)
- [ ] Remove redundant context
- [ ] Consolidate similar information
- [ ] Keep only semantically distinct information

**Goal:** Reduce token usage while maintaining quality

#### 9.4.2 Semantic Context Size
- [ ] Profile cognition context builder
- [ ] Limit visible entity lists intelligently
- [ ] Truncate memory lists (keep N most relevant)
- [ ] Compress personality summaries if needed

**Goal:** Faster API calls, lower latency

#### 9.4.3 Database Query Optimization
- [ ] Analyze slow queries (use Railway logs)
- [ ] Add indexes where needed
- [ ] Consider batch operations where applicable
- [ ] Profile connection pool usage

## 9.5 Redis Caching Layer

### Status: NOT STARTED

**Requirement:** Add Redis service to Railway without changing core semantics.

### 9.5.1 Setup

```bash
# In Railway project:
# 1. Create new Redis service
# 2. Add REDIS_URL to backend env vars
# 3. Add redis dependency to requirements.txt
```

### 9.5.2 Implementation

Create `/backend/cache/redis_client.py`:
- [ ] Async Redis client wrapper
- [ ] Connection pooling
- [ ] Fallback to no-cache if Redis unavailable
- [ ] TTL management
- [ ] Cache invalidation strategy

### 9.5.3 Cache Targets

**Safe to cache (with appropriate TTL):**

1. **LLM Response Cache**
   - Cache cognition/renderer LLM responses
   - Key: hash of (agent_id, event_context, state_hash)
   - TTL: 1 hour (responses valid for a limited time)
   - Safe: Yes (validated for current state)

2. **Renderer Perception Context**
   - Cache last N perception packets per agent
   - Key: hash of (user_id, world_tick)
   - TTL: 5 minutes (perception changes as world changes)
   - Safe: Yes (invalidated when world advances)

3. **Cognition Cooldown + Salience Caches**
   - Cache agent salience calculations (expensive)
   - Key: (agent_id, tick)
   - TTL: until next tick
   - Safe: Yes (deterministic given state)

4. **Recent Incursion Triggers**
   - Cache which agents triggered incursions this tick
   - Key: tick_number
   - TTL: until next tick
   - Safe: Yes (performance-only optimization)

### 9.5.4 Constraints & Fallback

```python
# Pseudocode
async def get_cognition_context(agent_id):
    cache_key = f"cognition:{agent_id}:{world_tick}"
    
    # Try cache first
    cached = await redis.get(cache_key)
    if cached:
        return cached
    
    # Cache miss: compute and store
    context = compute_cognition_context(agent_id)
    await redis.setex(cache_key, TTL, context)
    return context

# On Redis failure:
#   - Continue without cache (slight performance hit)
#   - Log warning
#   - Core logic unchanged
```

### 9.5.5 Testing

- [ ] Cache hit/miss behavior
- [ ] TTL expiration
- [ ] Correct invalidation on state change
- [ ] Determinism with and without cache
- [ ] Graceful fallback if Redis down
- [ ] No data corruption from stale cache

## 9.6 Qdrant Vector Memory Layer

### Status: NOT STARTED

**Requirement:** Add Qdrant for episodic + biographical memory retrieval without changing core logic.

### 9.6.1 Setup

```bash
# In Railway project:
# 1. Create custom container with Qdrant
# 2. Add QDRANT_URL, QDRANT_API_KEY to env vars
# 3. Add qdrant-client dependency to requirements.txt
```

### 9.6.2 Architecture

**Collections:**

1. **episodic_memories**
   - Vector: Embedding of memory description
   - Metadata: (agent_id, timestamp, salience, source: "event" | "cognition")
   - Used for: Semantic similarity search + recency + salience ranking

2. **biographical_memories**
   - Vector: Embedding of biographical fact
   - Metadata: (agent_id, timestamp_learned, importance)
   - Used for: Personality-shaping facts retrieval

3. **(Optional) personality_summaries**
   - Vector: Embedding of personality description
   - Metadata: (agent_id, domain)
   - Used for: Semantic personality matching (advanced)

### 9.6.3 Memory Retrieval Flow

**Current Flow (Postgres-only):**
```
Agent memory need
  → Query Postgres (recency + salience ranking)
  → Return top N memories
  → Build context
```

**Phase 9 Flow (with Qdrant):**
```
Agent memory need
  → Semantic query to Qdrant (similarity search)
  → Rank by: (similarity + recency + salience)
  → Return top N memories
  → Build context
```

### 9.6.4 Implementation

Create `/backend/memory/vector_retrieval.py`:
- [ ] Embedding function (via LLM or embedding model)
- [ ] Qdrant client wrapper
- [ ] Upsert episodic memories on creation
- [ ] Upsert biographical memories on learning
- [ ] Semantic search with ranking
- [ ] Fallback to Postgres if Qdrant unavailable

### 9.6.5 Constraints

```python
# Pseudocode
async def retrieve_relevant_memories(agent_id, context):
    # Postgres is ALWAYS authoritative
    postgres_memories = await db.query(Memory).filter(
        Memory.agent_id == agent_id
    ).all()
    
    # If Qdrant available, use for semantic ranking
    if qdrant_available:
        embeddings = await vector_retrieval.search(
            context, agent_id, top_k=10
        )
        # Rank by: similarity + recency + salience
        ranked = rank_by_salience_and_recency(postgres_memories, embeddings)
    else:
        # Fallback: just use Postgres ranking
        ranked = rank_by_salience_and_recency(postgres_memories)
    
    return ranked[:5]  # Top 5 memories

# Key rule: No information exists only in Qdrant
#   All memories stored in Postgres
#   Qdrant is index + ranker only
```

### 9.6.6 Testing

- [ ] Retrieval quality (sanity checks)
- [ ] Deterministic ordering (given same embeddings)
- [ ] Fallback behavior (if Qdrant down)
- [ ] Memory upsert consistency
- [ ] No data loss if Qdrant reset
- [ ] Semantic relevance improvement vs Postgres-only

## Implementation Roadmap

### Sprint 1: Testing & Validation (Days 1-3)
1. Implement full test suite (9.1-9.2)
2. Run long-duration simulations (9.3)
3. Validate determinism over extended runs
4. Fix any bugs found in simulations

### Sprint 2: Optimization (Days 4-5)
1. Audit and reduce prompt sizes (9.4.1)
2. Optimize context sizes (9.4.2)
3. Profile database queries (9.4.3)
4. Measure before/after performance

### Sprint 3: Redis Caching (Days 6-7)
1. Set up Redis in Railway
2. Implement cache clients (9.5.1-9.5.2)
3. Add cache targets (9.5.3)
4. Test fallback behavior (9.5.5)

### Sprint 4: Qdrant Memory (Days 8-10)
1. Set up Qdrant in Railway
2. Implement vector retrieval (9.6.3-9.6.4)
3. Integrate with memory pipeline
4. Test semantic retrieval (9.6.6)

### Final: Integration & Validation (Days 11-12)
1. Full end-to-end tests with all layers
2. Performance validation
3. Determinism validation
4. Stability under load
5. Documentation

## Success Criteria for Phase 9

✅ **Testing:**
- 100+ new test cases added
- >85% code coverage
- All regression tests passing

✅ **Stability:**
- 1000+ tick simulations without crashes
- Deterministic behavior verified
- No data corruption

✅ **Performance:**
- 20%+ reduction in average prompt size
- 15%+ reduction in API latency
- Memory usage stable under load

✅ **Redis:**
- Cache hits on 40%+ of requests
- Graceful fallback working
- Core logic unchanged

✅ **Qdrant:**
- Semantic retrieval ranking better than random
- Fallback to Postgres working
- No information lost if Qdrant fails

## Notes for Implementation

1. **Commit frequently** - Each substep is a potential commit
2. **Test before optimization** - Baseline performance first
3. **Conservative caching** - Better to cache less than to corrupt data
4. **Explicit fallbacks** - Log all cache misses/failures
5. **Documentation** - Keep deployment docs updated
6. **Production safety** - Never break determinism or data integrity

## Next Phase After Phase 9

✅ **Phase 10 — UI Phase (LOCKED)**

Once Phase 9 is complete and verified:
- Backend is hardened and optimized
- Performance acceptable for production use
- Ready for UI development (Phase 10)

---

**Ready to begin Phase 9 implementation?**

Current status: Phase 8 COMPLETE, Phase 9 PLANNED
