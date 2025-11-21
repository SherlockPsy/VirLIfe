## PROMPT

You are an implementation LLM with full read/write access to this repository.

Your single source of truth for what to build is the file:

  SIMULATION_IMPLEMENTATION_BLUEPRINT_v1.md

This file is located at the root of the repository (or in /docs if I moved it there). You MUST:

1. Open and read SIMULATION_IMPLEMENTATION_BLUEPRINT_v1.md in full.
2. Treat it as an *authoritative specification*, not a suggestion.
3. Implement everything in Sections A–F, in order, with no improvisation.

Key constraints you MUST obey:

- DO NOT change the high-level architecture of the existing PFEE system.
- DO NOT invent new behaviours that are not in the spec.
- DO NOT simulate George’s inner psychological state under any circumstances.
- DO NOT skip writing tests: the test suite specified in Section F is mandatory.
- DO NOT rely on your own ideas of “good UX” or “nice behaviour”. Obey the spec only.

Implementation order (strict):

1. **Data Mapping Layer (Section A)**  
   - Implement deterministic mapping functions for:
     - Rebecca_Fingerprint.json
     - Rebecca Master Profile.csv
     - Rebecca Ferguson - Connections.csv
     - Sim Baseline.docx
     - George_Profile.txt
     - Personalities.txt
   - These functions must NOT write to the DB directly; they prepare structured objects.

2. **Seed Script (Section B)**  
   - Implement a deterministic, idempotent seed function:
       `seed_baseline_world(engine)`  
   - This function uses the mapping layer to populate the DB:
     - world row
     - locations
     - objects
     - agents
     - relationships
     - memories
     - arcs
     - pfee_influence_fields
     - calendars
     - intentions
     - initial positions
   - Enforce all George rules in the seed (no internal state for George).

3. **PFEE Modifications (Section C)**  
   - Update:
     - world state builder
     - semantic mapper
     - cognition input builder
     - validation
     - consequence integrator
     - orchestrator entry point
   - Make them use the seeded data and obey all behaviours and constraints in Section C.

4. **Autonomy Engine (Section D)**  
   - Create module `autonomy_engine` (or equivalent) with:
     - `update_agents_over_time(...)`
     - `compute_initiative_candidates(...)`
   - Implement drive regulation, mood drift, relationship drift, arc progression, influence-field pressure rules, and initiative computation EXACTLY as specified.

5. **George-Protection Enforcement (Section E)**  
   - Add `is_real_user` flag to George’s agent row (if not already present).
   - Insert explicit `if agent.is_real_user: continue` or equivalent guards in:
     - world state builder
     - semantic mapper
     - cognition input builder
     - validation
     - consequence integrator
     - autonomy engine
     - any time/continuity agent-level logic
   - Ensure George’s internal psychological fields are never read or written.

6. **Full Test Suite (Section F)**  
   - Implement the tests described in Section F in the `tests/` folder.
   - All tests MUST pass.
   - No code is “done” until the tests in Section F succeed.

Working rules:

- At each stage, you MUST:
  - run the relevant tests,
  - fix failures,
  - and only then proceed to the next stage.
- When you create or modify a file, explain briefly:
  - what you changed,
  - which section(s) of the spec it implements.

Your goal is to bring the repository into full conformity with SIMULATION_IMPLEMENTATION_BLUEPRINT_v1.md, with all tests passing.

Begin by confirming:
- that you’ve opened SIMULATION_IMPLEMENTATION_BLUEPRINT_v1.md,
- summarising its sections very briefly (1–2 sentences per section),
- and outlining your concrete plan of work in terms of repo files and steps.
```
