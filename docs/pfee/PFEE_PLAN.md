# PFEE_PLAN.md
**IMPLEMENTATION PLAN — PERCEPTION-FIRST EXPERIENCE ENGINE (PFEE)**

This plan covers ONLY the PFEE subsystem.  
It assumes the core backend (world engine, logic layer, autonomy, cognition/renderer services, persistence) already exists or is being implemented separately.

PFEE MUST NOT be built ad hoc.  
The implementation MUST follow these phases in order.

---

## Phase P0 — PFEE Scaffolding and Interfaces

**Goal:** Create the structural skeleton for PFEE without implementing behaviour.

Tasks:

1. Create `pfee/` module (or equivalent) with submodules:
   - `triggers.py` (or triggers module)  
   - `potentials.py`  
   - `entities.py` (persistence classification)  
   - `orchestrator.py`  
   - `consequences.py`  
   - `time_continuity.py`  
   - `influence_fields.py`  
   - `info_events.py`  
   - `logging.py`

2. Define interface contracts between PFEE and:
   - world engine,  
   - logic layer,  
   - autonomy engine,  
   - cognition service,  
   - renderer service,  
   - gateway,  
   - persistence.

3. Add minimal unit tests that assert:
   - modules can be imported,  
   - interfaces exist,  
   - no circular dependencies.

No business logic in this phase.

---

## Phase P1 — Entity Persistence Model (Persistent vs Thin)

**Goal:** Implement universal Persistent vs Ephemeral (Deep vs Thin) entity model.

Tasks:

1. Extend persistence schema to represent:
   - `persistence_level` for entities: `{PERSISTENT, EPHEMERAL}`,  
   - entity types: person, location, object, organisation, information_source.

2. Implement `EntityPersistenceManager` with functions such as (names indicative):

   - `classify_entity_persistence(entity, context) -> PersistenceLevel`  
   - `promote_to_persistent(entity_id)`  
   - `is_persistent(entity_id) -> bool`

3. Implement deterministic rules:

   - criteria for Persistent vs Thin based on:
     - obligations,  
     - recurrence,  
     - emotional/biographical relevance,  
     - explicit references.

4. Add tests:
   - repeated encounters promote entities,  
   - one-off encounters remain Thin,  
   - promotion is idempotent and deterministic.

---

## Phase P2 — Latent Potentials and Influence Fields

**Goal:** Represent uninstantiated possibilities and long-term influence.

Tasks:

1. Implement a data model for **latent potentials** attached to:
   - locations,  
   - roles/status (e.g. celebrity),  
   - institutional systems (deliveries, travel, etc.),  
   - general environmental contexts (park, airport, café, street).

2. Implement `PotentialResolver`:

   - `register_potential(context, potential_type, parameters)`  
   - `resolve_potentials_for_context(context) -> list[ResolvedPotential]`

3. Implement **InfluenceFieldManager**:

   - store agent-level influence fields:
     - mood offsets,  
     - intention flags,  
     - pending contact likelihood,  
     - unresolved tensions.

   - APIs:
     - `update_influence_fields_from_background(world_state)`  
     - `query_influence_for_agent(agent_id) -> InfluenceSnapshot`

4. Add tests:
   - potentials are deterministic given context,  
   - influence fields change as background logic evolves,  
   - same inputs → same potentials / influence snapshots.

---

## Phase P3 — TriggerEvaluator (Perception Triggers)

**Goal:** Implement the logic deciding when perception must be generated.

Tasks:

1. Implement `TriggerEvaluator` with functions:

   - `evaluate_user_action_trigger(user_action, world_state) -> TriggerDecision`  
   - `evaluate_agent_initiative_triggers(world_state) -> list[TriggerDecision]`  
   - `evaluate_interruption_triggers(world_state) -> list[TriggerDecision]`  
   - `evaluate_info_event_triggers(world_state) -> list[TriggerDecision]`  
   - `evaluate_environment_triggers(world_state) -> list[TriggerDecision]`

2. Encode PFEE rules:

   - user actions only trigger when socially/perceptually meaningful,  
   - agents can initiate perception based on internal logic,  
   - interruptions arise from potentials and background state,  
   - information events are treated as perception,  
   - environmental/atmospheric shifts require salience thresholds.

3. Add tests:
   - trivial actions do NOT trigger LLM,  
   - meaningful speech/actions DO trigger,  
   - agent initiative triggers fire under correct conditions,  
   - info events appear when world state says they should,  
   - environmental changes trigger only when significant.

---

## Phase P4 — PerceptionOrchestrator

**Goal:** Implement the central PFEE orchestrator.

Tasks:

1. Implement `PerceptionOrchestrator` with a main entrypoint:

   - `run_perception_cycle(world_state, optional_user_action) -> PerceptionResult`

2. Responsibilities:

   - call `TriggerEvaluator` to determine if perception should occur,  
   - call `PotentialResolver` to instantiate needed Thin entities,  
   - ensure Persistent vs Thin classification via `EntityPersistenceManager`,  
   - build cognition/renderer inputs (semantic summaries only),  
   - call cognition and/or renderer LLMs,  
   - collect structured outputs.

3. PerceptionOrchestrator MUST:
   - NEVER send numeric internal state to LLMs,  
   - NEVER create entities directly from LLM output,  
   - ALWAYS record which triggers and potentials were used (via `PFEELogger`).

4. Add tests:
   - no triggers → no LLM calls,  
   - with triggers → correct LLM calls,  
   - correct entities instantiated and logged.

---

## Phase P5 — ConsequenceIntegrator

**Goal:** Integrate LLM outputs back into world state and psychology.

Tasks:

1. Implement `ConsequenceIntegrator`:

   - `apply_perception_outcome(outcome, world_state) -> world_state'`

2. Must:

   - update locations, presence, objects, and situational facts,  
   - apply deterministic changes to:
     - mood, drives, relationships, arcs (via existing logic layer),  
   - create episodic memories when salience thresholds are met,  
   - update biographical memory when stable patterns are reinforced,  
   - adjust latent potentials and influence fields.

3. MUST treat LLM outputs as:
   - proposals to be mapped into deterministic updates,  
   - never direct modifications of numeric substrate.

4. Add tests:
   - utterances/actions lead to expected numeric changes,  
   - consequences persist even when Thin entities are discarded,  
   - text is never required to replay state.

---

## Phase P6 — TimeAndContinuityManager

**Goal:** Enforce subjective time continuity and control time transitions.

Tasks:

1. Implement `TimeAndContinuityManager` with:

   - `advance_background_time(world_state, delta)`  
   - `handle_user_time_instruction(user_action, world_state)`  
   - rules enforcing:
     - no autonomous time skipping,  
     - background time vs perceptual time separation.

2. MUST:

   - treat explicit user time instructions as consent to compress time,  
   - ensure background processes and schedules advance correctly,  
   - prevent skipping over obviously important events,  
   - never summarise time without user action/consent.

3. Add tests:
   - no spontaneous fast-forwarding,  
   - explicit instructions cause controlled time jumps,  
   - background reality updates deterministically.

---

## Phase P7 — InformationEventManager

**Goal:** Treat information events as first-class perceptions.

Tasks:

1. Implement `InformationEventManager`:

   - identify when information events should occur based on world state and influence fields,  
   - resolve senders as Persistent vs Thin,  
   - construct structured representations for PerceptionOrchestrator.

2. Integrate with `TriggerEvaluator` and `PerceptionOrchestrator`.

3. Add tests:
   - information events fire correctly,  
   - senders treated consistently (Persistent vs Thin),  
   - messages respect determinism and context.

---

## Phase P8 — PFEELogger and Observability

**Goal:** Provide internal transparency for system owner.

Tasks:

1. Implement `PFEELogger`:

   - log:
     - active triggers,  
     - potentials resolved,  
     - whether entities were Persistent or Thin,  
     - influence fields consulted,  
     - LLM calls made (type, purpose),  
     - key decisions made by PFEE.

2. Ensure logs:

   - are not visible to in-world user,  
   - can be inspected externally via admin tools or offline analysis.

3. Add tests:
   - logging is robust and does not leak internal IDs into user-facing text,  
   - logs are complete enough to explain behaviour.

---

## Phase P9 — PFEE Test Suite

**Goal:** Comprehensive PFEE-specific tests.

Tasks:

1. Construct end-to-end tests for:

   - dog attack in park (latent potential → Thin entities → consequences),  
   - friend’s off-screen argument → future call / changed behaviour,  
   - random message from a client → Thin → possibly Persistent,  
   - repeated encounters promoting entities,  
   - gradual influence of background events into future perception.

2. Add property tests where possible:

   - same initial world state + same actions → same perception outcomes,  
   - Thin entities do not leave orphaned state,  
   - Persistent entities remain consistent across scenes.

3. Ensure PFEE tests are integrated into the main test runner and CI pipeline.

---

This PFEE plan is self-contained.  
The Builder LLM MUST follow it when implementing PFEE-specific behaviour.