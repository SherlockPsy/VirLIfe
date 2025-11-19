## COGNITION FLOW — EVENT DRIVEN PIPELINE

This document defines the exact flow for when and how Cognition LLM is called for an agent.

It is fully consistent with MASTER_SPEC.md and MUST be implemented as described here.


## 1. TRIGGER CONTEXT

Cognition is considered only when a **world event** occurs that involves one or more agents.

World events include (non-exhaustive, pattern only):

- Agent A speaks to B
- Agent A performs a non-trivial action toward B
- An external incursion (news, message, life event) hits an agent
- A significant internal milestone is reached (arc intensity, drive threshold, etc.)

For each such event, the system identifies candidate agents for cognition.


## 2. FLOW OVERVIEW

High-level flow:

1. Event occurs in the World Engine.
2. World Engine updates raw state (locations, objects, etc.).
3. Autonomy Engine updates numeric psychology:
   - drives
   - mood
   - arcs
   - relationships
   - energy
   - personality activation state (via Personality Kernel + current state)
4. For each potentially affected agent:
   - compute salience and meaningfulness score **M**.
5. If cognition conditions are met:
   - build semantic context packet.
   - call Cognition LLM.
   - parse structured output.
   - apply deterministic numeric updates.
6. World Engine persists state.
7. Renderer may be triggered separately (user-facing).


## 3. DETAILED FLOW (STEP-BY-STEP)

### 3.1 Event Handling

Given an event `E` at time `t`:

- World Engine:
  - updates physical world state (who is where, what changed).
  - enqueues psychological update for each involved agent.

- Autonomy Engine:
  - classifies `E` along psychological dimensions:
    - supportive vs undermining
    - safe vs threatening
    - affectionate vs cold
    - cooperative vs obstructive
    - boundary-respecting vs boundary-violating
  - maps `E` deterministically into drive effects `effect(E, drive)` ∈ [-1, 1].


### 3.2 Numeric Updates (Pre-cognition)

For each affected agent `A`:

1. Update drives:
   - `d_level ← clamp(d_level + effect(E, d) * d_sensitivity)`
   - apply baseline drift if appropriate.

2. Update mood:
   - compute aggregated drive satisfaction change over recent window.
   - update valence and arousal according to MASTER_SPEC mood rules.

3. Update arcs:
   - if `E` semantically matches arc.topic_vector → reinforce arc.
   - decay all arcs by their decay_rate * Δt.

4. Update relationships:
   - adjust warmth / trust / tension / comfort, scaled by volatility.
   - apply drift rules if no events for that dyad recently.

5. Update energy:
   - decrease for demanding events.
   - otherwise drift toward baseline.

6. Update memory:
   - compute `event_importance`.
   - if above threshold → create episodic memory.
   - update salience of relevant memories.
   - update biographical memory if `E` reveals stable fact (e.g. explicit statement).

7. Update personality activation:
   - use personality kernel + current drives, mood, relationships, arcs, energy
   - compute a short-lived activation state for this event (no LLM).


### 3.3 Salience and Meaningfulness Computation

For each candidate agent `A`:

1. Compute salience for:
   - people present (including user if physically there),
   - topics implied by `E`,
   - objects,
   - internal concerns (drives, arcs).

2. Compute:
   - `salience_max = max(salience)`
   - `drive_pressure_max = max(d_level)`
   - `arc_hot = max(arc.intensity)`
   - `rel_stakes = max over relevant relationship edges` (|warmth|, |trust|, tension)
   - `energy = A.energy`

3. Compute meaningfulness score:

```text
M = w1 * salience_max
  + w2 * drive_pressure_max
  + w3 * arc_hot
  + w4 * rel_stakes
  - w5 * (1 - energy)

  3.4 Cognition Eligibility Check

For each agent A, cognition MUST ONLY be triggered if ALL are true:
	1.	M ≥ cognition_threshold.
	2.	Event type is not classified as trivial.
	3.	Cognition cooldown window for A has elapsed.
	4.	There exists at least one non-trivial behavioural choice to be made (e.g., how to respond, whether to escalate, whether to disclose, whether to withdraw).

User presence MUST NOT be a separate rule.
User actions influence variables that feed into M but do not bypass these checks.

4. COGNITION INPUT PACKET

If cognition is triggered for agent A, build CognitionContext(A, E).

CognitionContext(A, E) MUST include (semantic, NOT numeric):
	•	Personality context (from Personality Compiler):
	•	stable personality summary
	•	relevant domain summaries (e.g., conflict, emotion, communication, humour)
	•	current dynamic activation packet (how their personality is tilted right now)
	•	Perception snapshot from A’s POV:
	•	who is present
	•	what was just said/done
	•	immediate environment
	•	Semantic summaries of:
	•	A’s current mood (valence/arousal)
	•	most pressured drives
	•	key relationships involved (toward each participant, including user if relevant)
	•	active arcs relevant to this situation
	•	energy (e.g., “tired vs energised”, not numbers)
	•	Relevant memory snippets:
	•	a small set of episodic memories (top-K by similarity + salience + recency)
	•	biographical facts about the people involved that matter here
	•	Current intentions:
	•	high-priority, relevant intentions (“avoid topic X”, “be gentle with Y”, etc.)

CognitionContext(A, E) MUST NOT include:
	•	raw numeric values
	•	any internal state for the user
	•	omniscient global state
	•	raw personality kernel values
	•	raw fingerprint text

5. LLM CALL AND OUTPUT CONTRACT

Cognition LLM is called with CognitionContext(A, E) and MUST respond with structured data.

A recommended schema (can be adapted but structure MUST be explicit):

{
  "utterance": "string or null",          // what A says now
  "action": "string or null",             // what A does now (salient, intentional)
  "stance_shifts": [                      // optional: changes in how A feels/positions themselves
    {
      "target": "person_id",
      "description": "textual stance change"
    }
  ],
  "intention_updates": [                  // create/boost/lower/drop intentions
    {
      "operation": "create|boost|lower|drop",
      "type": "controlled_intention_type",
      "target": "person_or_topic_id_or_null",
      "horizon": "short|medium|long",
      "description": "textual description"
    }
  ]
}

LLM MUST NOT output numeric values.
LLM MUST NOT talk about “setting trust to X” or similar.
LLM MUST NOT redefine stable personality (“she is now a completely different person”) in one step; any long-term change MUST be mediated by deterministic mapping.

6. POST-COGNITION NUMERIC UPDATE

The Autonomy Engine MUST:
	1.	Apply utterance:
	•	create speech event in World Engine from A to targets.
	2.	Apply action:
	•	update physical state (movement, posture, etc.) in World Engine.
	3.	Map stance_shifts → numeric updates:
	•	use deterministic mapping tables:
	•	e.g., “she decides to give him the benefit of the doubt” → small increase in trust, small decrease in tension.
	•	mapping MUST be stable and global (no per-instance improvisations).
	4.	Map intention_updates:
	•	create new intentions with appropriate priority/horizon.
	•	boost or lower existing priorities.
	•	drop intentions where instructed.
	5.	Update relationships, drives, arcs if implied by LLM decisions:
	•	still via deterministic mapping rules (e.g., choosing to open up may slightly reduce autonomy drive pressure, adjust warmth, etc.).
	6.	Optionally adjust personality kernel very slightly for long-term shifts:
	•	ONLY via deterministic rules informed by repeated patterns of cognition output and events.
	•	NEVER directly from a single “personality change” phrase.
	7.	Persist all updates.

Renderer is then free to describe the result from the user’s perceptual POV if the user is present.

7. KEY INVARIANTS
	•	Cognition is event-driven, not continuous.
	•	Cognition is decided by M and triviality classification.
	•	The user is never simulated.
	•	Numeric state never leaves the substrate.
	•	LLM outputs never directly set numeric state.
	•	All numeric changes after cognition are deterministic mappings.
	•	Personality context (stable + domain + activation) is always supplied by the Personality Compiler numerics, never inferred ad-hoc by the LLM.

   