## PART PFEE — PERCEPTION-FIRST EXPERIENCE ENGINE  
(**PFEE IS NORMATIVE AND INTEGRATES WITH ALL EXISTING SECTIONS**)

### 0. Scope and Purpose (Normative)

The Perception-First Experience Engine (PFEE) defines **how the simulated world is experienced**, not how it is fully simulated.

PFEE governs:

- when and why perception is generated,  
- how background reality influences future perception,  
- how new things may appear,  
- how entities are treated as persistent vs ephemeral,  
- how time is experienced subjectively,  
- how renderer output affects world state,  
- how information events are handled,  
- how contradictions are resolved,  
- how neutrality for therapeutic use is preserved,  
- and how the system remains auditable without breaking immersion.

PFEE is **experience-first** and MUST be understood as:

> The system does NOT simulate “the entire world”.  
> The system simulates **the user’s experience of the world**  
> and the subset of reality that affects that experience now or later.

All PFEE rules are **normative** unless explicitly labelled “Example — NON-NORMATIVE”.

---

### 1. Core Ontological Commitments (Normative)

1. The world state (Deep Reality + Thin Reality + background processes)  
   is maintained by non-LLM subsystems (World Engine, Autonomy, Persistence, etc.).

2. PFEE defines **when and how the user becomes aware of parts of this world**,  
   through renderer output and cognition LLM calls.

3. PFEE MUST NOT:
   - introduce a separate “story system”,  
   - introduce narrative arcs independent of world state,  
   - treat the user as a scripted protagonist,  
   - fabricate events purely for drama.

4. PFEE MUST operate under all global constraints already defined:
   - determinism,  
   - numeric vs semantic separation,  
   - user non-simulation,  
   - no rewind/replay,  
   - single world, no resets except via explicit system tools.

---

### 2. Deep Reality vs Thin Reality (Normative)

PFEE builds on two ontological layers:

#### 2.1 Deep Reality (Persistent Layer)

Deep Reality contains all **persistent entities** and structures that:

- have enduring identity,  
- can affect the user’s perception now or later,  
- have continuity across time.

This includes, at minimum:

- key people (e.g. Rebecca, daughter, close friends, recurring contacts),  
- the user’s home and other key places,  
- recurring workplaces, usual cafés, therapists’ offices, etc.,  
- persistent objects (e.g. user’s car, phone, keys, important belongings),  
- stable organisations (employers, universities, significant institutions),  
- long-term relationships and calendars/obligations,  
- arcs and biographical memories as already defined in MASTER_SPEC.

Entities in Deep Reality MUST:

- be uniquely identifiable,  
- be persisted across sessions,  
- participate in deterministic updates (psychology, obligations, schedules),  
- be available as context for PFEE.

#### 2.2 Thin Reality (Contextual Layer)

Thin Reality contains **ephemeral entities** that exist **only as long as they are needed** to support a specific experience.

Thin entities include, but are not limited to:

- strangers in public spaces,  
- waiters, baristas, cashiers, receptionists, security staff, drivers,  
- one-off photographers, directors, assistants, staff for a single event,  
- random dogs, passersby, minor bystanders, crowds,  
- disposable or incidental objects (cups, one-off bags, brochures, receipts),  
- one-off micro-locations (corridor, generic waiting area, random bench).

Thin entities MUST:

- be created deterministically when a perception requires them,  
- have only minimal state needed for that moment,  
- not have full internal psychology (mood, drives, arcs),  
- not have off-screen autonomous lives,  
- be allowed to be discarded once their role in the experience ends.

A thin entity MAY be **promoted** into Deep Reality if it later meets the persistence criteria defined in §3.

#### 2.3 PFEE Responsibility

PFEE MUST:

- treat Deep Reality as the authoritative source for persistent entities,  
- treat Thin Reality as scene-local scaffolding for realism,  
- NEVER let the LLM “invent” entities without the world engine first instantiating a Deep or Thin entity.

---

### 3. Persistent vs Ephemeral Entities (Universal Rule, Normative)

All entities in the world MUST be classified as either:

- **Persistent (Deep)**:  
  Can affect the user’s life again, across time.

- **Ephemeral (Thin)**:  
  Exist only to support one or a small number of local experiences and then MAY be removed.

This rule applies **universally** to:

- people,  
- items/objects,  
- locations,  
- roles (e.g. director, photographer, barista),  
- organisations,  
- information sources (e.g. recurring vs one-off customers).

#### 3.1 Persistence Criteria

An entity MUST be considered **Persistent** if one or more of the following holds:

- It is directly tied to the user’s continuing life (family, close friends, romantic partners, therapists, recurring colleagues).  
- It is tied to recurring obligations or schedules (e.g. workplace, therapist office, usual gym, regular café).  
- It has or is likely to have ongoing emotional, psychological, or relational impact on the user.  
- It is explicitly referenced in biographical memory or long-term plans/arcs.  
- It is encountered repeatedly in a way that changes future possibilities (e.g. recurring client).

An entity SHOULD be considered **Ephemeral** if:

- its only purpose is to make a specific scene realistic (e.g. random waiter, random stranger),  
- it has no continuing obligations or explicit future references,  
- it is unlikely to affect the user’s life beyond the immediate interaction,  
- it is equivalent to a background detail (crowd members, passersby).

Promotion rule:

- A Thin entity MUST be promoted to Persistent if:  
  - it reappears in multiple salient scenes, or  
  - it acquires obligations or biographical relevance, or  
  - it is explicitly important to the user or to a Persistent agent.

The world engine, NOT the LLM, MUST perform this classification and promotion.

---

### 4. Background Reality vs Foreground Perception (Normative)

PFEE distinguishes:

- **Background Reality**:  
  Everything that is happening in the world but is not currently perceived.

- **Foreground Perception**:  
  What the user actually experiences at a given moment (what appears on screen).

#### 4.1 Background Reality

Background Reality MUST include:

- other people’s routines, arguments, decisions, emotional shifts,  
- logistics (travel, delays, deliveries, traffic),  
- institutional changes (policy changes, scheduling changes),  
- all ongoing deterministic updates defined in existing Logic Layer.

Background Reality:

- MUST be computed deterministically and LLM-free,  
- MUST be allowed to run regardless of whether the user is active,  
- MUST be able to produce future influence on the user (see §8).

#### 4.2 Foreground Perception

Foreground Perception is the set of:

- sensory-like descriptions,  
- dialogue,  
- actions directed at the user or within their awareness,  
- informational content delivered to the user (messages, feeds, notifications).

Foreground MUST be generated **only** when PFEE determines that:

- something has become perceivable to the user,  
- or the user explicitly requests information or action.

LLM calls MUST ONLY be made to support Foreground Perception and/or agent cognition as already constrained by MASTER_SPEC.

---

### 5. Latent Potentials (Normative)

The world MUST maintain **latent potentials**: structured possibilities that MAY be instantiated later into Thin or Persistent entities or events.

Latent potentials are attached to:

- locations (e.g. parks, cafés, airports, streets),  
- roles and statuses (e.g. Rebecca as celebrity, user as client, etc.),  
- ongoing obligations and arcs,  
- environmental and institutional systems (e.g. transport, deliveries).

Examples — NON-NORMATIVE:

- A park potential: dogs, joggers, families, minor incidents.  
- A celebrity in public: recognition, selfies, paparazzi.  
- A phone: incoming messages from known or unknown contacts.  
- An airport: delays, announcements, staff instructions.

PFEE MUST enforce:

- Latent potentials do NOT require LLM calls.  
- Latent potentials are only resolved into concrete entities or events when:
  - a perception trigger occurs (§6), and  
  - context requires a specific instance.

When resolving a latent potential, the world engine MUST:

- deterministically choose whether to instantiate:
  - a new Thin entity, or  
  - an existing Persistent entity, or  
  - promote a Thin entity to Persistent (if thresholds are met).

The LLM MUST NOT independently create new entities or “types of things” outside these mechanisms.

---

### 6. Perception Triggers & LLM Invocation (Normative)

PFEE defines **when** perception MUST be generated and thus when an LLM may be invoked.

The LLM MUST ONLY be called when at least one of the following triggers is active:

#### 6.1 Trigger 1 — User Action Requiring Interpretation

A user action MUST trigger perception and/or cognition if and only if:

- it is directed toward another person or entity,  
- or it has social, psychological, or situational meaning that requires interpretation.

Non-LLM, deterministic rendering MUST handle:

- trivial movement,  
- neutral physical actions without social consequence,  
- routine manipulations (walking, picking up a glass, moving across a room),  
- entering/exiting spaces without any meaningful change of context.

Examples — NON-NORMATIVE:

- “I walk across the room.” → Renderer may describe this without LLM.  
- “I say to Rebecca: ‘We need to talk.’” → MUST trigger cognition and perception.

PFEE MUST NOT interpret “every user action” as a mandatory LLM call.

#### 6.2 Trigger 2 — Agent Initiative

A persistent agent (e.g. Rebecca, daughter, close friend) MAY act independently of user input.

PFEE MUST trigger cognition + perception when:

- an agent chooses to speak to the user,  
- an agent does something salient toward or near the user,  
- an agent’s mood/drive combination crosses a threshold leading to visible behaviour.

This behaviour MUST be grounded in:

- the existing logic layer (drives, mood, relationships, arcs),  
- background reality,  
- the PFEE rules for Perception.

#### 6.3 Trigger 3 — Interruptions

Interruptions are perceptual intrusions that demand attention, such as:

- someone knocking at the door,  
- a dog running toward the user,  
- an object dropping loudly,  
- a stranger approaching,  
- staff arriving with a drink,  
- an announcement in an airport,  
- traffic screeching,  
- an unexpected phone call.

PFEE MUST cause an LLM-based render when an interruption enters the user’s perceptual field.

#### 6.4 Trigger 4 — Information Events

Information events are **non-physical** but perceptible content, such as:

- text messages, emails, app notifications, calendar reminders,  
- news headlines seen by the user,  
- social media content,  
- system messages the user explicitly checks (e.g. bank notifications).

Information events MUST be treated as perception and MAY trigger LLM calls to render:

- content of the message,  
- context (who sends it, relationship, timing),  
- emotional relevance.

Information sources MUST follow the same Persistent/Thin rules as other entities (e.g. recurring client vs one-off contact).

#### 6.5 Trigger 5 — Environmental/Atmospheric Shift

PFEE MUST trigger perception when:

- something in the environment changes in a way that becomes meaningfully noticeable,  
- or the atmosphere of the scene shifts (tension rises/falls, quiet settles, crowd noise changes).

Examples — NON-NORMATIVE:

- Sudden silence in a previously noisy room.  
- A storm starting or ending.  
- The sense that Rebecca has withdrawn or softened, visible through body language.

PFEE MUST ensure atmospheric shifts are rendered only when they cross a salience threshold (see §8).

---

### 7. Subjective Time & Continuity (Normative)

PFEE MUST model **time as experienced by the user**, not as an abstract simulation.

#### 7.1 No Autonomous Time Skipping

The system MUST NOT autonomously:

- fast-forward the user’s experience,  
- summarise long intervals (“the rest of the day passes…”)  
- jump from one time to another,  

UNLESS:

- the user explicitly requests or implies such a jump, OR  
- the user’s action logically entails a time transition (e.g. “I sleep until morning,” “I drive to Manchester.”).

#### 7.2 Background Time vs Perceptual Time

Background time MUST progress deterministically, independent of user actions.

Perceptual time (what is rendered) MUST:

- reflect a continuous experience from the user’s point of view,  
- not omit intervals without the user’s explicit consent or action.

If nothing salient happens for a period, PFEE MAY render this as:

- **low-detail continuity** (e.g., “You spend an hour quietly reading.”),  
but MUST only do so in response to user actions or requests that imply passage of time, not spontaneously.

#### 7.3 Time-Related User Control

Whenever the user issues an explicit instruction about time (e.g. “skip to tomorrow”, “I stay here until she returns”), PFEE MUST:

- treat this as consent to compress the subjective timeline,  
- ensure background reality is updated accordingly,  
- avoid skipping over obviously important events that MUST affect the user directly.

---

### 8. Cross-Time Consequences & Future Hooks (Normative)

PFEE MUST ensure that **background events** can shape **future perceptions**.

#### 8.1 Influence Fields

Persistent agents and systems (e.g. calendar, obligations, institutions) MUST maintain latent “influence fields” that encode:

- mood/drive changes,  
- updated intentions,  
- changed availability,  
- new obligations or cancelled obligations,  
- potential future contact (e.g. someone intending to call the user),  
- ongoing unresolved tensions.

These fields MUST:

- be updated by background reality and autonomy logic,  
- not require LLM calls,  
- be referenced by PFEE when selecting future triggers and potentials.

#### 8.2 Future Hook Resolution

When a perception trigger is needed, PFEE MUST:

- consult these influence fields,  
- determine whether a pending influence (e.g. friend after an argument) should manifest as:
  - a text message,  
  - a phone call,  
  - a visit,  
  - a changed mood when meeting, etc.

PFEE MUST ensure that:

- past unseen events can affect how people behave when the user next encounters them,  
- without needing to render those background events themselves.

---

### 9. Renderer Output Integration (Normative)

Renderer output (text shown to the user) is **ephemeral**,  
but its **consequences MUST NOT be ephemeral**.

For every rendered moment, PFEE MUST ensure:

1. **World State Updates**  
   - Locations, presence, objects, and situational facts MUST be updated in world state.

2. **Agent Psychology Updates**  
   - Persistent agents’ numeric state (mood, drives, relationship edges, arcs) MUST be updated deterministically based on the event,  
   - NOT directly from the text, but from the structured output channels defined in cognition/renderer interfaces.

3. **Memory Updates**  
   - Episodic memories MUST be stored when salience thresholds are met (as already defined in MASTER_SPEC).  
   - Biographical memories MAY be updated when stable patterns or facts are reinforced.

4. **Consequences Persist**  
   - Injuries, broken objects, lost possessions, promises made, insults exchanged, decisions taken, etc. MUST be stored as part of world state or memory,  
   - even when the Thin entities involved are discarded.

5. **Potential Updates**  
   - Latent potentials and influence fields MUST be adjusted to reflect what is now more or less likely to occur in the future.

Renderer output text itself does NOT need to be stored verbatim,  
but the consequences of what happened MUST be.

---

### 10. Information Events as Perception (Normative)

PFEE MUST treat information events (digital or informational inputs) as first-class perceptions.

For any information event:

- The sender/source MUST be a Persistent or Thin entity as per §3.  
- The content MUST be rendered via the LLM using:
  - world state,  
  - influence fields,  
  - prior interactions,  
  - relationship context.

Information events MUST:

- obey the same determinism and non-hallucination rules,  
- NOT fabricate new contacts or organisations outside the Persistent/Thin + potentials framework.

---

### 11. Error Handling & Contradiction Resolution (Normative)

PFEE MUST define how to handle contradictions between LLM output and world state.

#### 11.1 World State Authority

World state (Deep + Thin Reality + background logic) IS authoritative.

If LLM output conflicts with world state (e.g. describes a person present who cannot logically be there, asserts a fact that contradicts persistent memory):

- The system MUST either:
  - reject and regenerate output with stricter constraints, or  
  - reinterpret as an in-world error (e.g. misperception, misremembering), but ONLY if this is itself coherently modelled.

#### 11.2 No Silent Drift

PFEE MUST NOT allow:

- silent divergence between rendered reality and world state,  
- the LLM to redefine facts that are already determined by the world engine.

Any correction/regeneration MUST remain deterministic and traceable in internal logs.

---

### 12. Therapy Neutrality (Normative)

PFEE MUST remain **neutral** with respect to the user’s comfort.

PFEE MUST NOT:

- bias outcomes to protect the user from emotional discomfort,  
- systematically skew toward positive or negative resolutions,  
- engineer “growth moments” or “lessons” as an independent goal.

PFEE MUST:

- generate experiences that are **plausible**,  
- grounded in world state, context, potentials, and influence fields,  
- neither padded for comfort nor contrived for suffering.

The therapeutic role is external: the system exists so the user’s real therapist can work with whatever emerges.

---

### 13. Observability & Internal Logging (Non-Experiential, Normative)

The system owner (the real user outside the world) MUST be able to audit why something happened.

PFEE MUST ensure that an internal logging and inspection mechanism exists which can:

- trace which latent potential was resolved into which entity/event,  
- show why a particular perception trigger fired,  
- show how an entity was classified as Persistent vs Thin,  
- show which background events influenced a future hook.

These logs:

- MUST NOT be part of the in-world user experience,  
- MUST NOT be rendered as perceptions,  
- MUST be for debugging, validation, and trust-building only.

---

### 14. PFEE and Existing Specifications (Integration Note)

PFEE MUST be implemented in coordination with:

- the Logic Layer (drives, mood, relationships, arcs, etc.),  
- the Autonomy Engine,  
- the Cognition and Renderer LLM services,  
- the Memory systems,  
- the existing numeric-semantic mapping,  
- the Persistence and World Engine modules.

In case of conflict:

- MASTER_SPEC fundamental constraints (determinism, user non-simulation, numeric-semantic separation) remain primary,  
- PFEE governs **when and how** perception occurs and how it feeds back into world state.

Examples in this section are NON-NORMATIVE and MUST NOT be treated as new rules.  
Only text explicitly labelled as rules, MUST, MUST NOT, or normative carries binding force.