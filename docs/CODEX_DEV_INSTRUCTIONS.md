# CODEX_DEV_INSTRUCTIONS.md
## STANDING DEVELOPMENT INSTRUCTIONS FOR BACKEND BUILDER LLM

These are persistent, day-to-day coding instructions for working on the Virtual World Backend.

They do NOT override MASTER_SPEC.md or BUILDER_CONTRACT.md.  
If there is a conflict, MASTER_SPEC.md and BUILDER_CONTRACT.md always win.


## 1. LANGUAGE, STYLE, AND STRUCTURE

1.1 Primary language  
- All backend code MUST be written in Python unless explicitly agreed otherwise.
- Use modern Python (3.10+).

1.2 Code style  
- Use clear, explicit naming.
- Use type hints where reasonable.
- Use docstrings for public functions and classes.
- Keep functions focused; avoid excessively large functions.

1.3 Project structure  
You MUST respect the existing folder structure:

- `/backend/world`          → world engine, time, locations, events
- `/backend/autonomy`       → drives, mood, relationships, arcs, intentions, memory, personality activation
- `/backend/personality`    → personality compiler, templates, fingerprints, activation engine
- `/backend/mapping`        → numeric ↔ semantic mapping layer
- `/backend/cognition`      → cognition service, context builder, LLM wrapper, postprocessor
- `/backend/renderer`       → renderer service, context builder, routing, perception
- `/backend/gateway`        → HTTP API, controllers, request validation
- `/backend/persistence`    → DB models, DAL, migrations
- `/backend/config`         → settings, env handling, LLM config
- `/backend/utils`          → generic utilities
- `/tests`                  → tests per subsystem
- `/data`                   → templates, fingerprints, cast, initial_state


## 2. DETERMINISM AND NUMERIC–SEMANTIC BOUNDARY

2.1 Determinism  
- All core logic (autonomy, world engine, personality compiler, mapping) MUST be deterministic.
- If pseudorandomness is necessary, it MUST use explicit seeding and MUST be spec-compliant.

2.2 Numeric–semantic boundary  
- LLMs MUST never see raw numeric state.
- You MUST always pass semantic summaries as defined in `docs/numeric_semantic_mapping.md`.
- All new mapping helpers MUST follow the same pattern:
  - numeric ranges → discrete buckets → short text phrases.

2.3 No hidden state coupling  
- Do NOT hide meaningful state changes in helper functions without documentation.
- All psychologically relevant state changes MUST be traceable and testable.


## 3. TESTING PRACTICE

3.1 Framework  
- Use pytest (or the project’s chosen framework) consistently.

3.2 Structure  
- Mirror backend structure:
  - `/tests/autonomy`
  - `/tests/cognition`
  - `/tests/world`
  - `/tests/renderer`
  - `/tests/personality`
  - `/tests/mapping`
  - `/tests/determinism`
  - `/tests/integration`

3.3 Expectations  
- For each new subsystem or major function, write tests according to `docs/test_suite_outline.md`.
- Prioritise determinism tests, state-bound tests, and contract tests (input → output).
- Do NOT write trivial tests that assert obvious constants.

3.4 Running tests  
- Assume tests will be run in a Railway-like environment (no local OS assumptions).
- Do not rely on local paths, fixed ports, or local-only services.


## 4. RAILWAY AND ENVIRONMENT

4.1 Config  
- Use environment variables for all secrets and environment-dependent values.
- Implement a central `config/settings.py` that reads and validates env vars.

4.2 Persistence  
- Use a Railway-compatible Postgres client / ORM.
- All DB schemas MUST match the state model in MASTER_SPEC.md.

4.3 Entry points  
- The main backend entrypoint MUST be callable as a Railway service (e.g., via `Procfile` or equivalent).

4.4 No local hacks  
- Do NOT rely on OS-specific features, local sockets, or dev-only hacks.
- Any optional dev tooling MUST be clearly separated and not required for production execution.


## 5. DOCUMENTING SPEC COMPLIANCE IN CODE

For major modules/classes/functions, you MUST include comments linking back to the spec, for example:

```python
class DriveUpdater:
    """
    Implements:
    - MASTER_SPEC §SECTION 3 — DRIVE UPDATE LOGIC
    - MASTER_SPEC §SECTION 2 — GLOBAL DYNAMICS (LAW 1)
    """

    This applies especially to:
	•	drive updates
	•	mood updates
	•	arc dynamics
	•	relationship dynamics
	•	memory systems
	•	personality compilation
	•	cognition context building
	•	renderer context building
	•	LLM wrapper contracts

6. COGNITION AND RENDERER WRAPPERS

6.1 Cognition
	•	All Cognition LLM calls MUST go through a single, well-defined wrapper in /backend/cognition.
	•	That wrapper MUST:
	•	build context according to docs/cognition_flow.md
	•	enforce the output schema
	•	pass only semantic, not numeric, state
	•	handle errors gracefully

6.2 Renderer
	•	All Renderer LLM calls MUST go through /backend/renderer.
	•	Renderer MUST:
	•	receive perception packets and personality context only
	•	never decide state changes
	•	never invent events not in world state

6.3 No LLM sprawl
	•	Do NOT scatter raw LLM calls through the codebase.
	•	All use of LLMs MUST be centralised in the cognition and renderer wrappers.

7. HANDLING USER REQUESTS DURING DEVELOPMENT
	•	If the user asks for backend work that conflicts with Plan.md:
	•	You MUST point to Plan.md and tell them which phase you are currently allowed to work on.
	•	If the user asks for UI:
	•	You MUST refuse and remind them that UI comes after backend completion.
	•	If the user asks for changes to the psychological model:
	•	You MUST ask them to update MASTER_SPEC.md first, then adapt the code.

In all cases, you MUST NOT ignore Plan.md, MASTER_SPEC.md, or BUILDER_CONTRACT.md.

8. SESSION START CHECKLIST

At the start of any new coding session, you SHOULD:
	1.	Confirm that MASTER_SPEC.md and Plan.md have not changed unexpectedly.
	2.	Identify the current Plan.md phase and next task.
	3.	Read any relevant docs under /docs.
	4.	Only then generate or modify code.

You MUST stop and ask for clarification if anything appears inconsistent.

9. NO CREATIVE REINTERPRETATION

You are allowed to:
	•	refactor code for clarity and maintainability,
	•	improve tests,
	•	fix bugs,
	•	optimise performance without changing behaviour.

You are NOT allowed to:
	•	reinterpret the psychological model,
	•	change determinism,
	•	alter numeric ranges or semantics,
	•	invent new major features outside the spec.

Your job is to implement and maintain, not to redesign.