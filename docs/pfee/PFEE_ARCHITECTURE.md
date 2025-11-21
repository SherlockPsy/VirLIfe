# PFEE_ARCHITECTURE.md
**PERCEPTION-FIRST EXPERIENCE ENGINE — ARCHITECTURE**

## 1. Purpose and Scope

The Perception-First Experience Engine (PFEE) is a dedicated backend subsystem that:

- mediates between the deterministic world state and all LLM-based perception/cognition,  
- ensures the system simulates the **user’s experience of the world**, not a full world simulation,  
- controls when perception is generated, what becomes visible, and how renderer output feeds back into state,  
- enforces persistent vs ephemeral entity treatment, subjective time continuity, and future influence.

PFEE is not optional. Any path that leads to perception or cognition MUST go through PFEE.

PFEE does NOT:

- simulate full physics,  
- manage low-level psychology (drives, mood, arcs — that is the Logic Layer),  
- handle UI rendering,  
- handle deployment concerns directly.

PFEE DOES:

- orchestrate perception triggers,  
- resolve latent potentials into concrete entities/events,  
- classify entities as Persistent vs Ephemeral (Deep vs Thin Reality),  
- call cognition/renderer LLMs when required,  
- integrate LLM output back into world state,  
- manage subjective time continuity,  
- manage background → future influence,  
- log decision traces for audit.

---

## 2. High-Level PFEE Components

PFEE MUST be implemented as a cohesive module or package (e.g. `pfee/`) with the following components:

1. `TriggerEvaluator`  
   - Evaluates whether a perception event should occur.  
   - Implements all trigger types:
     - user-action triggers,  
     - agent-initiative triggers,  
     - interruption triggers,  
     - information-event triggers,  
     - environmental/atmospheric shift triggers.

2. `PotentialResolver`  
   - Holds and resolves **latent potentials** for:
     - locations,  
     - roles,  
     - institutional systems (e.g. deliveries, travel),  
     - status-based potentials (celebrity, client, etc.).  
   - Decides when to instantiate Thin entities vs reusing/promoting Persistent ones.

3. `EntityPersistenceManager`  
   - Implements **Persistent vs Ephemeral (Deep vs Thin)** classification logic for:
     - people,  
     - locations,  
     - objects/items,  
     - organisations,  
     - information sources (recurring vs one-off contacts).  
   - Handles promotion (Thin → Persistent) when thresholds are reached.

4. `PerceptionOrchestrator`  
   - Central orchestrator for perception cycles.  
   - Given world state + optional user action:
     - decides whether to trigger perception,  
     - resolves entities and potentials,  
     - builds semantic context for LLMs,  
     - dispatches to cognition and/or renderer,  
     - receives structured results,  
     - passes results to consequence integrator.

5. `ConsequenceIntegrator`  
   - Applies the consequences of LLM outputs to:
     - world state (location, objects, facts),  
     - agent psychology (mood, drives, relationships, arcs) via deterministic mappings,  
     - episodic and biographical memory,  
     - latent potentials and influence fields.  
   - Ensures the **text itself** is ephemeral but **consequences persist**.

6. `TimeAndContinuityManager`  
   - Enforces **subjective time continuity**:
     - no autonomous time skipping,  
     - only explicit / implied user-driven time jumps,  
     - background time vs perceptual time separation.  
   - Coordinates with world engine for advancing background time and updating schedules.

7. `InfluenceFieldManager`  
   - Maintains **cross-time influence fields** for persistent agents and systems:
     - mood shifts,  
     - updated intentions,  
     - new or cancelled obligations,  
     - pending contacts,  
     - unresolved tensions.  
   - Serves as a source for future triggers.

8. `InformationEventManager`  
   - Manages non-physical informational events:
     - messages, emails, notifications, calendar alerts, news, social content.  
   - Resolves senders as Persistent/Thin sources.  
   - Coordinates with `PerceptionOrchestrator` to render informational perception.

9. `PFEELogger`  
   - Internal logging and traceability:
     - what potential was resolved,  
     - why a trigger fired,  
     - why an entity was treated as Persistent vs Thin,  
     - which influence fields were involved.  
   - Logs are **for system owner only**, not part of in-world perception.

---

## 3. Integration Points with Existing System

PFEE MUST integrate with:

1. **World Engine**  
   - Access to:
     - locations, presence, time, schedules, physical facts,  
     - existing persistent entities.  
   - Ability to:
     - advance background time,  
     - update world state,  
     - create/update entities.

2. **Logic Layer (Psychology & Relationships)**  
   - PFEE reads:
     - mood, drives, relationships, arcs, energy, etc.  
   - PFEE writes:
     - deterministic updates via `ConsequenceIntegrator` after LLM output.

3. **Autonomy Engine**  
   - Supplies:
     - agent initiative decisions (when someone chooses to act/speak).  
   - Gets:
     - PFEE-mediated perception outcomes that may influence further autonomy.

4. **Cognition Service (LLM)**  
   - PFEE constructs inputs:
     - stable personality summaries,  
     - domain summaries,  
     - dynamic activation packets,  
     - memory snippets,  
     - relationship context,  
     - event context.  
   - PFEE receives:
     - utterances,  
     - actions,  
     - stance/intention shifts.  
   - PFEE then updates state deterministically (no direct numeric changes from LLM).

5. **Renderer Service (LLM)**  
   - PFEE constructs perception packets:
     - who is present,  
     - what is physically happening,  
     - relevant atmospheric cues,  
     - relevant semantic context.  
   - PFEE receives:
     - second-person descriptions for the user,  
     - first-person outputs for agent POV where allowed.  
   - PFEE ensures Renderer never sees numeric state.

6. **Gateway / API Layer**  
   - All user actions MUST route through PFEE’s PerceptionOrchestrator for evaluation.  
   - Gateway MUST NOT directly call LLM services without PFEE mediation.

7. **Persistence Layer**  
   - PFEE uses persistence to:
     - read/write entity persistence flags,  
     - store influence fields,  
     - log key events and perception traces,  
     - manage Thin entities’ life cycle.

8. **UI**  
   - PFEE does NOT render UI elements.  
   - UI simply displays:
     - PFEE’s perception outputs,  
     - user’s own actions,  
     - conversation and scene history.  
   - PFEE defines what is perceptible; UI visualises it.

---

## 4. Deployment and Service Boundaries

PFEE MUST be deployable as:

- a backend module in the main backend service, OR  
- a dedicated service that exposes an internal API (e.g. `/pfee/perception`).

Requirements:

- PFEE MUST be stateless per request, relying on persistence and world engine for state.  
- PFEE MUST NOT rely on local filesystem state.  
- PFEE MUST be Railway-compatible: environment variables for configuration, Postgres (or designated DB) for state, Redis/Qdrant integration only when main architecture allows them.

---

## 5. Determinism and Non-Simulation of the User

PFEE MUST:

- be deterministic given the same world state and inputs,  
- never simulate the user’s internal psychology (no mood/drives for the user),  
- treat the user as a physical/relational presence only,  
- never generate perception that contradicts master constraints in MASTER_SPEC (determinism, numeric-semantic separation, user non-simulation).

---

## 6. Error Handling and Auditing

PFEE MUST:

- validate LLM outputs against world state,  
- reconcile or reject outputs that contradict state,  
- log all critical decisions (trigger firings, potential resolution, classification),  
- provide structured logs for external inspection (not shown to the in-world user).

This architecture document defines *what PFEE is* and *how it fits in*.  
Concrete behaviour, rules, and pseudocode are specified in `PFEE_LOGIC.md`.  
Implementation order is defined in `PFEE_PLAN.md`.  
Builder-facing instructions are defined in `PFEE_INSTRUCTIONS.md`.