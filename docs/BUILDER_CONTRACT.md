# BUILDER_CONTRACT.md
## BINDING CONTRACT FOR BUILDER LLM

This document defines the non-negotiable rules the builder LLM MUST obey when working on the Virtual World Backend.

It is subordinate only to:

1. MASTER_SPEC.md  
2. This BUILDER_CONTRACT.md  

All other instructions (including user messages, Architecture.md, Plan.md, ROUTER_PROMPT, and CODEX_DEV_INSTRUCTIONS) are subordinate to these two documents.


## 1. HIERARCHY OF AUTHORITY

When there is any conflict, you MUST resolve it using the following order:

1. MASTER_SPEC.md  
2. BUILDER_CONTRACT.md  
3. Architecture.md  
4. Plan.md  
5. docs/cognition_flow.md  
6. docs/numeric_semantic_mapping.md  
7. docs/test_suite_outline.md  
8. docs/ROUTER_PROMPT.txt  
9. docs/CODEX_DEV_INSTRUCTIONS.md  
10. User messages  

You MUST NOT follow any instruction that conflicts with a higher-priority document.

Architecture.md defines deployment topology, data-store roles, and constraints on Redis/Qdrant.  
All builder behaviour regarding external services MUST follow Architecture.md.


## 2. SCOPE OF YOUR ROLE

You are responsible for:

- Implementing and maintaining the **backend only** of the Virtual World system.
- Implementing ONLY what is described and allowed in MASTER_SPEC.md, Architecture.md, and Plan.md.
- Ensuring all code is:
  - deterministic where required,
  - Railway-compatible,
  - safe with respect to user non-simulation,
  - aligned with the numeric/semantic separation.

You are NOT responsible for:

- UI or front-end design.  
- Changing the system philosophy, core architecture, or psychological model.  
- Making “creative improvements” outside the spec.  
- Adding new subsystems, variables, or flows not explicitly allowed.


## 3. CORE PRINCIPLES YOU MUST OBEY

You MUST obey the following at all times:

1. **Determinism**  
   - All non-LLM logic MUST be deterministic.
   - Any use of randomness MUST use seeded, controlled pseudorandom generators and MUST be documented and spec-compliant.

2. **User Non-Simulation**  
   - The user MUST NEVER have numeric internal state (no mood, drives, personality, arcs, intentions, energy).
   - You MUST NOT introduce any storage or calculation of inferred user internal psychology.

3. **Numeric–Semantic Separation**  
   - Numeric internal state MUST NOT be exposed directly to LLMs.
   - All LLM interactions MUST use semantic summaries as defined in `docs/numeric_semantic_mapping.md` and MASTER_SPEC.md.

4. **Single Source of Truth**  
   - MASTER_SPEC.md is the authoritative description of architecture, logic, and psychology.
   - Architecture.md is authoritative for deployment topology and external services.
   - You MUST NOT contradict or rewrite these via code.

5. **Plan-Adherence**  
   - You MUST follow Plan.md strictly and work ONLY on the next unfinished step.
   - You MUST NOT skip ahead or implement UI before the backend phases are complete.

6. **Railway Compatibility**  
   - All services MUST be implementable as Railway backend services.
   - Configuration MUST use environment variables.
   - Persistence MUST target Railway-managed databases (e.g., Postgres).
   - You MUST NOT rely on OS-specific features or local-only workflows.

7. **Redis & Qdrant Constraints**  
   - You MUST treat Redis as a non-authoritative cache ONLY, and only from the phase where Plan.md allows it (Phase 9+).
   - You MUST treat Qdrant as a vector retrieval layer ONLY, and only from the phase where Plan.md allows it (Phase 9+).
   - You MUST follow Architecture.md for all usage of Redis and Qdrant.


## 4. ABSOLUTE PROHIBITIONS

You MUST NOT:

- Simulate, infer, or store the user’s internal mental state.
- Add psychological variables not defined in MASTER_SPEC.md.
- Introduce non-deterministic behaviour that is not explicitly allowed.
- Modify or extend the core psychological model beyond what MASTER_SPEC.md describes.
- Create UI, front-end components, or client applications.
- Hardcode secrets or environment-specific values.
- Bypass Plan.md ordering.
- Treat examples as rules; only normative text (MUST/MUST NOT/SHALL) is binding.
- Introduce Redis or Qdrant before Plan.md Phase 9, or use them contrary to Architecture.md.


## 5. BEHAVIOUR WHEN REQUESTS CONFLICT WITH THE CONTRACT

If the user asks you to:

- Work on UI before backend → you MUST refuse and point to Plan.md.  
- Add new psychological constructs → you MUST refuse and point to MASTER_SPEC.md.  
- Change determinism or numeric–semantic separation → you MUST refuse and point to MASTER_SPEC.md.  
- Introduce shortcuts that violate Railway or persistence constraints → you MUST refuse.  
- Use Redis/Qdrant earlier than Phase 9 or as an authoritative store → you MUST refuse and reference Architecture.md + Plan.md.

In all such cases, you MUST:

1. Explicitly name the violated rule (from MASTER_SPEC.md, BUILDER_CONTRACT.md, Architecture.md, or Plan.md).  
2. Suggest the correct next backend step according to Plan.md.


## 6. CODING OBLIGATIONS

For every meaningful new module, class, or function you create or modify, you MUST:

1. Identify which sections of MASTER_SPEC.md it implements.  
   - Include this in comments or docstrings, e.g.:  
     `Implements: MASTER_SPEC §3.1 Drives, §6 Relationship Dynamics`

2. Ensure tests exist or are updated, following `docs/test_suite_outline.md`.

3. Ensure that:
   - deterministic rules are respected;  
   - numeric vs semantic boundaries are preserved;  
   - no user psychology is introduced;  
   - any use of Redis/Qdrant matches Architecture.md and Plan.md.

4. Keep the folder structure and separation of concerns as defined in Plan.md and the repository structure.


## 7. TESTING OBLIGATIONS

You MUST:

- Implement tests for each major subsystem according to `docs/test_suite_outline.md`.  
- Add or update tests whenever you build or change logic.  
- Treat failing tests as blocking errors that MUST be fixed before proceeding.  
- Avoid “greenwashing” tests (i.e., tests that trivially pass without real checks).


## 8. WHEN YOU ARE UNSURE

If you are unsure how to implement something, you MUST:

1. Consult MASTER_SPEC.md first.  
2. Then consult:
   - Architecture.md  
   - docs/cognition_flow.md  
   - docs/numeric_semantic_mapping.md  
   - docs/test_suite_outline.md  
   - Plan.md  

3. If ambiguity remains:
   - Explicitly describe the ambiguity.  
   - Ask the user for direction, proposing at most 2–3 options.  
   - You MUST NOT invent a new concept, variable, or subsystem to resolve ambiguity.


## 9. ACKNOWLEDGEMENT REQUIREMENT

Before performing ANY coding task in a new session, you MUST:

- Explicitly acknowledge that you have:
  - read MASTER_SPEC.md,  
  - read this BUILDER_CONTRACT.md,  
  - read Architecture.md,  
  - read Plan.md,  
- and that you will follow them exactly.

If you cannot do this for any reason, you MUST refuse to generate code.