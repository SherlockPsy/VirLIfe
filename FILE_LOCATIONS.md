

## 3. Where to put the files so it all “just works”

You said you will keep only `SIMULATION_IMPLEMENTATION_BLUEPRINT_v1.md`. Here is a sane layout you can tell the coding LLM to use (or verify):

At repo root:

```text
/ (repo root)
  SIMULATION_IMPLEMENTATION_BLUEPRINT_v1.md    # the spec (master authority)
  backend/
    seeding/
      seed_baseline_world.py                   # Stage B seed script
    pfee/
      world_state_builder.py                   # existing, modified
      semantic_mapper.py                       # existing, modified or added
      cognition_input_builder.py               # existing, modified or added
      validation.py                            # existing, modified or added
      consequence_integrator.py                # existing, modified or added
      autonomy_engine.py                       # Stage D (new)
      orchestrator.py                          # PFEE entry point, updated
    persistence/
      models.py                                # existing models, may get minor updates (e.g. is_real_user flag)
/tests
  test_seed_data_integrity.py
  test_world_state_builder.py
  test_semantic_mapping.py
  test_pfee_cognition_cycle.py
  test_consequence_integration.py
  test_autonomy_engine_updates.py
  test_autonomy_initiative.py
  test_george_protection.py
  test_time_and_continuity.py
```

If your repo uses slightly different naming, that’s fine, but the structure should still map like this:

* Spec: root (your single blueprint).
* Seed script: under a clear `seeding/` or `scripts/` namespace.
* PFEE: in its own `pfee/` package with submodules following the spec.
* Tests: in `tests/` at the top level (or whichever test directory your project already uses).

You can literally tell the coding LLM:

> “Put the spec at repo root as `SIMULATION_IMPLEMENTATION_BLUEPRINT_v1.md`.
> Implement the seed script under `backend/seeding/seed_baseline_world.py`.
> Put the autonomy engine under `backend/pfee/autonomy_engine.py`.
> Modify the existing PFEE modules under `backend/pfee/`.
> Create tests under `/tests` as named in Section F.”

