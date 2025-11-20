# TEST_PLAN.md
VIRTUAL WORLD BACKEND — PHASED TEST SPEC

This document defines the COMPLETE test plan for the Virtual World backend.

It is written for an LLM test-runner (Cursor, Copilot, etc.).
You MUST treat all “MUST” / “MUST NOT” clauses as NORMATIVE.

The goal is:

1. Verify that ALL phases 0–9 are implemented as described in:
   - MASTER_SPEC.md
   - Architecture.md
   - Plan.md

2. Verify that the backend behaves correctly as a whole system:
   - deterministic world
   - no user simulation
   - numeric/semantic separation
   - renderer/gateway correctness
   - Redis/Qdrant used only as non-authoritative optimisations

You MUST NOT modify production code while running these tests,
except where the plan explicitly tells you to add or extend tests.

You MUST extend tests in `tests/` rather than replacing them.

You MUST use `pytest` as the test runner.

================================================================================
GLOBAL TEST RUN RULES
================================================================================

1. Test discovery and execution
   - You MUST be able to run:
       - `pytest`
       - `pytest -q`
       - `pytest tests/test_phase*_*.py`
   - Any test failure MUST be treated as a violation of MASTER_SPEC, Architecture,
     or Plan, and MUST be fixed by updating tests OR implementation, whichever
     is actually wrong. You MUST NOT silence tests.

2. Determinism
   - Where tests refer to determinism, you MUST:
       - initialise state in a fixture
       - run the same logic twice
       - assert identical outputs (world state, events, memory, etc.)
     This MUST be done WITHOUT seeding global RNGs in a way that breaks other tests.

3. User non-simulation
   - Tests MUST ensure:
       - `UserModel` has no mood/drives/traits/arcs/energy fields.
       - no code attaches psychology to the user.
       - LLM contexts NEVER include “user internal state”.

4. Numeric/semantic separation
   - Tests MUST ensure:
       - numeric substrate fields NEVER appear in LLM prompts
         (no raw floats, no kernel vectors, no `[0.0–1.0]` values)
       - semantic mapping is bucket-based and deterministic.

5. Redis/Qdrant optionality
   - Phase 9 tests MUST verify:
       - system runs with Redis/Qdrant disabled (env vars unset).
       - caching and vector retrieval are only optimisations.

================================================================================
PHASE-BY-PHASE TEST SUITES
================================================================================

You MUST ensure that each phase below has its OWN clearly named test module.
If missing, you MUST create it.

Suggested filenames (adapt to existing ones if they differ):

- `tests/test_phase0_health_and_docs.py`
- `tests/test_phase1_persistence.py`
- `tests/test_phase1_5_personality.py`
- `tests/test_phase2_world_and_calendar.py`
- `tests/test_phase2_determinism.py`
- `tests/test_phase3_autonomy.py`
- `tests/test_phase4_mapping.py`
- `tests/test_phase5_cognition.py`
- `tests/test_phase6_renderer.py`
- `tests/test_phase7_gateway.py`
- `tests/test_phase8_environment.py`
- `tests/test_phase9_cache_and_memory.py`

You MUST reference MASTER_SPEC / Architecture / Plan sections in test names or comments
where appropriate.

-------------------------------------------------------------------------------
PHASE 0 — PROJECT SKELETON, DOCS, HEALTH
-------------------------------------------------------------------------------

Tests MUST cover:

1. Docs presence & readability
   - MASTER_SPEC.md, Architecture.md, Plan.md, BUILDER_CONTRACT, ROUTER_PROMPT,
     CODEX_DEV_INSTRUCTIONS, cognition_flow, numeric_semantic_mapping,
     test_suite_outline MUST exist.
   - You MUST parse them and assert they are non-empty and contain the
     required section headings.

2. Health endpoint
   - `GET /health` MUST:
       - return 200
       - include a JSON payload with at least `status: "ok"` keys.
   - When DB is unreachable, `/health` MUST:
       - NOT crash the process
       - return a non-2xx OR a degraded-but-valid JSON payload.

-------------------------------------------------------------------------------
PHASE 1 — DOMAIN MODEL & PERSISTENCE
-------------------------------------------------------------------------------

Tests MUST cover:

1. Schema shape
   - `AgentModel` MUST have:
       - `drives`, `mood`, `personality_kernel`, `personality_summaries`,
         `domain_summaries`, `intentions`, `episodic_memories`,
         `biographical_memories`, `energy`.
   - `UserModel` MUST NOT have ANY of those.
   - RelationshipModel MUST allow edges from agents to agents and agents to user.

2. CRUD and persistence
   - World creation, save, reload.
   - Agent creation, psychology attach, save, reload.
   - Relationship creation and reload.
   - Memory insert and reload (episodic and biographical).

3. Restart invariants
   - Create a world and some agents → commit → close session.
   - Start a new session → reload world/agents → assert all essential state matches.

-------------------------------------------------------------------------------
PHASE 1.5 — PERSONALITY COMPILER & INITIALISATION
-------------------------------------------------------------------------------

Tests MUST cover:

1. Kernel determinism
   - Same template mixture + fingerprint → identical personality kernel.
   - Different mixtures → clearly different kernels.

2. Summary determinism
   - Same kernel + fingerprint → identical stable summary.
   - Summary regeneration only when inputs change.

3. Initial biographical memory & relationships
   - For a test agent with a fingerprint:
       - initial biographical memories MUST exist.
       - initial relationships toward user MUST exist and match the template config.

4. Non-LLM
   - Personality compiler MUST NOT call any LLM client.
   - Tests MUST assert imports and calls do NOT include OpenAI/Venice etc.

-------------------------------------------------------------------------------
PHASE 2 — WORLD ENGINE, CALENDARS, UNEXPECTED EVENTS, CONTINUITY
-------------------------------------------------------------------------------

Tests MUST cover:

1. World tick determinism
   - Fixture: world + 2 agents + initial time.
   - Run tick N times → snapshot relevant state.
   - Reset world to same initial state → tick N times again.
   - Assert:
       - `current_tick`, `current_time` identical.
       - same number and type of world events.
       - same continuity movements (locations of agents).

2. Calendar edge cases
   - No upcoming events: tick MUST NOT crash and MUST NOT create reminders.
   - Multiple overlapping events: correct number of reminder events.
   - Boundary condition: event exactly at reminder threshold gets ONE reminder.
   - Missed events: after passing time, “missed” events generate a `calendar_missed` event.

3. Incursion engine
   - For fixed world + tick, repeated calls MUST generate identical incursion sets.
   - Incursions MUST be stored as events, not just logs.
   - Incursion descriptions MUST be grounded in world context (time/location)
     and MUST NOT be purely random noise.

4. Continuity
   - Agents MUST move according to deterministic routines (e.g., 08:00 → kitchen).
   - Test: for a fixed routine map, repeated runs produce same locations.

-------------------------------------------------------------------------------
PHASE 3 — AUTONOMY ENGINE
-------------------------------------------------------------------------------

Tests MUST cover:

1. Drive update law
   - Events mapped to drive effects MUST produce changes consistent with MASTER_SPEC:
       - effect in [-1, 1], sensitivity applied, clamped to [0, 1].
   - Drift toward baseline MUST occur over time steps without events.

2. Mood law
   - Recent positive drive history → valence increases.
   - Recent negative drive history → valence decreases.
   - Arousal responds to novelty/conflict and decays toward baseline.

3. Relationship drift and updates
   - No events → warmth, trust drift toward neutral; tension decays; familiarity decays slowly.
   - Positive events → warmth/trust increase; tension decreases.
   - Negative events → warmth/trust decrease; tension increases.

4. Energy model
   - Energy falls under workload/high arousal; recovers during “rest” ticks.
   - Low energy raises cognition thresholds in Phase 5 tests.

-------------------------------------------------------------------------------
PHASE 4 — MAPPING (NUMERIC → SEMANTIC)
-------------------------------------------------------------------------------

Tests MUST cover:

1. Deterministic mapping
   - Given fixed numeric drives/mood/relationships, repeated calls produce identical text.

2. Bucket sanity
   - Values at extremes (near 0, near 1) map to appropriately strong phrases.
   - Mid-range values map to neutral/moderate phrases.

3. No numeric leakage
   - Semantic strings MUST NOT contain raw floats, percentages, or explicit numeric scales.
   - You MUST assert that mapping outputs contain no digits when passing typical ranges.

-------------------------------------------------------------------------------
PHASE 5 — COGNITION SERVICE
-------------------------------------------------------------------------------

Tests MUST cover:

1. Salience & meaningfulness
   - High-stakes events with strong drive pressure → high meaningfulness.
   - Trivial events → below threshold, no cognition.

2. Eligibility
   - Cognition triggered ONLY when meaningfulness ≥ threshold AND cooldown respected.
   - Low energy blocks cognition where specified.

3. LLM wrapper
   - Valid responses pass schema validation.
   - Responses with forbidden patterns (numeric state changes, full personality rewrites,
     simulation of the user) MUST be rejected or sanitised.

4. Numeric updates
   - Given a structured cognition decision (e.g., “stance: soften”), numeric updates MUST
     be deterministic and consistent with MASTER_SPEC mapping rules.

-------------------------------------------------------------------------------
PHASE 6 — RENDERER
-------------------------------------------------------------------------------

Tests MUST cover:

1. Perception-only, correct POV
   - Renderer output for user MUST:
       - be in second person (“you see…”).
       - describe only visible/ perceptible information, not hidden thoughts.
   - Renderer MUST NOT describe user feelings or unobservable internal states.

2. No omniscience
   - If an agent is not in the same location, their private actions MUST NOT be rendered.
   - If event is off-screen, it may affect atmosphere but MUST NOT be described directly.

3. Determinism with caching
   - Given identical world + perception packet, repeated calls MUST produce identical text
     (when using a stub or deterministic mode).
   - Where caching is enabled, a second render MUST re-use cached output if unchanged.

4. Adult vs non-adult model selection
   - For a scene flagged as “adult”, renderer MUST choose adult-capable model.
   - For non-adult scenes, renderer MUST NOT call adult model.

-------------------------------------------------------------------------------
PHASE 7 — GATEWAY
-------------------------------------------------------------------------------

Tests MUST cover:

1. Endpoint existence
   - `POST /user/action`, `POST /world/advance`, `GET /render` MUST exist and return
     the correct types/status codes.

2. No logic in gateway
   - Gateway handlers MUST delegate to world engine, autonomy, cognition, renderer.
   - Tests MUST ensure there is no world logic implemented directly in handlers.

3. Deterministic world advance
   - Two identical `/world/advance` runs from same state MUST produce identical
     world snapshots after N ticks.

4. Rendering via gateway
   - `GET /render` MUST return renderer output and NOT raw world state.

-------------------------------------------------------------------------------
PHASE 8 — ENVIRONMENT & RAILWAY SETUP
-------------------------------------------------------------------------------

Tests MUST cover:

1. Environment variable loading
   - `database_url` MUST be required and correctly converted to asyncpg URL.
   - Redis/Qdrant URLs MAY be unset; system MUST still run.

2. No hard-coded local paths
   - Config MUST NOT contain hard-coded local file paths or localhost-only assumptions.

3. Railway readiness
   - There MUST be a single entrypoint compatible with `uvicorn backend.main:app`.
   - Where RAILWAY_SETUP.md defines env vars, tests MUST assert that the config
     can load these names without crashing.

-------------------------------------------------------------------------------
PHASE 9 — REDIS & QDRANT
-------------------------------------------------------------------------------

Tests MUST cover:

A. REDIS

1. Optionality & fallback
   - With `REDIS_URL` unset:
       - `get_redis_service()` MUST return a disabled/None-like service.
       - Calls to caching helpers MUST NOT crash and MUST behave as cache misses.

2. Caching semantics
   - With Redis enabled:
       - caching LLM responses and perception packets MUST work.
       - TTLs MUST match intended durations (long for LLM output, short for salience).
       - Cache invalidation rules MUST be deterministic.

3. Non-authoritative
   - Deleting keys from Redis MUST NOT corrupt Postgres state.
   - Restarting without Redis MUST NOT break the system.

B. QDRANT

1. Optionality & fallback
   - With Qdrant config unset:
       - `get_qdrant_service()` MUST return disabled/None-like.
       - Cognition MUST fall back to DB-only memory retrieval.

2. Deterministic embeddings
   - `_embed_text` MUST be deterministic (same text → same vector).
   - Tests MUST assert that repeated calls for same input yield identical vectors.

3. Deterministic retrieval
   - For a fixed set of memories, queries MUST return same ordered results
     on repeated calls.

4. No numeric leakage
   - Only memory text and metadata (id, agent_id, type) are embedded.
   - Numeric psych state MUST NOT be embedded into Qdrant.

================================================================================
END-TO-END SCENARIOS
================================================================================

In addition to per-phase tests, you MUST implement at least two end-to-end tests:

1. Quiet Day Scenario
   - Create world and two agents (e.g., you and Rebecca).
   - Run ticks for a simulated day with:
       - some calendar events
       - some low-stakes interactions
   - Assertions:
       - world advances deterministically across reruns.
       - no cognition triggered when stakes are low.
       - renderer produces simple, perception-only descriptions.
       - Redis/Qdrant may be present or absent; behaviour remains correct.

2. High-Stakes Scenario
   - Create world and agents with high-tension relationship edges.
   - Inject a high-stakes event (conflict or disclosure).
   - Run tick & cognition pipeline.
   - Assertions:
       - meaningfulness crosses threshold, cognition triggers.
       - cognition output passes LLM wrapper validation.
       - numeric updates reflect stance/mood changes.
       - renderer describes the scene correctly in second person.
       - Redis/Qdrant usage (if enabled) improves performance but does NOT
         alter determinism or correctness.

================================================================================
EXECUTION INSTRUCTIONS FOR CURSOR’S LLMS
================================================================================

When running in Cursor:

1. LOAD and OBEY:
   - MASTER_SPEC.md
   - Architecture.md
   - Plan.md
   - This TEST_PLAN.md

2. For EACH phase:
   - Ensure the corresponding `tests/test_phaseX_*.py` file exists.
   - Implement or extend tests EXACTLY as specified above.
   - Run `pytest` and fix failures.
   - DO NOT claim a phase is “tested” until all tests are passing.

3. After all tests pass:
   - You MUST summarise:
       - which tests were added/modified
       - which invariants they checked
       - any changes made to implementation to satisfy MASTER_SPEC.

This completes the test plan for the Virtual World backend.