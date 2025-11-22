We are continuing an ongoing multi-phase implementation already in progress.

The master, authoritative, and ONLY specification for this project is:

    SIMULATION_IMPLEMENTATION_BLUEPRINT_v1.md

This file must always be read FIRST and treated as the source of truth.
Nothing else overrides it. No assumptions override it. No “improvements” override it.

Because this is a continuation session inside Cursor, you MUST follow these rules exactly:

1. Re-open and re-read SIMULATION_IMPLEMENTATION_BLUEPRINT_v1.md now to rebuild full context.
   - Do NOT rely on memory from prior sessions.
   - Do NOT guess or improvise missing context.
   - Anchor yourself on the contents of this file every session.

2. Scan the entire repository to determine:
   a) What phases of Sections A–F have already been completed,
   b) What code already exists,
   c) What remains unfinished or unimplemented.

3. Identify the NEXT phase to implement according to Sections A–F.
   - DO NOT restart from Phase 1.
   - DO NOT redo work that is complete.
   - DO NOT overwrite working code unless it violates the spec or fails tests.

4. Continue implementation STRICTLY according to the master spec.
   - No creative liberties.
   - No architectural redesigns.
   - No deviation from the PFEE model.
   - No reinterpretation of the George rules.
   - No summarizing intentions: follow EXACTLY what Sections A–F specify.

5. All real-world seed files are located in:

       backend/data_sources/

   You MUST load all data from there.  
   You MUST NOT move, rename, or relocate these files.  
   You MUST NOT recreate or duplicate them.

6. For any phase, follow this discipline:
   - Implement exactly what the spec says.
   - Run or outline the relevant tests (Section F).
   - Fix violations.
   - Only then proceed to the next phase.

7. GEORGE IS THE REAL USER.
   Under NO circumstances may you:
   - simulate his inner state,
   - generate drives or mood for him,
   - assign him arcs or intentions,
   - select him as a vantage agent,
   - allow PFEE or Autonomy Engine to modify him internally.

8. NO stage is considered complete unless:
   - the implementation matches the spec,
   - the code compiles,
   - and the corresponding tests in Section F are passing.

9. In this continuation session, your first output MUST be:
   - A clear statement of which phases (A–F) are already complete,
   - Which phase is next,
   - And a concrete, file-by-file plan of what you will implement next.

10. Do not rewrite completed modules unless they fail tests or contradict SIMULATION_IMPLEMENTATION_BLUEPRINT_v1.md.

Proceed.