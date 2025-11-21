# Architecture.md
## HIGH-LEVEL ARCHITECTURE FOR THE VIRTUAL WORLD BACKEND

This document describes the high-level architecture of the Virtual World Backend, including:

- services on Railway  
- data stores (Postgres, Redis, Qdrant)  
- LLM integrations  
- how subsystems talk to each other  

It does NOT override MASTER_SPEC.md.  
If there is any conflict, MASTER_SPEC.md and BUILDER_CONTRACT.md win.


## 1. DEPLOYMENT TOPOLOGY (RAILWAY)

All components live inside a single Railway project (e.g. `virlife`).

### 1.1 Core services

- `virlife-backend` (Python backend service)
  - Code from GitHub repo (e.g. `SherlockPsy/VirLIfe`).
  - Runs the HTTP API (Gateway).
  - Hosts all backend subsystems:
    - World Engine
    - Autonomy Engine
    - Personality Compiler
    - Mapping Layer
    - Cognition Wrapper
    - Renderer Wrapper
    - Persistence & DAL

- `virlife-db` (Postgres service)
  - Railway-managed Postgres instance.
  - Provides:
    - `PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`, `PGDATABASE`, `DATABASE_URL`.


### 1.2 Optional optimisation services (Phase 9 only)

These MUST NOT be used before Phase 9 in Plan.md:

- `virlife-redis` (Redis)
  - Non-authoritative cache.
  - Used for:
    - renderer context caching
    - cognition cooldown / salience cache
    - optional safe LLM response cache

- `virlife-qdrant` (Qdrant)
  - Vector database.
  - Used for:
    - episodic memory retrieval
    - biographical memory retrieval
    - optional personality-similarity queries


## 2. DATA STORE ROLES

### 2.1 Postgres — AUTHORITATIVE STATE

Postgres is the **only source of truth** for:

- world state:
  - time, tick
  - locations, objects
  - events and queues
- agent internal state:
  - drives
  - mood
  - arcs
  - relationships
  - intentions
  - energy
  - personality kernel
  - personality summaries and domain summaries
- memory:
  - episodic memories
  - biographical memories
- logs required for tests and debugging.

All reads and writes that matter for system correctness MUST go through Postgres.


### 2.2 Redis — NON-AUTHORITATIVE CACHE (PHASE 9+)

Redis is an optional, non-authoritative performance layer.

It MAY be used for:

- caching renderer perception packets:
  - last view of a scene
  - short TTL snapshots for quick re-renders
- caching cognition state:
  - last cognition timestamp per agent
  - precomputed salience values
- caching LLM responses for repeated, identical inputs (optional, safe keys only).
- caching recent unexpected-event triggers (short TTL) for performance ONLY.

Redis MUST:

- never become the canonical source for any state described in MASTER_SPEC.md.
- always be safe to flush without losing correctness.
- be bypassable: if Redis is down, the system falls back to Postgres-only behaviour,
  with behaviour remaining logically equivalent (though slower).


### 2.3 Qdrant — VECTOR MEMORY RETRIEVAL (PHASE 9+)

Qdrant is a vector store used for semantic similarity and memory retrieval.

It MAY be used for:

- storing embeddings of:
  - episodic memory summaries
  - episodic memories that originated as unexpected events
  - biographical memory summaries
  - optional stable personality summaries
- retrieving memories:
  - “find events similar to this situation”
  - “find biographical facts relevant to this topic”

Qdrant MUST NOT:

- replace Postgres as the store of record for memories.
- hold unique information that does not exist in Postgres.

Instead:

- Postgres stores the full memory records.
- Qdrant stores embeddings + IDs referencing the Postgres rows.
- Retrieval process:
  - query Qdrant by vector similarity
  - obtain candidate IDs
  - fetch full records from Postgres
  - combine with recency + salience rules from MASTER_SPEC.md.


## 3. BACKEND SUBSYSTEMS AND THEIR DATA DEPENDENCIES

### 3.1 World Engine (`/backend/world`)

- Reads/writes:
  - world schema in Postgres.
- Does NOT use Redis or Qdrant directly.
- Deterministic, no LLM use.

The World Engine is also responsible for:

- maintaining agent calendars, obligations, and long-term plans as world data,
- generating world events for:
  - scheduled events,
  - obligation start/expiry,
  - calendar-related reminders,
- generating unexpected events (incursions) originating from:
  - agent movement and routines,
  - calendar-driven activity,
  - environmental processes (e.g. deliveries, knocks, ambient incidents),
  - communication channels (messages, calls, notifications).


### 3.2 Autonomy Engine (`/backend/autonomy`)

- Reads/writes:
  - drives, mood, arcs, relationships, intentions, energy, memories in Postgres.
- MAY optionally:
  - write episodic/biographical memory summaries and embeddings into Postgres + Qdrant (Phase 9+).
- MUST NOT:
  - depend on Redis or Qdrant for core decision logic.

The Autonomy Engine MUST:

- treat calendar/obligation data as input pressures into decision-making,
- update intentions and decision pressure deterministically in response to:
  - approaching or missed obligations,
  - conflicts between commitments and current activities,
  - world-level unexpected events (incursions),
- NOT introduce any new psychological variables for calendars or incursions themselves.


### 3.3 Personality Compiler (`/backend/personality`)

- Reads:
  - personality templates from `/data/templates`.
  - fingerprints from `/data/fingerprints`.
- Writes:
  - personality kernel to Postgres.
  - personality summaries, domain summaries, and cached context fragments to Postgres.
- Does NOT use Redis or Qdrant directly.
- Embeddings for Qdrant (if any) are computed later by a dedicated mapping or memory component.


### 3.4 Mapping Layer (`/backend/mapping`)

- Responsible for:
  - numeric ↔ semantic mapping
  - generating semantic buckets for LLM.
- Reads numeric state from Postgres.
- Does NOT talk to Redis or Qdrant directly.


### 3.5 Cognition Service (`/backend/cognition`)

- Uses:
  - Postgres for core state (via DAL).
  - Mapping layer for semantic packets.
- MAY use Redis (Phase 9+) for:
  - caching cognition eligibility (cooldown, salience snapshots).
- Does NOT store authoritative state in Redis.
- MAY consult Qdrant (Phase 9+) indirectly through a memory retrieval helper to get similar memories,
  but the final memories are always re-fetched from Postgres.

Cognition MUST:

- receive calendar/obligation context when relevant,
- receive information about recent unexpected events when they significantly affect salience, meaning, or relational stakes.


### 3.6 Renderer Service (`/backend/renderer`)

- Uses:
  - world state and agent state via Postgres (through DAL).
  - mapping layer + personality summaries.
- MAY use Redis (Phase 9+) for:
  - caching last perception packet per user/session.
- Does NOT store any authoritative state in Redis.

Renderer MUST:

- render perception of calendars and obligations via:
  - visible artefacts (calendars, notes, devices),
  - observed behaviour (checking watch, leaving, preparing),
  - dialogue.
- render unexpected events (incursions) as perceptual interruptions:
  - knocks, doors opening, arrivals, notifications, etc.
- follow APPENDIX I and APPENDIX J of MASTER_SPEC.md for:
  - incursion behaviour,
  - calendar/obligation behaviour.


### 3.7 Gateway API (`/backend/gateway`)

- Exposes:
  - `/user/action`
  - `/world/advance`
  - `/render`
- Orchestrates calls into:
  - world engine
  - autonomy
  - cognition
  - renderer
- Reads/writes:
  - state via Postgres.
- MAY indirectly benefit from Redis + Qdrant, but MUST NOT depend on them for correctness.


### 3.8 Unexpected Events (Incursions)

Unexpected Events (Incursions) are world-level events that arise from:

- other agents’ schedules, routines, or movement,
- environmental processes (deliveries, knocks, noises, interruptions),
- communication channels (messages, calls, notifications),
- time-based triggers (calendar or world clock),
- natural world dynamics.

They are NOT a separate subsystem and MUST NOT be implemented as a new service.

They MUST be generated entirely by:

- the World Engine (origin, scheduling, environmental triggers),
- the Autonomy Engine (agent movement and activities that cause incursions),
- the Renderer (perceptual presentation to THE HUMAN USER).

Incursions MUST:

- be possible at any time,
- be derived from world state,
- be deterministic,
- interact naturally with all scenes (including intimate ones).

Incursions MUST NOT:

- bypass the Logic Layer,
- be enumerated as a fixed set of event categories,
- be LLM-fabricated without grounding in world data.

The Renderer presents incursions as interruptions in the sensory field.  
The Logic Layer updates agents in response to incursions normally, with no special-case psychology.


### 3.9 Calendars, Obligations, and Plans

The Calendar/Obligation system MUST be implemented as part of the World Engine.

Each agent MAY have:

- personal calendar entries,
- obligations,
- plans,
- recurring events.

These items MUST:

- be persisted in Postgres as world data,
- influence Autonomy (decision pressure, intention updates),
- influence Cognition when stakes are meaningful,
- be displayed by the Renderer through perception,
- be deterministic and grounded in world time.

Calendars MUST NOT introduce new psychological variables.  
Calendars MUST NOT be stored as drives, mood, relationship state, or arcs.  
Calendars are inputs, not psychology.

Unexpected Events MAY arise from calendar items (e.g., a taxi or visitor arriving at a scheduled time).  
World Engine MUST integrate both seamlessly.

## 4. LLM INTEGRATION

### 4.1 LLM Providers

The backend talks to one or more LLM providers (e.g. Venice):

- Cognition model (reasoning-only).
- Renderer model (perception-only, possibly adult-capable).

These are accessed via HTTP from the backend:

- Configured via env vars (e.g. `VENICE_API_KEY`, `VENICE_BASE_URL`, `COGNITION_MODEL_ID`, `RENDERER_MODEL_ID`).
- All calls MUST go through:
  - `/backend/cognition` (for cognition)
  - `/backend/renderer` (for rendering)


### 4.2 Numeric–Semantic Separation

- LLMs MUST NEVER receive raw numeric state.
- Mapping layer MUST generate semantic summaries as per `docs/numeric_semantic_mapping.md`.
- Redis and Qdrant do not change this rule:
  - Qdrant stores embeddings of semantic summaries or memory descriptions.
  - Redis caches semantic packets or recent results.


## 5. PHASE GATING FOR REDIS AND QDRANT

To avoid premature or incorrect use of Redis and Qdrant, the builder LLM MUST honour:

- Plan.md Phases 1–8:
  - Postgres-only implementation.
  - Redis and Qdrant MUST NOT appear in code, config, or tests.
- Plan.md Phase 9:
  - Redis and Qdrant MAY be introduced as described in Plan.md §9.5–9.6.
  - They MUST be used strictly as:
    - Redis → performance cache, non-authoritative.
    - Qdrant → vector retrieval, non-authoritative.

If any user instruction asks to wire Redis or Qdrant prior to Phase 9,  
the builder LLM MUST refuse and reference Plan.md and Architecture.md.


## 6. SUMMARY OF RESPONSIBILITIES

- Postgres:
  - authoritative state for everything defined in MASTER_SPEC.md.
- Redis:
  - optional, performance only, safe to lose.
- Qdrant:
  - optional, vector retrieval only, always backed by Postgres IDs.
- Backend:
  - implements all logic as per MASTER_SPEC.md and Plan.md.
  - uses LLMs only through cognition and renderer wrappers.
  - never encodes user internal psychology.

---------------------------------------------------------------------
FRONTEND SERVICE (RAILWAY)
---------------------------------------------------------------------

Name: `virlife-frontend` (exact name may vary, but MUST be a dedicated Railway service)

Purpose:
- Serve the Virtual World UI as a text-only, visually rich SPA.
- Connect to the backend gateway/API services over HTTPS and WebSockets.
- Provide a stable, browser-accessible entrypoint for the user.

Type:
- Railway service hosting a Node/JS-based frontend (e.g., React + Vite/Next), or a static build served via a lightweight Node/Edge runtime.
- MUST NOT depend on local filesystem paths outside its own container.

Networking:
- Exposed via HTTPS on a public URL (e.g. `https://virlife-frontend.up.railway.app`).
- Communicates with backend service(s) exclusively via HTTPS/WebSockets.
- MUST NOT access databases directly; all world interaction MUST go through the backend gateway.

Environment Variables (minimum):

- `VIRLIFE_ENV`  
  - e.g. `production`, `staging`
  - Used for environment-specific behaviour (primarily logging, not logic).

- `BACKEND_BASE_URL`  
  - The public URL for the backend gateway/API service.
  - All HTTP calls from the frontend MUST use this base URL.

- `BACKEND_WS_URL`  
  - WebSocket endpoint for live timeline/events (e.g. `wss://virlife-backend.up.railway.app/ws`).

- `TTS_ENABLED`  
  - `true` or `false`, to toggle TTS integration at runtime.

- `TTS_BASE_URL` (OPTIONAL)  
  - If TTS is provided by a separate service, its base URL.

- `APP_VERSION`  
  - String version identifier for debugging and support (not logic).

Persistence:
- The frontend service MUST NOT maintain authoritative state.
- All authoritative state (world, agents, psychology, memories) lives in the backend’s Postgres.
- The frontend MAY cache ephemeral UI state in memory but MUST tolerate restarts.

Constraints:
- No direct database connections.
- No direct Redis/Qdrant connections.
- No background jobs.
- All state changes MUST go through backend APIs in line with MASTER_SPEC and Architecture.



This architecture ensures:

- determinism in the numeric substrate  
- clean separation of concerns  
- safe and controlled use of Redis and Qdrant  
- and a clear, enforceable deployment model for Railway.