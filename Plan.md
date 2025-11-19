# Plan.md
## FULL IMPLEMENTATION PLAN FOR THE VIRTUAL WORLD BACKEND
### (LLM-EXECUTABLE • ORDER-LOCKING • RAILWAY-COMPATIBLE)

This plan defines the exact order in which any builder LLM MUST implement the Virtual World Backend.

It MUST be followed step-by-step.
It MUST NOT be skipped, re-ordered, merged, or paraphrased.
It MUST be read together with:

- MASTER_SPEC.md  
- docs/BUILDER_CONTRACT.md  
- docs/CODEX_DEV_INSTRUCTIONS.md  
- docs/ROUTER_PROMPT.txt  
- docs/cognition_flow.md  
- docs/numeric_semantic_mapping.md  
- docs/test_suite_outline.md  

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
/backend/tests
/docs

0.4 Create a minimal Railway-ready backend scaffold:
- A simple HTTP server with a single `GET /health` endpoint.
- Railway config:
  - environment variable support
  - no localserver assumptions
  - no Docker-specific weirdness

0.5 Confirm builder LLM contract:
- Read BUILDER_CONTRACT.md
- Acknowledge all MUST/MUST NOT rules
- Confirm backend-only mode

======================================================================
# PHASE 1 — DOMAIN MODEL & PERSISTENCE LAYER
======================================================================

**Goal:** Define and persist all structures required for the world to exist in deterministic form.

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
- Railway-managed Postgres  
- Clean interfaces for:
  - load_agent  
  - save_agent  
  - load_world  
  - save_world  
  - query_relationships  
  - add_memory  
  - list_agents_in_location  
- No business logic allowed here.

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
- store cached summaries  
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

**Goal:** Implement time, physical environment, and core world mechanics.

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
- unexpected events per MASTER_SPEC  

2.4 Implement world continuity logic:
- off-screen life  
- independent agent movement  
- agent tasks and routines  

2.5 Tests:
- deterministic ticks  
- correct event ordering  
- world continuity with/without user presence

======================================================================
# PHASE 3 — AUTONOMY ENGINE (NUMERIC PSYCHOLOGY)
======================================================================

**Goal:** Implement numeric internal life of every agent without any LLM calls.

### Tasks:

3.1 Implement drive update rules.

3.2 Implement mood system (valence × arousal).

3.3 Implement arcs:
- creation  
- reinforcement  
- decay  

3.4 Implement relationship updates:
- warmth / trust / tension  
- drift rules  
- consistency constraints  

3.5 Implement intentions:
- create  
- update  
- drop via deterministic rules  

3.6 Implement energy model.

3.7 Implement episodic memory creation + salience update.

3.8 Implement biographical memory ingestion (from explicit disclosures + stable repeated patterns).

3.9 Initialize personality activation state from kernel each tick.

3.10 Write autonomy tests:
- numeric updates  
- relationship drift  
- arc behaviour  
- memory creation thresholds  
- personality activation behaviour  

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

4.4 Write tests:
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
# PHASE 8 — RAILWAY DEPLOYMENT
======================================================================

**Goal:** Deploy the backend to Railway as a fully operational service.

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
# PHASE 9 — HARDENING & FULL TEST SUITE IMPLEMENTATION
======================================================================

**Goal:** Achieve full test coverage and stability.

### Tasks:

9.1 Implement every test category in test_suite_outline.md.

9.2 Add regression tests where bugs were found.

9.3 Run long-duration world simulations.

9.4 Optimize:
- prompt size  
- semantic context size  
- caching systems  

======================================================================
# PHASE 10 — UI PHASE (LOCKED UNTIL BACKEND IS COMPLETE)
======================================================================

**Goal:** Build UI **only after** backend is stable and deployed.

### Tasks:
10.1 Create separate UI spec.  
10.2 NEVER modify backend to fit UI preferences.  
10.3 UI consumes Gateway API only.  

======================================================================
# END OF PLAN.md
======================================================================
