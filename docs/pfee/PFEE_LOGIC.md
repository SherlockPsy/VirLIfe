# PFEE_LOGIC.md
**LOGIC AND ALGORITHMIC RULES — PERCEPTION-FIRST EXPERIENCE ENGINE (PFEE)**

This document specifies the core logic and algorithms PFEE MUST implement.  
It complements `PFEE_ARCHITECTURE.md` (structure) and `PFEE_PLAN.md` (order).

Pseudocode is indicative and MUST be made concrete in the implementation language.

---

## 1. Entity Persistence Logic (Persistent vs Thin)

### 1.1 Classification

Function (indicative):

```pseudo
function classify_entity_persistence(entity, context) -> PersistenceLevel:
    if entity.already_marked_persistent:
        return PERSISTENT

    if entity.is_core_person:  # family, close friend, therapist, etc.
        return PERSISTENT

    if entity.has_long_term_obligations_with_user:
        return PERSISTENT

    if entity.is_key_location_for_user_routines:
        return PERSISTENT

    if entity.has_been_encountered_in_multiple_salient_events:
        return PERSISTENT

    if entity.is_tied_to_biographical_memory_or_core_arcs:
        return PERSISTENT

    # default
    return EPHEMERAL

1.2 Promotion

function promote_to_persistent(entity_id):
    entity = load_entity(entity_id)
    if entity.persistence_level == PERSISTENT:
        return  # idempotent
    entity.persistence_level = PERSISTENT
    persist(entity)

Thin entities MAY be promoted when:
	•	they reappear in multiple salient scenes,
	•	they accumulate obligations or biographical salience.

⸻

2. Latent Potentials

Latent potentials are stored as structured possibilities, e.g.:

Potential:
    id
    context_type   # e.g. PARK, AIRPORT, CELEBRITY_PUBLIC, PHONE
    potential_type # e.g. DOG_ENCOUNTER, FAN_APPROACH, CLIENT_MESSAGE
    parameters     # free-form structured info

2.1 Registration

function register_potential(context, potential_type, parameters):
    potential = Potential(context_type=context.type,
                          potential_type=potential_type,
                          parameters=parameters)
    save_potential(potential)

2.2 Resolution

function resolve_potentials_for_context(context) -> list[ResolvedPotential]:
    potentials = load_potentials_matching(context)
    # Deterministic selection:
    # For now, select all that meet threshold conditions (time, salience, etc.)
    resolved = []
    for p in potentials:
        if meets_resolution_criteria(p, context):
            resolved.append(resolve_single_potential(p, context))
    return resolved

Resolution MUST be deterministic given the same inputs.

⸻

3. Influence Fields

Influence fields encode cross-time effects:

InfluenceField:
    agent_id
    mood_offset
    drive_pressures
    pending_contact_probability
    unresolved_tension_topics
    last_updated_timestamp

3.1 Update from Background

function update_influence_fields_from_background(world_state):
    for agent in world_state.persistent_agents:
        # Use background logic (not LLM) to compute deltas
        deltas = compute_background_deltas(agent, world_state)
        field = load_or_create_influence_field(agent.id)
        field = apply_deltas(field, deltas)
        persist(field)

3.2 Query

function query_influence_for_agent(agent_id) -> InfluenceSnapshot:
    return load_influence_field(agent_id)

Influence fields MUST NEVER require LLM calls.

⸻

4. Trigger Evaluation

4.1 User Action Trigger

function evaluate_user_action_trigger(user_action, world_state) -> TriggerDecision:
    if user_action is None:
        return TriggerDecision.none()

    if is_trivial_physical_action(user_action):
        return TriggerDecision.none()

    if is_internal_instruction_without_perceptual_consequences(user_action):
        # e.g. "show logs", out-of-world command
        return TriggerDecision.none()

    # Social/interpretive actions:
    if action_targets_agent_or_entity(user_action, world_state):
        return TriggerDecision.perception_required(reason="user_action_social")

    if action_changes_context_meaningfully(user_action, world_state):
        return TriggerDecision.perception_required(reason="user_action_context_change")

    return TriggerDecision.none()

4.2 Agent Initiative

function evaluate_agent_initiative_triggers(world_state) -> list[TriggerDecision]:
    decisions = []
    for agent in world_state.persistent_agents_present_with_user:
        if agent_has_initiative_to_act(agent, world_state):
            decisions.append(TriggerDecision.perception_required(
                reason="agent_initiative", agent_id=agent.id))
    return decisions

4.3 Interruptions

function evaluate_interruption_triggers(world_state) -> list[TriggerDecision]:
    context = extract_current_context(world_state)
    resolved_potentials = resolve_potentials_for_context(context)
    decisions = []
    for rp in resolved_potentials:
        if rp.is_interruptive:
            decisions.append(TriggerDecision.perception_required(
                reason="interruption", potential_id=rp.id))
    return decisions

4.4 Information Events

function evaluate_info_event_triggers(world_state) -> list[TriggerDecision]:
    events = compute_due_information_events(world_state)
    decisions = []
    for ev in events:
        decisions.append(TriggerDecision.perception_required(
            reason="info_event", info_event_id=ev.id))
    return decisions

4.5 Environmental/Atmospheric Shifts

function evaluate_environment_triggers(world_state) -> list[TriggerDecision]:
    shifts = detect_environmental_shifts(world_state)
    decisions = []
    for shift in shifts:
        if shift.salience >= SALIENCE_THRESHOLD:
            decisions.append(TriggerDecision.perception_required(
                reason="environment_shift", shift_id=shift.id))
    return decisions


⸻

5. Perception Cycle

The main PFEE entrypoint:

function run_perception_cycle(world_state, optional_user_action) -> PerceptionResult:
    # 1. Evaluate triggers
    decisions = []
    decisions.append(evaluate_user_action_trigger(optional_user_action, world_state))
    decisions.extend(evaluate_agent_initiative_triggers(world_state))
    decisions.extend(evaluate_interruption_triggers(world_state))
    decisions.extend(evaluate_info_event_triggers(world_state))
    decisions.extend(evaluate_environment_triggers(world_state))

    decisions = filter_non_none(decisions)

    if decisions.empty():
        return PerceptionResult.none()

    # 2. Resolve potentials and entities
    context = extract_current_context(world_state)
    resolved_potentials = resolve_potentials_for_context(context)
    entities = instantiate_entities_from_potentials(resolved_potentials, world_state)

    # Ensure classification
    for e in entities:
        e.persistence_level = classify_entity_persistence(e, context)
        persist(e)

    # 3. Build LLM inputs
    cognition_input = build_cognition_input(world_state, decisions, entities, context)
    renderer_input  = build_renderer_input(world_state, decisions, entities, context)

    # 4. Call LLM services
    cognition_output = maybe_call_cognition(cognition_input)
    renderer_output  = call_renderer(renderer_input)

    # 5. Integrate consequences
    updated_world_state = apply_perception_outcome(
        cognition_output, renderer_output, world_state
    )

    # 6. Log
    PFEELogger.log_perception_cycle(
        decisions, resolved_potentials, entities, cognition_output, renderer_output
    )

    return PerceptionResult(
        text=renderer_output.text,
        world_state=updated_world_state
    )

The actual implementation MUST preserve:
	•	determinism,
	•	no numeric state leakage to LLMs,
	•	no entity creation bypassing PFEE.

⸻

6. Time and Continuity Logic

6.1 No Autonomous Time Skipping

function handle_user_time_instruction(user_action, world_state):
    if user_action.explicitly_requests_time_skip:
        target_time = compute_target_time_from_instruction(user_action, world_state)
        world_state = advance_background_time_to(target_time, world_state)
        return world_state
    else:
        return world_state

The system MUST NOT:
	•	compress or skip time without either:
	•	explicit user instruction, or
	•	a logically implied time-consuming action (sleep, long travel, etc.).

6.2 Background vs Perceptual Time

function advance_background_time(world_state, delta):
    # deterministic updates:
    world_state.time += delta
    update_schedules(world_state)
    update_autonomy_background(world_state)
    update_influence_fields_from_background(world_state)
    return world_state

Perceptual time is advanced only through perception cycles.

⸻

7. Consequence Integration Logic

At a high level:

function apply_perception_outcome(cognition_output, renderer_output, world_state) -> world_state:
    # 1. Apply agent utterances and actions
    if cognition_output is not None:
        world_state = apply_agent_actions(cognition_output, world_state)
        world_state = apply_stance_and_intention_shifts(cognition_output, world_state)

    # 2. Apply physical consequences from renderer_output (structured, not raw text)
    world_state = apply_physical_changes(renderer_output.struct, world_state)

    # 3. Update psychology deterministically
    world_state = update_psychology_from_events(world_state)

    # 4. Create episodic memories when salience >= threshold
    world_state = store_episodic_memories(world_state)

    # 5. Update biographical memory where applicable
    world_state = update_biographical_memory(world_state)

    # 6. Update potentials and influence fields
    world_state = update_potentials_and_influence(world_state)

    return world_state

All numeric/psychological updates MUST be computed by existing logic layer functions, not by LLM outputs directly.

⸻

8. Information Events Logic

Information events are handled like:

function compute_due_information_events(world_state) -> list[InfoEvent]:
    # purely deterministic, no LLM
    return events_due_based_on_schedules_and_influence(world_state)

Then:

function build_info_event_perception(info_event, world_state):
    sender = resolve_sender(info_event)
    sender.persistence_level = classify_entity_persistence(sender, context_for_info_event)
    persist(sender)
    # Build renderer packet including:
    # - sender identity summary
    # - message content skeleton
    # - relationship context

LLM is then used only to render the textual experience of receiving the info.

⸻

9. Contradiction Handling Logic

function validate_llm_output_against_state(output, world_state) -> ValidationResult:
    # Check for impossible presences, contradictions with known facts, etc.
    if contradicts_world_state(output, world_state):
        return ValidationResult.invalid(reason="state_conflict")
    return ValidationResult.valid()

If invalid:

function reconcile_or_regenerate(output, world_state):
    # Strategy: regenerate with stricter constraints
    # or reinterpret as misperception only if explicitly modelled

PFEE MUST NOT allow silent divergence between rendered text and authoritative state.

⸻

This logic specification provides the behavioural backbone of PFEE.
The Builder MUST implement it in a way compatible with the broader backend and tests defined in PFEE_PLAN.md.
