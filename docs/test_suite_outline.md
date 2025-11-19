## TEST SUITE OUTLINE FOR BUILDER
### (FOR MASTER_SPEC.md COMPLIANCE)

This document outlines the categories of tests that MUST exist to validate an implementation against MASTER_SPEC.md.

Individual tests can be generated later from this outline.


## 1. DETERMINISM TESTS

**Goal:** Prove that the substrate is deterministic.

Tests (examples of categories, not exhaustive):

1.1 Same Seed, Same Outcome  
- Given: identical initial world state + same sequence of user and agent actions + fixed seeds  
- When: simulation is run twice  
- Then: world state trajectories MUST match bit-for-bit at each checkpoint.

1.2 No Hidden Randomness  
- Given: repeated identical actions under same seed  
- Then: no variation in agent state trajectories.

1.3 LLM Boundary  
- Ensure that numeric state is updated only via deterministic mappings after an LLM call, not directly by LLM content.


## 2. USER NON-SIMULATION TESTS

**Goal:** Prove the user is never simulated.

Tests:

2.1 Data Model Audit  
- Check: user object has no fields for mood, drives, personality, arcs, intentions, energy.

2.2 No User Passed as Agent to Cognition  
- Assert: Cognition Service is never invoked with user as the cognitive subject.

2.3 Renderer POV  
- Check: all user-facing output is second-person, with no explicit claims about user internal state.

2.4 Persistence  
- Confirm: no table or structure stores numeric psychology for the user.


## 3. STATE VARIABLE INVARIANTS

**Goal:** Ensure all variables remain within defined ranges.

Tests:

3.1 Bounds Checks  
- Drives ∈ [0,1], valence ∈ [-1,1], arousal ∈ [0,1], etc.

3.2 Relationship Edge Bounds  
- warmth, trust, tension, etc., all within specified ranges after every update.

3.3 Arc Intensity and Decay  
- intensity never negative; decays correctly; never exceeds 1.0.


## 4. COGNITION TRIGGER TESTS

**Goal:** Verify correct triggering of cognition.

Tests:

4.1 Threshold-Based Triggering  
- Given: artificially high M (salience, drive pressure, arc, rel_stakes)  
- Then: cognition MUST trigger.

4.2 Below Threshold  
- Given: low M and trivial events  
- Then: cognition MUST NOT trigger.

4.3 Cooldown  
- Given: repeated events inside cooldown window  
- Then: second cognition MUST NOT be triggered until cooldown expires.

4.4 User Presence  
- Ensure: user presence alone does not trigger cognition; it only influences salience and relationships.


## 5. NUMERIC → SEMANTIC MAPPING TESTS

**Goal:** Ensure LLM never sees raw numbers and mapping is coherent.

Tests:

5.1 No Numerics in LLM Payload  
- Inspect Cognition and Renderer requests: assert no numeric psychology values are present.

5.2 Mapping Function Coverage  
- For each range bucket, assert that a deterministic phrase is output.

5.3 Mood Mapping Coherence  
- Extreme negative valence/arousal scenarios produce “negative” descriptors, and vice versa.

5.4 Relationship Mapping Coherence  
- High trust+warmth+low tension produce positive relationship summaries, etc.


## 6. LLM OUTPUT → NUMERIC UPDATE TESTS

**Goal:** Ensure LLM never sets numbers directly; mapping is deterministic.

Tests:

6.1 Schema Compliance  
- Check LLM output conforms to expected JSON schema.

6.2 Mapping Tables Applied  
- Given a specific stance_shift description, assert same numeric deltas are applied every time.

6.3 No Direct Numeric Instructions  
- Detect and reject LLM outputs that attempt to set numeric values explicitly (e.g. "set trust to 0.9").


## 7. AUTONOMY ENGINE TESTS

**Goal:** Ensure reasonable behaviour without LLM.

Tests:

7.1 Routine Execution  
- Agents follow sleep/work/commute schedules without LLM calls.

7.2 Low-Level Responses  
- In trivial small-talk or low-stakes situations, agents behave via deterministic patterns and do not call Cognition.

7.3 Drift  
- Drives, relationships, arcs drift as described when no events occur.


## 8. MEMORY SYSTEM TESTS (EPISODIC + BIOGRAPHICAL)

**Goal:** Ensure memory behaves correctly over time.

Tests:

8.1 Episodic Creation Threshold  
- Only events above importance threshold create memories.

8.2 Salience Decay and Reinforcement  
- Memory salience decays and increases on recall or similar events.

8.3 Biographical Growth  
- Biographical facts are only created from explicit disclosures or stable repeated patterns.

8.4 Biographical Influence  
- Biographical facts influence interpretation (e.g., conflicts with known history affect trust updates).


## 9. RENDERER TESTS

**Goal:** Validate perception-only rendering.

Tests:

9.1 Sensory Only  
- Renderer output contains only perceptual content from perceiver POV.

9.2 No Internal State Narration  
- Ensure no text like “you feel X” appears unless explicitly designated as user self-report.

9.3 Trigger Conditions  
- Renderer is called when specified triggers occur (location change, important action, etc.).


## 10. WORLD CONTINUITY TESTS

**Goal:** Ensure off-screen continuity.

Tests:

10.1 Life Without User  
- Run simulation with no user actions: agents still live, move, work, interact, etc.

10.2 User Drop-In  
- User connects after long absence: world state correctly reflects elapsed time and agents’ development.

10.3 No Freeze on Disconnect  
- Agents continue evolving after user disconnects.


## 11. REGRESSION AND INTEGRATION TESTS

- Full scenario tests where:
  - multiple agents interact
  - user moves through scenes
  - cognition triggers where expected
  - renderer output is coherent
  - all invariants hold

These can be used as long-running “storylike” tests to ensure the system behaves realistically.


## 12. META-ASSERTION

Each test case MUST be explicitly tied back to one or more normative clauses in MASTER_SPEC.md.

No test may enforce a behaviour that is not grounded in the spec.


## 13. PERSONALITY COMPILER AND PERSONALITY CONTEXT TESTS

**Goal:** Ensure the Personality Compiler and personality context behave deterministically and are correctly integrated into cognition and rendering.

Tests:

13.1 Kernel Determinism  
- Given: same template mixture + same fingerprint input for an agent  
- When: Personality Compiler runs twice  
- Then: personality kernel MUST be identical.

13.2 Summary Determinism  
- Given: same kernel + same fingerprint  
- When: summaries are recomputed  
- Then: stable personality summary and domain summaries MUST be identical.

13.3 Caching Behaviour  
- Given: no change in kernel or fingerprint  
- Then: summaries MUST NOT be regenerated unnecessarily during normal ticks.  
- Given: change in kernel or fingerprint  
- Then: summaries MUST be regenerated and updated in persistence.

13.4 Prompt Inclusion  
- Inspect Cognition and Renderer requests:  
  - Assert stable personality summary is present whenever the agent is cognitively involved.  
  - Assert relevant domain summaries and dynamic activation packet are included.  
  - Assert raw kernel values and raw fingerprint text are **never** present.

13.5 Activation Packet Correctness  
- Given: controlled changes to drives, mood, arcs, relationships, energy  
- Then: dynamic activation packet text MUST change in a way consistent with those changes and with the personality kernel.  
- Running the same scenario twice MUST yield identical activation packet text.

13.6 Personality Boundary Tests  
- Assert LLM outputs cannot directly change personality kernel.  
- Assert any long-term personality changes (if supported) are mediated by deterministic rules outside the LLM.  
- Assert no test or code path allows creating new personality variables beyond those defined in the spec.