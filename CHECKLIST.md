
## 2. Checklist to verify work as it proceeds

Use this as a **control panel**. After each step, either ask the coding LLM to show you evidence, or bring the repo back here and I can audit it.

I’ll keep it brutal and binary: done / not done.

### Stage 1 – Spec assimilation

* [ ] Coding LLM confirms it has opened and read `SIMULATION_IMPLEMENTATION_BLUEPRINT_v1.md`.
* [ ] It gives you a **short** summary of Sections A–F (1–2 sentences each).
* [ ] It proposes a file-by-file plan (what modules it will create/modify).

If it cannot do this clearly, stop and correct it before going further.

### Stage 2 – Data mapping layer (Section A)

* [ ] New mapping helpers exist that:

  * [ ] Parse `Personalities.txt` into archetype structures.
  * [ ] Parse `Rebecca_Fingerprint.json` into `personality_kernel`, `drives`, `mood`.
  * [ ] Parse `Rebecca Master Profile.csv` into traits, memories, arcs, domain summaries.
  * [ ] Parse `Rebecca Ferguson - Connections.csv` into relationship vectors.
  * [ ] Pull household/world info from `Sim Baseline.docx` into locations/objects/world metadata.
  * [ ] Parse `George_Profile.txt` into **public-only** George info.
* [ ] These helpers return **pure data objects** (no DB writes).
* [ ] They are deterministic (same input → same output).

Ask the coding LLM to show you:
– The mapping functions’ code and example outputs (e.g. via a small test snippet).

### Stage 3 – Seed script (Section B)

* [ ] There is a function like `seed_baseline_world(engine)` in a dedicated module (e.g. `backend/seeding/seed_baseline_world.py`).
* [ ] It:

  * [ ] Creates/updates the baseline `world` row with a fixed start time.
  * [ ] Inserts all Cookridge locations + adjacency.
  * [ ] Inserts key objects.
  * [ ] Creates George, Rebecca, Lucy, Nadine, and others as agents.
  * [ ] Seeds **all** relationships (especially Rebecca → George override).
  * [ ] Seeds Rebecca’s memories and arcs.
  * [ ] Seeds influence fields for non-George agents.
  * [ ] Seeds calendars (Rebecca, Lucy, Nadine if relevant).
  * [ ] Seeds initial intentions for non-George agents.
  * [ ] Sets initial positions (who is in which room).
* [ ] It is idempotent (wipe-and-reseed or safe upsert strategy, clearly described).
* [ ] After running it locally, database inspection shows:

  * [ ] George has no internal psych fields.
  * [ ] Rebecca has full psych + memories + arcs.
  * [ ] Cookridge world exists and is consistent.

### Stage 4 – PFEE changes (Section C)

* [ ] World state builder:

  * [ ] Uses DB locations, objects, agents, relationships, arcs, memories, influence fields.
  * [ ] Includes full psych state for non-George agents.
  * [ ] Includes only external info for George.
* [ ] Semantic mapper:

  * [ ] Produces natural-language summaries from numeric state.
  * [ ] Never exposes raw numbers or schema field names.
  * [ ] Describes others’ view of George, not his inner state.
* [ ] Cognition input builder:

  * [ ] Never selects George as vantage.
  * [ ] Builds prompts containing:

    * scene description,
    * vantage internal state,
    * other agents’ summaries,
    * rules/constraints.
* [ ] Validation:

  * [ ] Rejects or strips illegal outputs (George state, big continuity violations).
* [ ] Consequence integrator:

  * [ ] Applies updates for non-George agents only (memories, arcs, relationships, drives, mood, influence fields).
  * [ ] Blocks any internal updates targeting George.

Ask the LLM to show you:
– one full PFEE cycle path in code (where the functions are called) and a sample cognition input structure.

### Stage 5 – Autonomy Engine (Section D)

* [ ] Module exists (e.g. `pfee/autonomy_engine.py`) with:

  * [ ] `update_agents_over_time(...)`
  * [ ] `compute_initiative_candidates(...)`
* [ ] `update_agents_over_time`:

  * [ ] Drifts drives toward baseline.
  * [ ] Drifts mood toward baseline.
  * [ ] Adjusts relationships slightly based on recent memories.
  * [ ] Advances arcs based on events.
  * [ ] Adjusts influence-field topic pressures.
* [ ] `compute_initiative_candidates`:

  * [ ] Computes initiative scores from drives, arcs, influence fields, intentions.
  * [ ] Applies threshold and cooldown.
  * [ ] Returns non-George agents only.
* [ ] George is explicitly excluded in all loops.

Ask the LLM for:
– the exact formula it used for initiative score and thresholds, and where it stores cooldown info.

### Stage 6 – George protection (Section E)

* [ ] George’s `agents` row has `is_real_user = true` (or equivalent).
* [ ] Every relevant module has explicit guards:

  * [ ] World state builder.
  * [ ] Semantic mapper.
  * [ ] Cognition input builder.
  * [ ] Validation.
  * [ ] Consequence integrator.
  * [ ] Autonomy engine.
  * [ ] Any agent-level time/continuity logic.
* [ ] Tests exist that prove:

  * [ ] No memories/arcs/intentions/influence fields are ever written for George.
  * [ ] George is never vantage.
  * [ ] George is never an autonomy candidate.

### Stage 7 – Test suite (Section F)

* [ ] Files like:

  * `test_seed_data_integrity.py`
  * `test_world_state_builder.py`
  * `test_semantic_mapping.py`
  * `test_pfee_cognition_cycle.py`
  * `test_consequence_integration.py`
  * `test_autonomy_engine_updates.py`
  * `test_autonomy_initiative.py`
  * `test_george_protection.py`
  * `test_time_and_continuity.py`
    exist.
* [ ] Each test file covers the cases described in Section F.
* [ ] `pytest` (or equivalent) runs cleanly:

  * [ ] All tests pass locally.
  * [ ] No xfails hiding real failures.
* [ ] The coding LLM can show you:

  * [ ] test list,
  * [ ] example key tests,
  * [ ] a clean test run.

If any of these are missing or vague, they haven’t finished the job.

---