# Plan.md
## FULL IMPLEMENTATION PLAN FOR THE VIRTUAL WORLD BACKEND
### (LLM-EXECUTABLE • ORDER-LOCKING • RAILWAY-COMPATIBLE)

This plan defines the exact order in which any builder LLM MUST implement the Virtual World Backend.

It MUST be followed step-by-step.  
It MUST NOT be skipped, re-ordered, merged, or paraphrased.  
It MUST be read together with:

- MASTER_SPEC.md — core world architecture, psychology, logic, determinism, and user rules.  
- Architecture.md — system topology, data stores (Postgres, Redis, Qdrant), and when/how they MAY be used.  
- docs/BUILDER_CONTRACT.md — mandatory development behaviour.  
- docs/CODEX_DEV_INSTRUCTIONS.md — standing coding guidelines.  
- docs/ROUTER_PROMPT.txt — task classification and routing rules.  
- docs/cognition_flow.md — full cognition pipeline.  
- docs/numeric_semantic_mapping.md — numeric → semantic mapping rules.  
- docs/test_suite_outline.md — required test categories.  

This is the **canonical build order**.  
Every coding session MUST begin by reading this file.

No UI implementation is allowed until Phase 10.

======================================================================
# PHASE 0 — BOOTSTRAP & REPO HYGIENE
======================================================================

**Goal:** Prepare the repository with all required documents and ensure the builder LLM has correct behavioural constraints.

### Tasks:

0.1 Place the following at repo root:
- MASTER_SPEC.md  
- Architecture.md  
- Plan.md  

0.2 Place the following under `/docs`:
- BUILDER_CONTRACT.md  
- CODEX_DEV_INSTRUCTIONS.md  
- ROUTER_PROMPT.txt  
- cognition_flow.md  
- numeric_semantic_mapping.md  
- test_suite_outline.md  

0.3 Create base folder structure:

/backend  
/backend/world  
/backend/autonomy  
/backend/cognition  
/backend/renderer  
/backend/personality  
/backend/persistence  
/backend/mapping  
/backend/gateway  
/backend/config  
/backend/utils  
/tests  
/docs  
/data  

0.4 Create a minimal Railway-ready backend scaffold:
- A simple HTTP server with a single `GET /health` endpoint.
- Railway config:
  - environment variable support
  - no localserver assumptions
  - no Docker-specific weirdness

0.5 Confirm builder LLM contract:
- Read MASTER_SPEC.md  
- Read Architecture.md  
- Read BUILDER_CONTRACT.md  
- Read Plan.md  
- Acknowledge all MUST/MUST NOT rules  
- Confirm backend-only mode  

======================================================================
# PHASE 1 — DOMAIN MODEL & PERSISTENCE LAYER
======================================================================

**Goal:** Define and persist all structures required for the world to exist in deterministic form.

Postgres IS the authoritative state store.  
Redis and Qdrant MUST NOT be introduced before Phase 9. They are optimisation layers only.

### Tasks:

1.1 Define agent schema including:
- identity  
- personality kernel  
- personality summaries  
- domain summaries  
- cached context fragments  
- drives  
- mood  
- arcs  
- relationships  
- intentions  
- energy  
- episodic memories  
- biographical memories  
- location  
- status flags  
- last cognition timestamp (cooldown)  

1.2 Define world schema including:
- time  
- tick  
- locations  
- objects  
- event queue  

1.3 Implement persistence layer:
- Railway-managed Postgres ONLY  
- Clean interfaces for:
  - load_agent  
  - save_agent  
  - load_world  
  - save_world  
  - query_relationships  
  - add_memory  
  - list_agents_in_location  
- No business logic allowed here.  
- NO Redis, NO Qdrant, NO other stores in this phase.

1.4 Write persistence tests:
- CRUD tests for all state  
- bounds enforcement  
- schema validation  
- persistence across restart  

======================================================================
# PHASE 1.5 — PERSONALITY COMPILER & CHARACTER INITIALIZATION
======================================================================

**Goal:** Build the entire Personality Compiler subsystem and initialize every agent’s personality.

This phase MUST precede Autonomy Engine development.

### Tasks:

1.5.1 Implement Personality Template Library:
- Load template definitions from structured files.  
- Provide deterministic merge of templates.  

1.5.2 Implement Personality Compiler:
- template mix → personality kernel  
- kernel → stable personality summary  
- kernel → domain summaries  
- kernel + state → dynamic activation packet  
- store cached summaries in Postgres  
- forbid raw fingerprint text from being passed to LLM  

1.5.3 Implement Fingerprint Interpreter (optional):
- For agents with fingerprints (e.g. Rebecca),  
  convert fingerprint JSON → weighted modifiers → kernel adjustments → summary augmentations.  

1.5.4 Implement Character Initialization Pipeline:
- For each agent in cast list:
  - assign template mixture  
  - compute kernel  
  - compute summaries  
  - store all fields in persistence  
  - build initial relationship graph  
  - build initial biographical memory pack  

1.5.5 Write tests for Personality Compiler:
- kernel determinism  
- summary determinism  
- caching behaviour  
- integration with cognition & renderer context building  
- fingerprint interpretation (if applicable)  

======================================================================
# PHASE 2 — WORLD ENGINE
======================================================================

**Goal:** Implement time, physical environment, core world mechanics, calendars, and unexpected events.

### Tasks:

2.1 Implement global clock + tick system.

2.2 Implement location + movement model:
- rooms  
- adjacency rules  
- presence lists  

2.3 Implement event system:
- world events  
- scheduled events  
- asynchronous events  
- unexpected events per MASTER_SPEC (incursions derived from world state)

2.4 Implement world continuity logic:
- off-screen life  
- independent agent movement  
- agent tasks and routines  

2.5 Implement Calendar and Obligation System:
- Create world-state structures for agent calendars, obligations, and long-term plans.
- Implement deterministic schedule evaluation per tick.
- Generate world events when:
  - an obligation becomes due,
  - a scheduled event begins,
  - a preparatory period begins,
  - a commitment is missed.
- Ensure calendars are stored as world data, NOT as drives, mood, relationships, or arcs.

2.6 Implement Unexpected Event (Incursion) Framework:
- Ensure unexpected events arise from:
  - the world clock,
  - agents' calendars and routines,
  - environmental processes,
  - communication channels.
- Represent incursions as ordinary world events whose “unexpectedness” is from the perceiver’s POV.
- Do NOT introduce special-case psychology for incursions.
- Do NOT enumerate a finite set of incursion “types.”

2.7 Tests:
- deterministic ticks  
- correct event ordering  
- world continuity with/without user presence  
- correctness of calendar event generation  
- correctness of unexpected event (incursion) generation from world state  

======================================================================
# PHASE 3 — AUTONOMY ENGINE (NUMERIC PSYCHOLOGY) [COMPLETED]
======================================================================

**Goal:** Implement numeric internal life of every agent without any LLM calls.

### Tasks:

3.1 Implement drive update rules. [DONE]

3.2 Implement mood system (valence × arousal). [DONE]

3.3 Implement arcs: [DONE]
- creation  
- reinforcement  
- decay  

3.4 Implement relationship updates: [DONE]
- warmth / trust / tension  
- drift rules  
- consistency constraints  

3.5 Implement intentions: [DONE]
- create  
- update  
- drop via deterministic rules  

3.6 Implement energy model. [DONE]

3.7 Implement episodic memory creation + salience update. [DONE]

3.8 Implement biographical memory ingestion (from explicit disclosures + stable repeated patterns). [DONE]

3.9 Initialize personality activation state from kernel each tick. [DONE]

3.10 Ensure that: [DONE]
- calendar/obligation events feed into decision pressure and intention logic,
- unexpected events influence drives, mood, arcs, and relationships via deterministic rules,
- NO new psychological variables are created for calendars or incursions.

3.11 Write autonomy tests: [DONE]
- numeric updates  
- relationship drift  
- arc behaviour  
- memory creation thresholds  
- personality activation behaviour  
- calendar/obligation influence on intentions  
- unexpected-event influence on decision pressure  

======================================================================
# PHASE 4 — NUMERIC ↔ SEMANTIC MAPPING LAYER
======================================================================

**Goal:** Implement the mapping layer between numeric substrate and LLM semantic packets.

### Tasks:

4.1 Implement numeric → semantic mapping for:
- drives  
- mood  
- relationship edges  
- arcs  
- energy  
- intentions  
- memory snippets  

4.2 Integrate personality summaries:
- stable personality summary  
- domain summaries  
- dynamic activation packet  

4.3 Ensure NO raw numeric values ever reach LLM.

4.4 Ensure that:
- calendar and obligation information is exposed semantically as world facts,
- unexpected events are exposed semantically as perceptual interruptions or context.

4.5 Write tests:
- mapping determinism  
- bucket coverage  
- no numeric leakage into LLM payloads  

======================================================================
# PHASE 5 — COGNITION SERVICE WRAPPER
======================================================================

**Goal:** Implement full cognition pipeline as described in cognition_flow.md.

### Tasks:

5.1 Implement salience calculation.

5.2 Implement meaningfulness computation (M formula).

5.3 Implement cognition eligibility logic (threshold, cooldown, triviality rules).

5.4 Implement CognitionContext builder:
- semantic mood  
- semantic drives  
- semantic relationships  
- semantic arcs  
- memory snippets  
- intentions  
- personality summaries (stable + domain + activation)  
- event context  
- relevant calendar/obligation context  
- relevant unexpected-event context (when meaningful)

5.5 Implement LLM wrapper:
- use reasoning model (not adult model)  
- enforce schema  
- validate output  

5.6 Implement numeric update mapping:
- stance_shifts → numeric deltas  
- intention_updates → numeric deltas  

5.7 Tests:
- cognition triggering  
- correct context packets  
- schema validation  
- determinism of post-cognition numeric updates  
- correct inclusion of calendar/obligation and unexpected-event context when appropriate  

======================================================================
# PHASE 6 — RENDERER SERVICE WRAPPER
======================================================================

**Goal:** Implement user-facing rendering of perceptual experience.

### Tasks:

6.1 Implement Perception Packet builder:
- who is visible  
- what is happening  
- what changed since last render  
- second-person POV ONLY  

6.2 Implement dual-model renderer architecture:
- reasoning model for non-sexual scenes  
- adult-capable model for sexual scenes  
- routing logic based on event classification  

6.3 Build RendererContext:
- stable personality summary  
- relevant domain summaries  
- dynamic activation packet  
- perception snapshot  
- event context  

6.4 Implement renderer LLM wrapper:
- schema enforcement  
- perception-only rules  
- no invented events  
- no narration of user internal states  

6.5 Tests:
- no internal state leakage  
- correct routing (normal model vs adult model)  
- deterministic mapping of renderer classification  

6.6 Integrate Unexpected Event Rendering:
- Ensure renderer presents unexpected events (incursions) as perceptual interruptions (e.g., knocks, arrivals, messages).
- Ensure renderer follows APPENDIX I for how incursions are expressed.
- Ensure renderer surfaces calendar/obligation context through perception (e.g., clocks, calendars, dialogue, body language).
- Ensure renderer does NOT assign internal psychological states unless coming from cognition output.

======================================================================
# PHASE 7 — GATEWAY API
======================================================================

**Goal:** Expose the backend as a Railway-ready HTTP API that the UI will use later.

### Tasks:

7.1 Implement API endpoints:
- POST /user/action  
- POST /world/advance  
- GET /render  

7.2 Integrate:
- World Engine  
- Autonomy Engine  
- Cognition Service  
- Renderer Service  

7.3 Security rules:
- user identity verification  
- no UI logic here  
- no session history stored in API  

7.4 Tests:
- end-to-end scenario tests  
- world-state mutation tests  
- rendering correctness  

======================================================================
# PHASE 8 — RAILWAY DEPLOYMENT (POSTGRES-ONLY)
======================================================================

**Goal:** Deploy the backend to Railway as a fully operational service using Postgres as the ONLY data store.

Redis and Qdrant MUST NOT be wired in this phase.  
They belong to the optimisation/memory phase (Phase 9).

### Tasks:

8.1 Prepare Railway project (service + DB + env vars).

8.2 Implement:
- environment variable reading  
- connection pooling  
- logging  

8.3 Deploy service.

8.4 Smoke test via Railway URL:
- /health  
- basic actions  
- cognition call  
- renderer call  

======================================================================
# PHASE 9 — HARDENING, CACHING, AND VECTOR MEMORY
======================================================================

**Goal:** Achieve full test coverage, stability, and introduce Redis + Qdrant as optimisation and memory layers without changing core logic semantics.

### Tasks:

9.1 Implement every test category in `docs/test_suite_outline.md`.

9.2 Add regression tests where bugs were found.

9.3 Run long-duration world simulations.

9.4 Optimize:
- prompt size  
- semantic context size  


### 9.5 Introduce Redis caching layer (NON-AUTHORITATIVE CACHE ONLY)

- Create a Redis service in the same Railway project.
- Add `REDIS_URL` (or equivalent) to backend env vars.

Implement caching modules for:

- LLM response caching (optional, safe keys only).  
- renderer perception context (last render snapshots, small TTL).  
- cognition cooldown and salience caches.  
- recent unexpected-event triggers (short TTL) for performance-only optimisation.

Constraints:

- Redis is NEVER the source of truth for world or psychology state.  
- On Redis failure, the system falls back to Postgres-only behaviour.  
- Core logic semantics MUST remain identical with or without Redis.

Add tests:

- cache hit/miss behaviour  
- correctness of fallbacks  
- determinism of behaviour with and without cache  


### 9.6 Introduce Qdrant vector memory layer (EPISODIC + BIOGRAPHICAL RETRIEVAL)

- Create a Qdrant service in the same Railway project (custom container).  
- Add env vars:
  - `QDRANT_URL`
  - `QDRANT_API_KEY` (if auth enabled)

Implement embedding + vector storage for:

- episodic memory summaries  
- episodic memories that originated as unexpected events  
- biographical memory summaries  
- (optionally) stable personality summaries  

Integrate Qdrant into memory retrieval:

- semantic similarity search combined with recency + salience from Postgres.  

Constraints:

- Postgres remains the authoritative store for all memories.  
- Qdrant is used ONLY for retrieval ranking and similarity.  
- No unique information MUST exist only in Qdrant.  

Add tests:

- retrieval quality (sanity checks).  
- deterministic retrieval ordering given fixed embeddings.  
- failover behaviour if Qdrant is unavailable.  

=====================================================================
PHASE 10 — UI CLIENT (TEXT-ONLY, VISUALLY RICH, WORLD-FAITHFUL)
=====================================================================

STATUS: NOT STARTED

This phase defines the complete implementation plan for the UI client, based on:

- MASTER_SPEC.md
- Architecture.md
- UI_SPEC.md (Virtual World UI Specification)
- Plan.md (this file)
- docs/BUILDER_CONTRACT.md
- docs/ROUTER_PROMPT.txt
- docs/ROUTER_PROMPT_UI.txt (UI router, optional but recommended)
- docs/test_suite_outline.md

The UI MUST:
- be text-only but visually rich,
- be emotionally neutral,
- treat intimacy as normal reality (no modes),
- never simulate the user’s internal state,
- never expose numeric psychology,
- respect backend determinism and constraints.

The UI MUST be built in SEQUENTIAL SUBPHASES.
The Builder LLM MUST NOT skip, merge, or reorder steps.

---------------------------------------------------------------------
10.0 PRECONDITIONS (MUST BE TRUE BEFORE STARTING)
---------------------------------------------------------------------

The Builder LLM MUST verify that:

1. Phases 0–9 are COMPLETE and tests are passing.
2. The backend exposes stable HTTP and WebSocket endpoints for:
   - world/session snapshot,
   - timeline events,
   - user actions,
   - phone/notifications,
   - TTS control (if applicable),
   - any existing endpoints required by UI_SPEC.md.
3. UI_SPEC.md exists at the repository root (or /docs/) and is the latest version.
4. There is a clear environment configuration for FRONTEND_BASE_URL, BACKEND_BASE_URL, and any TTS / WebSocket URLs.
5. No backend changes are required except:
   - adding non-breaking UI-related endpoints already anticipated by MASTER_SPEC / Architecture.

If preconditions are not met, Builder MUST stop and report, NOT proceed.

---------------------------------------------------------------------
10.1 CHOOSE AND INITIALISE UI FRAMEWORK
---------------------------------------------------------------------

Goal: Create the UI project skeleton.

Requirements:

1. Use a modern SPA framework (e.g. React with Vite, Next.js in SPA mode, or equivalent) that:
   - supports WebSockets,
   - supports modular components,
   - can be deployed on Railway or compatible platform.

2. Create a `frontend/` directory (or similar, defined in Architecture.md) containing:
   - main entry point (e.g. `src/main.tsx` or `src/index.tsx`),
   - component directories (`src/components`, `src/views`),
   - state management (`src/state`),
   - API client module (`src/api`).

3. Integrate a minimal design system:
   - a base typography scale,
   - colour tokens (neutral, non-emotional),
   - spacing tokens,
   - layout primitives (container, column, row),
   - no image-based assets.

4. Add basic routing if needed (single route is acceptable to start; most UI lives in one screen).

5. Add initial tests:
   - basic render test for root app component,
   - CI command (e.g. `npm test` or `pnpm test`) wired into existing CI.

Builder MUST map this subphase to UI_SPEC.md sections 0–4 (global philosophy, timeline, design).

---------------------------------------------------------------------
10.2 IMPLEMENT TIMELINE VIEW (READ-ONLY, WIRED TO MOCK DATA)
---------------------------------------------------------------------

Goal: Implement the Timeline UI components based on UI_SPEC.md, initially with mock data.

Requirements:

1. Create a `TimelineView` component that:
   - renders a vertical list of MessageCards,
   - supports scrollback,
   - supports anchoring at the bottom when at the end,
   - pauses auto-scroll when user scrolls up.

2. Implement `MessageCard` component types:
   - PerceptionBlock,
   - CharacterDialogue,
   - UserDialogue,
   - SystemLine (incursions, notifications),
   - PhoneEchoLine.

3. Implement speaker labels and message types:
   - clear, consistent speaker label for characters,
   - second-person perception blocks with distinct styling,
   - user messages visually distinct (e.g. alignment/frame),
   - system lines minimal and unobtrusive.

4. Implement visual hierarchy:
   - typography hierarchy per UI_SPEC.md,
   - spacing rules,
   - neutral colour tokens,
   - no images or avatars.

5. Use mock data (static JSON or fixtures) to verify:
   - multi-character scenes,
   - interleaved perception and dialogue,
   - long sequences.

6. Add unit tests:
   - speaker attribution correctness,
   - type-based styling (perception vs dialogue vs system),
   - scroll behaviour (auto-scroll only when at bottom).

Builder MUST comply with UI_SPEC.md sections 5, 6, 11 and 14 for this subphase.

---------------------------------------------------------------------
10.3 CONNECT TIMELINE TO BACKEND (HTTP + WEBSOCKET)
---------------------------------------------------------------------

Goal: Replace mock data with real backend data.

Requirements:

1. Implement an `ApiClient` module that:
   - fetches initial snapshot and recent timeline (HTTP),
   - opens a WebSocket connection for live events.

2. Define TypeScript/JS interfaces that match backend payloads:
   - timeline event structure,
   - perception vs dialogue vs system fields,
   - speaker identity,
   - timestamps.

3. Implement state management:
   - store timeline in a central store (e.g. React context, Zustand, Redux),
   - append incoming events,
   - paginate older messages on demand.

4. Implement reconnection logic:
   - on WebSocket disconnect, show neutral “Reconnecting…” banner,
   - on reconnect, fetch missed events and merge deterministically.

5. Tests:
   - mocked HTTP + WebSocket tests,
   - deterministic ordering of events,
   - reconnection and catching up.

Builder MUST NOT:
   - expose numeric psychology,
   - simulate user internal state,
   - modify text from backend.

---------------------------------------------------------------------
10.4 IMPLEMENT INPUT BAR AND USER ACTIONS
---------------------------------------------------------------------

Goal: Allow the user to speak/act into the world.

Requirements:

1. Implement an `InputBar` component:
   - text entry,
   - send button,
   - optional keyboard shortcuts (Enter to send).

2. Wire it to backend:
   - POST/WS message for user utterances or actions,
   - immediate optimistic echo *or* conservative echo after backend confirmation (Architecturally defined; choose and document).

3. Visual representation:
   - user’s own messages rendered via UserDialogue MessageCard,
   - NO rewriting of text.

4. Tests:
   - user input sends the correct payload,
   - messages appear in timeline,
   - failure handling (e.g. transient error message, retry option).

Builder MUST ensure all user actions align with MASTER_SPEC user non-simulation rule and UI_SPEC.

---------------------------------------------------------------------
10.5 IMPLEMENT PHONE OVERLAY AND APPS (PHASE 1)
---------------------------------------------------------------------

Goal: Implement the phone overlay and core apps in a minimal but correct form.

Requirements:

1. Implement Phone overlay:
   - open/close transitions,
   - dimmed background,
   - panel layout.

2. Implement core apps in text-only form:
   - Messages (threads of in-world SMS/IM),
   - Calendar (events list and details),
   - Notifications (basic list).

3. Wire to backend:
   - endpoints for retrieving phone data (messages, calendar, notifications),
   - endpoints for creating user-driven events where permitted (e.g. user adds calendar entry).

4. Ensure world continuity:
   - world events continue in the background,
   - urgent events produce inline alert inside phone overlay.

5. Tests:
   - opening/closing phone does not stop timeline,
   - notifications appear correctly,
   - phone UI behaves as defined in UI_SPEC.

Later expansions (Email, Social, Banking, etc.) MAY be deferred to Phase 10.x, but the scaffolding MUST follow UI_SPEC.

---------------------------------------------------------------------
10.6 IMPLEMENT TTS INTEGRATION
---------------------------------------------------------------------

Goal: Implement optional text-to-speech according to UI_SPEC.

Requirements:

1. Integrate a TTS layer:
   - may use browser API or configured backend TTS service,
   - MUST be optional.

2. Implement TTS queue:
   - perception and dialogue enqueued,
   - user messages and phone messages optional based on settings.

3. Implement interruption rules:
   - high-priority events interrupt,
   - normal-priority content queues.

4. Implement user controls:
   - mute/unmute,
   - replay last line,
   - clear queue,
   - speed control,
   - toggles per UI_SPEC.

5. Tests:
   - queue ordering,
   - interruption behaviour,
   - control behaviour,
   - no summarisation or rephrasing.

---------------------------------------------------------------------
10.7 HANDLE CONCURRENCY, SCENE FLOW, AND INTERACTION DENSITY
---------------------------------------------------------------------

Goal: Make the UI robust under high-density and multi-character scenes.

Requirements:

1. Implement internal Scene Flow tracking:
   - based on backend location, time, and context signals,
   - used only for auto-scroll and grouping, never labelled visibly.

2. Implement Interaction Density tracking:
   - message rate,
   - number of participants,
   - used to adjust UI pacing (auto-scroll, minor layout decisions).

3. Improve timeline behaviour under high density:
   - ensure clarity of who speaks,
   - ensure perception vs dialogue separation,
   - ensure auto-scroll feels stable.

4. Tests:
   - concurrency scenarios (multiple characters talking),
   - long (100–300 message) sequences,
   - combination with phone overlay and TTS.

---------------------------------------------------------------------
10.8 ACCESSIBILITY & LONG-SESSION OPTIMISATION
---------------------------------------------------------------------

Goal: Make the UI safe and pleasant for long, frequent use.

Requirements:

1. Implement accessibility features:
   - font scaling,
   - contrast options,
   - keyboard navigation,
   - screen reader labels.

2. Respect system “reduce motion” settings:
   - disable micro-animations when requested.

3. Long-session usability:
   - ensure CPU/GPU use stays moderate over many hours,
   - handle large timelines without performance degradation,
   - manage pagination and memory.

4. Tests:
   - accessibility checks (linting, snapshots),
   - performance tests for large timelines.

---------------------------------------------------------------------
10.9 RAILWAY DEPLOYMENT FOR FRONTEND + FINAL UI POLISH
---------------------------------------------------------------------

Goal: Make the UI production-ready AND deploy it as a dedicated Railway service.

Requirements:

1. CREATE FRONTEND RAILWAY SERVICE

   - Create a Railway service (e.g. `virlife-frontend`) dedicated to the UI.
   - Configure build and start commands (e.g. `npm install && npm run build`, `npm run preview` or equivalent) according to the chosen framework.
   - Ensure the service runs as a pure frontend service:
     - no direct DB access,
     - no direct Redis/Qdrant access,
     - all calls go via `BACKEND_BASE_URL` and `BACKEND_WS_URL`.

2. ENVIRONMENT VARIABLES

   The frontend Railway service MUST define at least:

   - `VIRLIFE_ENV` → `production`
   - `BACKEND_BASE_URL` → public HTTP(S) URL of the backend gateway.
   - `BACKEND_WS_URL` → public WebSocket URL of the backend timeline/events.
   - `TTS_ENABLED` → `true` or `false` depending on whether TTS is wired.
   - `TTS_BASE_URL` → if a separate TTS service exists.
   - `APP_VERSION` → current frontend version string.

   The Builder MUST document these in `FRONTEND_README.md`.

3. BUILD AND DEPLOY PIPELINE

   - Add a `frontend` build script (e.g. `npm run build`) that produces a production bundle.
   - Wire CI to:
     - run frontend unit tests,
     - run frontend integration tests (at least smoke tests),
     - build the frontend artifact.
   - Ensure Railway uses the correct Node version and build commands.
   - Ensure static assets are served correctly by the chosen framework.

4. E2E VALIDATION FLOWS (AGAINST RAILWAY DEPLOYMENT)

   The Builder MUST validate, against the live Railway deployment, at least:

   - Quiet day scenario:
     - User connects to frontend URL.
     - World snapshot loads.
     - Timeline renders.
     - User can send a message.
     - Responses appear in real time.

   - High-stakes emotional scenario:
     - Backend runs a pre-defined test script or scenario.
     - Frontend shows multi-character dialogue clearly.
     - Interruptions and incursion markers appear correctly.
     - No emotional distortion is introduced by UI.

   - Long intimate interaction (100+ messages):
     - User stays in a long, interactive, intimate scene.
     - Timeline remains readable.
     - Speaker labels stay clear.
     - No special UI mode is applied.
     - Auto-scroll behaves correctly.

   - Mixed phone and world interaction:
     - Phone overlay opens/closes.
     - Notifications appear inline on timeline.
     - World continues while phone is open.
     - Urgent events appear inside phone and timeline.

5. DOCUMENTATION

   - Create `FRONTEND_README.md` that explains:
     - how to run the UI locally,
     - how to deploy to Railway,
     - required environment variables and their meaning,
     - how the UI obeys UI_SPEC.md and MASTER_SPEC.md.

   - Update `Architecture.md` to confirm the frontend Railway service exists and is correctly integrated.

6. NON-NEGOTIABLE CONSTRAINTS

   - Frontend MUST NOT access Postgres, Redis, or Qdrant directly.
   - Frontend MUST NOT violate UI_SPEC.md’s neutrality, text-only, and non-mode rules.
   - Frontend MUST NOT change backend logic.
   - Any required backend endpoint adjustments MUST remain non-breaking and conform to Architecture and MASTER_SPEC.

When this subphase is complete, and:

- all frontend tests pass,
- deployment to Railway is stable,
- the UI behaves as defined in UI_SPEC.md,

…then Phase 10 MAY be marked COMPLETE.

======================================================================
# END OF PLAN.md
======================================================================