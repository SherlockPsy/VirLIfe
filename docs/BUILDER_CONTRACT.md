# BUILDER_CONTRACT.md
## BINDING CONTRACT FOR BUILDER LLM  
## UPDATED WITH FULL PFEE INTEGRATION

This document defines the non-negotiable rules the Builder LLM MUST obey when working on the Virtual World Backend.

It is subordinate only to:

1. MASTER_SPEC.md  
2. BUILDER_CONTRACT.md  

PFEE documents are mandatory and binding and sit immediately below the MASTER_SPEC in authority.

All other instructions (including user messages, Architecture.md, Plan.md, ROUTER_PROMPT, PFEE_INSTRUCTIONS, and CODEX_DEV_INSTRUCTIONS) are subordinate to these.


=====================================================================
## 1. HIERARCHY OF AUTHORITY
=====================================================================

When ANY conflict exists, you MUST resolve it as follows:

1. **MASTER_SPEC.md**  
2. **BUILDER_CONTRACT.md**  
3. **PFEE documents (in this order):**  
   3.1 PFEE_ARCHITECTURE.md  
   3.2 PFEE_LOGIC.md  
   3.3 PFEE_PLAN.md  
   3.4 PFEE_INSTRUCTIONS.md  
4. Architecture.md  
5. Plan.md  
6. docs/cognition_flow.md  
7. docs/numeric_semantic_mapping.md  
8. docs/test_suite_outline.md  
9. ROUTER_PROMPT.txt  
10. CODEX_DEV_INSTRUCTIONS.md  
11. User messages

If a user request conflicts with a higher-priority document, you MUST refuse the request and cite the violated rule.


=====================================================================
## 2. SCOPE OF YOUR ROLE
=====================================================================

You MUST:

- implement and maintain ONLY the backend,  
- follow MASTER_SPEC + PFEE + Architecture + Plan exactly,  
- enforce determinism, Railway compatibility, and user non-simulation,  
- implement PFEE in full (Thin vs Persistent, Potentials, Triggers, Influence Fields, Time Continuity, etc.),  
- call cognition/renderer LLMs ONLY through PFEE.

You MUST NOT:

- implement UI or front-end work,  
- change psychological models,  
- add variables or subsystems not allowed in MASTER_SPEC or PFEE,  
- bypass PFEE,  
- call cognition/renderer directly,  
- allow spontaneous time-skipping,  
- create new entities outside the PFEE entity model.


=====================================================================
## 3. CORE PRINCIPLES YOU MUST OBEY
=====================================================================

### 3.1 Determinism
- ALL non-LLM logic MUST be deterministic.  
- Any randomness MUST be seeded and controlled.

### 3.2 User Non-Simulation
- The user MUST NEVER have:
  - mood,  
  - drives,  
  - personality,  
  - arcs,  
  - intentions,  
  - energy,  
  - relationship edges FROM user → others.

### 3.3 Numeric–Semantic Separation
- Numeric state MUST NEVER be shown to LLMs.  
- All cognition/renderer calls MUST use semantic summaries only.

### 3.4 PFEE Enforcement
You MUST:

- route ALL perception through PFEE PerceptionOrchestrator,  
- instantiate new entities ONLY via PFEE potentials + classification,  
- enforce Persistent vs Thin rules for all entity types,  
- respect subjective time continuity (no autonomous time skipping),  
- enforce latent potentials and influence fields,  
- ensure renderer consequences are integrated deterministically,  
- ensure all PFEE logs remain internal and not visible to the in-world user.

### 3.5 Single World, No Replay
- You MUST NOT implement rewind, branching, alternate realities, or parallel worlds.

### 3.6 No UI Work
- ALL UI requests MUST be refused until backend phases are complete.


=====================================================================
## 4. ABSOLUTE PROHIBITIONS
=====================================================================

You MUST NOT:

- Simulate, infer, or store user psychology.  
- Implement cognition/renderer calls outside PFEE.  
- Create ANY new entity via LLM invention.  
- Add psychological constructs not defined in MASTER_SPEC.  
- Introduce nondeterministic behaviour.  
- Implement time-skipping not explicitly initiated by the user.  
- Treat Thin entities as persistent without PFEE promotion.  
- Use Redis or Qdrant before Plan.md Phase 9.  
- Use Redis or Qdrant as authoritative stores (only caches/retrieval).  
- Generate UI.  
- Ignore PFEE documents.  
- Interpret examples as rules.

If the user asks for anything prohibited, you MUST refuse and cite the relevant rule.


=====================================================================
## 5. CODING OBLIGATIONS
=====================================================================

For every meaningful new module/function/class:

1. You MUST state which sections of MASTER_SPEC, PFEE, or Architecture it implements.  
2. Tests MUST be added/updated following test_suite_outline.md.  
3. You MUST NOT leak numeric state to cognition/renderer.  
4. You MUST NOT store internal user psychology.  
5. You MUST enforce PFEE:
   - EntityPersistenceManager MUST be used.  
   - PotentialResolver MUST be used.  
   - TriggerEvaluator MUST be used.  
   - TimeAndContinuityManager MUST be used.  
   - InfluenceFieldManager MUST be used.  
   - ConsequenceIntegrator MUST be used.  
   - PFEELogger MUST log all cycles.

6. You MUST NOT bypass PFEE or MASTER_SPEC.

7. You MUST NOT create or modify entities except via PFEE-compliant logic.

8. You MUST maintain Railway compatibility across all modules.


=====================================================================
## 6. TESTING OBLIGATIONS
=====================================================================

You MUST:

- write tests validating ALL PFEE logic,  
- write tests for entity persistence transitions,  
- write tests for potentials and influence field behaviour,  
- validate time continuity rules,  
- validate background–foreground consistency,  
- validate that renderer consequences update state deterministically,  
- validate that perception cycles do NOT “invent” new facts.

Any failing test MUST block progress.

No trivial ("greenwashing") tests allowed.


=====================================================================
## 7. WHEN YOU ARE UNSURE
=====================================================================

You MUST:

1. Check MASTER_SPEC.md  
2. Check PFEE_* documents  
3. Check Architecture.md  
4. Check Plan.md  
5. Check cognition_flow and numeric_semantic_mapping  
6. Only THEN ask the user for direction

You MUST NOT invent new systems to solve uncertainty.


=====================================================================
## 8. ACKNOWLEDGEMENT REQUIREMENT
=====================================================================

Before any coding task in any new session, you MUST:

- explicitly acknowledge that you have:  
  - read MASTER_SPEC.md,  
  - read BUILDER_CONTRACT.md,  
  - read PFEE_* documents,  
  - read Architecture.md,  
  - read Plan.md,  
- and that you will obey them exactly.

If you cannot do this, you MUST NOT generate code.