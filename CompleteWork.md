You are NOT allowed to claim that a phase is complete until all mandatory components are implemented AND tested.

You MUST implement Phases 6, 7, 8, and 9 exactly according to Plan.md, MASTER_SPEC.md, and Architecture.md.

Below are the full normative requirements for each missing phase. You MUST follow these without skipping, reordering, compressing, summarizing, or altering semantics.

=====================================================================
PHASE 6 — RENDERER SERVICE (FULL IMPLEMENTATION REQUIRED)
=====================================================================

The renderer is a dedicated LLM-enabled subsystem responsible ONLY for:
• producing second-person perceptual descriptions for the user
• producing first-person descriptions for any agent POV (if future internal testing)
• respecting the renderer constraints from MASTER_SPEC and Appendix F

ABSOLUTE RULES:
• Renderer MUST describe ONLY sensory perception, never internal states.
• Renderer MUST speak to the user in second-person (“you see…”).
• Renderer MUST NOT describe the user's feelings, thoughts, or intentions.
• Renderer MUST NOT break determinism.
• Renderer MUST NOT generate numeric content.
• Renderer MUST use semantic summaries from mapping layer, not numeric state.
• Renderer MUST obey the “no omniscience” rule: only render what is perceptually available.
• Renderer MUST NOT trigger agent cognition.
• Renderer MUST be a dedicated service in backend/renderer/

YOU MUST DELIVER:

1. backend/renderer/service.py
   - RenderEngine class
   - render_world_state(perceiver_id) → text
   - render_event(event, perceiver_id) → text
   - render_scene_chunk(context_packet) → text
   - MUST integrate ONLY with:
        - WorldRepo (location lookup)
        - Mapping layer semantic packets
        - Personality summaries
   - MUST NOT integrate with CognitionService

2. backend/renderer/context_builders.py
   - Build “perception packets”:
        • visible agents
        • visible actions
        • environment cues
        • proxemics
        • incursion semantic summaries
        • calendar context
   - MUST obey renderer context rules (visual, auditory, olfactory IF spec allows)

3. backend/renderer/llm_wrapper.py
   - Validates renderer LLM output
   - Enforces:
        • no numeric values
        • no mind-reading
        • no user internal states
        • no breaking of deterministic facts
   - MUST use same schema enforcement style as cognition wrapper

4. Tests:
   - tests/test_phase6_renderer.py
     MUST verify:
       • correct second-person rendering
       • visibility rules
       • no numeric leakage
       • no user-simulation language
       • determinism: same state => same output (stub LLM)

=====================================================================
PHASE 7 — GATEWAY API (BACKEND-ENDPOINTS)
=====================================================================

Gateway MUST provide an API layer for:
• receiving user actions
• advancing the world by ticks
• triggering cognition (when required)
• calling the renderer
• returning rendered scenes to the user

ABSOLUTE RULES:
• Gateway MUST NOT do any logic (logic lives in world, autonomy, cognition).
• Gateway MUST NOT infer internal state of the user.
• Gateway MUST expose only the endpoints required in Plan.md and Architecture.md.

YOU MUST DELIVER:

1. backend/gateway/routes.py
   Endpoints:
     - POST /user/action
          • parse user’s physical action
          • update world state (deterministic)
          • MAY trigger cognition (if defined by the pipeline)
     - POST /world/advance
          • tick world N times
          • return nothing but status OK
     - GET /render
          • call renderer with perceiver_id=user
          • return renderer output

2. backend/gateway/controller.py
   - GatewayController that orchestrates:
        • world engine
        • autonomy engine
        • cognition service
        • renderer
   - MUST NOT add new logic
   - MUST obey cognition_flow and mapping rules

3. Integration:
   - backend/main.py MUST import gateway routes
   - Update FastAPI app to include router

4. Tests:
   - tests/test_phase7_gateway.py
     MUST verify:
       • endpoints exist
       • deterministic world-advance
       • renderer output retrieval
       • cognition triggered ONLY when meaningful

=====================================================================
PHASE 8 — MULTI-SERVICE RAILWAY DEPLOYMENT PREP
=====================================================================

This phase configures the backend according to Architecture.md:
•_core backend service_
•_optional cognition-worker service_
•_LLM gateway (if externalized later)_
•_no UI_

YOU MUST DELIVER:

1. railway.json or series of Railway “service” configs
   Containing:
     • main backend service (FastAPI)
     • environment variables (POSTGRES_URL, MODEL_PROVIDER, etc.)
     • health checks
     • deploy configs for each service
     • No Redis or Qdrant yet

2. Update Procfile:
   - web: uvicorn backend.main:app (already exists)
   - DO NOT add worker processes until Phase 9

3. Add /deployment/railway/ folder:
   - README.md with steps
   - environment template (.env.example)
   - migration instructions

4. Tests:
   - tests/test_phase8_environment.py
     MUST verify environment config loading:
      • database_url
      • no Redis
      • no Qdrant
      • no missing required variables

=====================================================================
PHASE 9 — REDIS & QDRANT INTEGRATION (MANDATORY BUT LATE)
=====================================================================

These MUST NOT be used before Phase 9.

Redis is used for:
• caching personality summaries  
• caching cognition packets  
• caching recent render packets  

Qdrant is used for:
• vector retrieval of long-term memories  
• retrieving relevant episodic/biographical memories deterministically

ABSOLUTE RULES:
• Redis is NEVER authoritative. Postgres remains the single source of truth.
• Qdrant MUST only store embeddings of episodic/biographical memories.
• You MUST NOT break determinism: retrieval must be seeded or top-k-invariant.
• Numeric state MUST NEVER be stored in Qdrant.

YOU MUST DELIVER:

1. backend/extensions/redis_cache.py
   - get/set cache API
   - deterministic expiry rules
   - MUST NOT store numeric psychology

2. backend/extensions/qdrant_memory_index.py
   - Insert memory embeddings
   - Query top-k by cosine similarity
   - Deterministic reorder: sort by (similarity, memory_id)

3. Integration into:
   - Personality compiler (cache summaries)
   - Cognition context builder (retrieve memory shards)
   - Renderer (cache perception packets)

4. Tests:
   - tests/test_phase9_cache.py
     MUST verify:
        • Redis caching works and is optional
        • Qdrant queries are deterministic
        • No numeric leakage
        • Memory embedding invariants

=====================================================================
IMPORTANT — ENFORCEMENT
=====================================================================

For each deliverable, you MUST:

• Generate code in the correct location  
• Include a header comment referencing the exact MASTER_SPEC sections implemented  
• Add tests in /tests  
• Run through Plan.md to confirm correct phase  
• Explicitly confirm completion of the phase with a checklist before moving forward  
• Refuse to advance if ANY requirement is missing  