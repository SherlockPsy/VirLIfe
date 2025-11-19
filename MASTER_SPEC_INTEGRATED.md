# MASTER_SPEC.md  
**VIRTUAL WORLD — COMPLETE SYSTEM SPECIFICATION**  
**FULLY CLEANED • NON-SUMMARISED • BUILDER-READY • AMBIGUITY-PROOF**  
**INCLUDES BIOGRAPHICAL MEMORY SYSTEM**

======================================================================
## INTERPRETATION RULES FOR BUILDER LLM
======================================================================

These rules override all others. You MUST follow them exactly.

### 1. Normative Language  
Any sentence containing **MUST**, **MUST NOT**, **SHALL**, **SHALL NOT**, **IS REQUIRED TO**, **IS PROHIBITED FROM**  
is a binding requirement.

### 2. Examples  
Any text labelled **“Example — NON-NORMATIVE”** or **“Examples — NON-NORMATIVE”** is illustrative ONLY.  
You MUST NOT treat examples as rules.

### 3. Requirements vs Examples  
If an example contradicts a requirement, the requirement wins.

### 4. No Implicit Inference  
You MUST NOT infer requirements from patterns in examples.

### 5. No Summarisation or Simplification  
You MUST NOT compress or reinterpret normative text.

### 6. Numeric vs Semantic  
You MUST keep the separation:  
- internal substrate = numeric  
- LLM interface = semantic summaries only  
Examples NEVER override this rule.

### 7. User Non-Simulation  
You MUST NOT simulate the user’s mind.  
The user has no internal numeric state.

### 8. Single Source of Truth  
This document IS the full source of truth.  
Nothing else overrides it.

======================================================================
## PART I — SYSTEM WORLDVIEW  
(THE HUMAN REALITY OF THE SYSTEM)
======================================================================

### 1. The World Exists Independently of the User  
The world is a persistent, deterministic environment. It:
- progresses time continuously  
- updates agent location, routines, lives, arcs  
- processes environmental changes  
- continues even if the user disconnects  
- has no protagonist  

The system MUST NOT pause for the user.

### 2. The Substrate: Deterministic Psychology  
All **simulated agents** share:
- mood  
- drives  
- personality traits  
- relationships  
- arcs  
- intentions  
- energy  
- memory (episodic + biographical)  

The user MUST NOT have any of these.

### 3. Autonomy Without LLM  
Agents MUST live their lives without constant LLM use:
- schedules  
- tasks  
- movement  
- relationship drift  
- mood shifts  

Cognition LLM MUST be invoked only for meaningful events.

### 4. Cognition LLM is Event-Driven  
Triggered ONLY when:
- high emotional load  
- relational stakes  
- ambiguous decisions  
- arc-relevant events  
- drive-relevant events  

User presence alone MUST NOT trigger cognition.

### 5. Renderer is Pure Perception  
Renderer MUST:
- describe only what the perceiver senses  
- describe for user ONLY in second-person  
- never explain internal states  

### 6. World Tick is Impartial  
World MUST:
- ignore the user’s internal state  
- continue life off-screen  
- treat you as one presence among many  

### 7. On-Screen vs Off-Screen is Perceptual  
World MUST NOT freeze off-screen agents.

### 8. High Resolution Comes from Proximity  
You see more of Rebecca because you are with her often, not because the system privileges her.

### 9. Cognition Load Distribution is Uniform  
Agents MUST use cognition in proportion to their own stakes, not because of user presence.

### 10. You Are a Person in the World, Not Its Centre  
No narrative bias.  
You have real cognition.  
The world does not simulate you.

======================================================================
## PART II — CLEAN ARCHITECTURE SPECIFICATION
======================================================================

### 1. Entities  
- **World** — deterministic environment  
- **Simulated Agents** — have internal state  
- **User** — external mind with physical presence only  

### 2. User: Absolute Prohibitions  
System MUST NOT assign to user:
- mood  
- drives  
- personality  
- relationships (outgoing edges)  
- arcs  
- intentions  
- energy  

Agents WILL have relationship edges toward user.

### 3. Subsystems  
- World Engine  
- Autonomy Engine  
- Cognition Service (LLM)  
- Renderer Service (LLM)  
- Gateway  
- Persistence Layer  

Each MUST obey strict boundary rules.

----------------------------------------------------------------------
### 4. World Engine
----------------------------------------------------------------------

World Engine MUST:
- maintain time  
- handle locations and movement  
- apply environmental rules  
- update physical state  
- NEVER use LLM  
- NEVER simulate the user’s mind  

It MUST be fully deterministic.

----------------------------------------------------------------------
### 5. Simulated Agent Model
----------------------------------------------------------------------

Each agent MUST have:
- mood  
- drives  
- personality  
- relationships  
- arcs  
- intentions  
- episodic memories  
- **biographical memory**  
- energy  

User MUST NOT have these.

----------------------------------------------------------------------
### 6. Autonomy Engine  
----------------------------------------------------------------------

Autonomy Engine MUST:
- execute routines  
- update numeric psychology  
- choose low-level behaviour  
- operate deterministically  

LLM MUST NOT be used for trivial choices.

----------------------------------------------------------------------
### 7. Cognition Service (LLM)
----------------------------------------------------------------------

Cognition MUST be triggered ONLY for meaningful events.

Input MUST include:
- semantic summaries  
- relevant memories  
- arcs  
- intentions  
- NO numeric state  
- NO user internal state  

Output MUST be:
- utterance  
- physical action  
- stance/intent shifts  

Numeric changes MUST be produced deterministically.

----------------------------------------------------------------------
### 8. Renderer Service (LLM)
----------------------------------------------------------------------

Renderer MUST:
- render ONLY perception  
- speak to user in second person  
- speak in first person for agent POV  
- avoid omniscience  
- avoid emotional explanations  
- NEVER describe user internal state  

----------------------------------------------------------------------
### 9. Gateway
----------------------------------------------------------------------

Gateway MUST:
- parse user actions  
- update world  
- trigger cognition when required  
- call renderer  

Gateway MUST NOT infer user psychology.

----------------------------------------------------------------------
### 10. Persistence Layer
----------------------------------------------------------------------

Persistence MUST store:
- world state  
- agent internal state  
- episodic memories  
- biographical memories  
- relationships  
- arcs  
- logs  

Persistence MUST NOT store:
- user psychology  
- inferred emotions of user  

======================================================================
## PART III — LOGIC LAYER (FULL SPEC)
======================================================================

This is the deterministic psychological substrate.

All rules below are normative.

----------------------------------------------------------------------
### SECTION 1 — STATE VARIABLES
----------------------------------------------------------------------

Agents MUST store:

#### 1.1 Mood
- valence ∈ [-1.0, +1.0]  
- arousal ∈ [0.0, 1.0]

#### 1.2 Drives
Five drives MUST exist:
- relatedness  
- autonomy  
- competence  
- novelty  
- safety  

Each with:
- level ∈ [0.0, 1.0]  
- sensitivity ∈ [0.5, 1.5]  

#### 1.3 Personality
- sociability  
- emotional_volatility  
- dominance  
- conscientiousness  
- openness  

#### 1.4 Relationship Edges
- warmth  
- trust  
- tension  
- attraction  
- familiarity  
- comfort  
- volatility  

#### 1.5 Arcs
- intensity  
- valence_bias  
- topic_vector  
- decay_rate  

#### 1.6 Intentions
- priority  
- horizon  
- type  
- OPTIONAL stability  

#### 1.7 Energy
- energy ∈ [0,1]

#### 1.8 Episodic Memory
- description  
- timestamp  
- salience  
- tags  

#### 1.9 **Biographical Memory (NEW, NORMATIVE)**  
Agents MUST maintain a structured set of long-term personal facts about others, including the user.

Biographical memory MUST include facts such as:
- factual background (age, family structure, past experiences explicitly shared)  
- long-term preferences (e.g., “he dislikes dishonesty”)  
- relational constants (e.g., “she always tries to avoid conflict when tired”)  
- identity themes (“he values independence”)  

BIOGRAPHICAL MEMORY RULES (NORMATIVE)
- MUST persist across the entire simulation  
- MUST accumulate naturally from long-term interaction  
- MUST influence interpretation of new events  
- MUST be deterministic  
- MUST NOT contain user internal states  

This system MUST co-exist with episodic memory.

----------------------------------------------------------------------
### SECTION 2 — GLOBAL DYNAMICS (THE LAWS)
----------------------------------------------------------------------

The following laws MUST govern all simulated agents continuously and deterministically.  
These laws MUST NOT be overridden by examples, special cases, or narrative logic.

------------------------------------------------------------
#### LAW 1 — DRIVES MOVE TOWARD OR AWAY FROM SATISFACTION
------------------------------------------------------------

Whenever an event occurs that affects any drive, the system MUST apply:

d_level ← clamp(d_level + effect(event, drive) * d_sensitivity)

Where:

- **effect(event, drive)** is a deterministic mapping in [-1, +1]  
- **d_sensitivity** modulates the magnitude  
- clamp() restricts values to [0.0, 1.0]

Drives MUST drift toward a baseline over time.

**Examples — NON-NORMATIVE:**  
- Comforting conversation → relatedness decreases (need satisfied).  
- Being blocked or controlled → autonomy increases.  
- A moment of success → competence decreases (need satisfied).  
These illustrate patterns, not rules.

------------------------------------------------------------
#### LAW 2 — MOOD REFLECTS RECENT DRIVE HISTORY
------------------------------------------------------------

Valence MUST update as:

valence ← clamp(valence + k_val * weighted_drive_change)

Arousal MUST update with:

- novelty  
- emotional shock  
- conflict  
- cognitive load  

Arousal MUST slowly drift toward baseline.

Personality.emotional_volatility MUST scale sensitivity.

------------------------------------------------------------
#### LAW 3 — ARCS DECAY UNLESS REINFORCED
------------------------------------------------------------

Arcs MUST decay according to:

arc.intensity ← arc.intensity * (1 - arc.decay_rate * Δt)

If a new event semantically matches arc.topic_vector, intensity MUST increase.

Arcs MUST NOT script behaviour; they bias tendencies.

------------------------------------------------------------
#### LAW 4 — RELATIONSHIPS DRIFT OVER TIME
------------------------------------------------------------

Without events:

- tension MUST decay  
- warmth MUST slowly move toward neutral  
- trust MUST slowly move toward neutral  
- familiarity MUST slowly increase during co-presence and decay during absence  
- comfort MUST track long-term warmth+trust+safety patterns  

With events, each dimension MUST update deterministically and be scaled by volatility.

**Examples — NON-NORMATIVE:**  
- A kind gesture → warmth↑ trust↑ tension↓  
- Dismissiveness → warmth↓  
- An inconsistency → trust↓  

These are NOT rules; they illustrate the update pattern.

------------------------------------------------------------
#### LAW 5 — ENERGY DEPLETES AND RESTORES
------------------------------------------------------------

energy MUST decrease during:

- conflict  
- focused work  
- prolonged wakefulness  
- high cognitive load  

energy MUST increase during:

- rest  
- sleep  
- low-stimulation periods  

Low energy MUST raise cognition thresholds.

------------------------------------------------------------
#### LAW 6 — DECISION PRESSURE IS A WEIGHTED COMBINATION
------------------------------------------------------------

For every behavioural choice, the system MUST compute:

effective_tendency = f(drives, mood, personality, arcs, relationships, energy)

This MUST be the universal pattern for:

- approach vs withdrawal  
- speak vs silence  
- escalate vs de-escalate  
- engage vs ignore  
- remain vs leave  

No single variable may dominate unless its value is extreme.

======================================================================
### SECTION 3 — DRIVE UPDATE LOGIC (FULL DETAIL)
======================================================================

### 3.1 Event Mapping
Every event MUST map into drive effects ∈ [-1, +1] for each drive.

This mapping MUST be deterministic.

**Examples — NON-NORMATIVE:**  
- Harsh criticism → competence↑ safety↑  
- Loving reassurance → relatedness↓ safety↓  
- Novel, exciting plan → novelty↓ arousal↑  

Do NOT treat these as rules; the mapping pattern is the requirement.

### 3.2 Baseline Drift  
Drives MUST drift toward a baseline level (≈0.3–0.4).

d_level ← d_level + (baseline - d_level) * drift_factor

======================================================================
### SECTION 4 — MOOD DYNAMICS (FULL DETAIL)
======================================================================

### 4.1 Valence
Valence MUST be calculated, never assigned arbitrarily.

### 4.2 Arousal
Arousal MUST increase with emotional intensity and novelty, and decay toward baseline.

======================================================================
### SECTION 5 — ARC DYNAMICS
======================================================================

Arcs MUST:

- be created based on clusters of semantically related events  
- intensify when matched  
- decay when inactive  
- influence tendencies (not produce direct behaviours)  

Arc logic MUST be deterministic.

======================================================================
### SECTION 6 — RELATIONSHIP DYNAMICS
======================================================================

Relationship edges MUST update for every interaction.

### 6.1 Event-Based Updates
Updates MUST depend on:
- event classification  
- volatility  
- drive activation  
- existing warmth/trust/tension  

### 6.2 Drift
Edges MUST drift as defined previously.

======================================================================
### SECTION 7 — MEMORY SYSTEM  
(EPISODIC + **BIOGRAPHICAL MEMORY SYSTEM**)
======================================================================

### 7.1 Episodic Memory (Events)
Agents MUST store episodic memories when event_importance ≥ threshold.

Each memory MUST store:
- description  
- timestamp  
- salience  
- semantic tags  

### 7.2 Episodic Memory Retrieval
Retrieval MUST consider:
- semantic similarity  
- recency  
- salience  

### 7.3 Biographical Memory (Lifelong Personal Knowledge)

Biographical memory MUST be a dedicated subsystem storing long-term personal facts.

#### Biographical Memory MUST store:
- declared background facts (place of origin, age, profession, losses, milestones)  
- stable traits inferred from interaction (e.g., “he likes straightforward answers”)  
- long-term preferences (“she hates being rushed”)  
- stable relational patterns (“he becomes distant when overwhelmed”)  
- recurring behavioural themes (“she avoids conflict when tired”)  

#### Biographical Memory MUST NOT store:
- user’s internal emotions  
- user’s unexpressed thoughts  
- any psychological details not derived from explicit behaviour  

#### Biographical Memory MUST influence:
- interpretation of events  
- trust thresholds  
- warmth/tension response  
- arc activation  
- drive relevance  

This subsystem MUST grow naturally over the simulation lifetime.

======================================================================
### SECTION 8 — SALIENCE & ATTENTION
======================================================================

Salience MUST be computed from:
- sensory prominence  
- relational stakes  
- drive pressure  
- arc intensity  
- novelty  
- user presence (ONE factor, not privileged)  

======================================================================
### SECTION 9 — COGNITION TRIGGER LOGIC
======================================================================

Meaningfulness score MUST be computed as:

M = w1max(salience) +
w2max(drive pressure) +
w3max(arc intensity) +
w4relational stakes -
w5*(1 - energy)

Cognition MUST trigger when:
- M ≥ threshold  
- AND event is not trivial  
- AND cooldown is respected  

======================================================================
### SECTION 10 — LOW-LEVEL BEHAVIOUR (NON-LLM)
======================================================================

When cognition does not trigger, agents MUST behave via deterministic tendencies.

**Examples — NON-NORMATIVE:**  
- high relatedness → incline toward proximity  
- high tension → incline toward distancing  
- low energy → minimal engagement  

These are NOT rules; they illustrate the required pattern.

======================================================================
### SECTION 11 — RENDERER TRIGGERS
======================================================================

Renderer MUST output perception when:
- perceiver location changes  
- agents enter/leave  
- someone acts toward perceiver  
- salient sensory event happens  
- proxemics change  
- atmosphere shifts  

======================================================================
### SECTION 12 — NUMERIC → SEMANTIC MAPPING
======================================================================

LLMs MUST NEVER see numeric internal state.

Renderer/Cognition MUST receive:
- templated semantic summaries  
- derived deterministically  

**Examples — NON-NORMATIVE:**  
- “She feels uneasy” ← (low trust + high tension)  
- “She feels warmly toward him” ← (high warmth + high comfort)  

These are templates, not rules.

======================================================================
### SECTION 13 — LLM OUTPUT → NUMERIC UPDATE
======================================================================

LLM output MUST be parsed into:
- utterance  
- action  
- stance shift  
- intention manipulation  

Numeric updates MUST be deterministic mappings.

======================================================================
### SECTION 14 — OPENNESS
======================================================================

System MUST allow:
- neutral actions  
- seeded pseudo-random variation  
- simplicity in trivial contexts  

No enumeration of life events.

======================================================================
### SECTION 15 — USER NON-SIMULATION (ABSOLUTE RULE)
======================================================================

User MUST NOT have:
- mood  
- drives  
- personality  
- arcs  
- intentions  
- energy  
- relationship edges from user → others  

Agents may store:
- relationship edges toward user  
- episodic memories involving user  
- biographical facts about user that you explicitly reveal  

Agents MUST NOT store or infer your unseen internal state.

======================================================================
## PART IIA — PERSONALITY COMPILER & CHARACTER INITIALIZATION
======================================================================

### 1. Purpose of This Subsystem

The Personality Compiler is a mandatory subsystem responsible for transforming human-readable personality materials (e.g., personality templates, person-specific fingerprints, relationship matrices) into:

- stable personality summaries (semantic, cached)
- numeric personality kernels (deterministic, substrate-level)
- domain-specific personality packs (emotion, conflict, humour, intimacy)
- dynamic activation packets (moment-to-moment behavioural tendencies)
- cached context fragments used by LLM cognition and rendering
- initialization data for each simulated agent at world creation

It serves as the bridge between:

- human-defined personality material  
and  
- the deterministic numeric substrate + semantic summaries used at runtime.

### 2. Responsibilities

The Personality Compiler MUST:

1. Accept for each agent:
   - a weighted mixture of foundational personality templates  
   - an optional personality fingerprint (rich text or JSON)
   - an optional relationship map  
   - optional notes about intimacy/sexuality (for adults only; used exclusively by adult-capable renderer)

2. Produce:
   - a stable personality summary (approximately 150–250 tokens)  
   - a personality kernel (numeric vector)  
   - domain summaries (emotion, conflict, humour, intimacy)  
   - a stable semantic cache for slow-changing traits  
   - an initial biographical memory pack  
   - an initial relationship profile toward relevant people (warmth, trust, tension, familiarity, comfort)

3. Store:
   - numeric kernel  
   - stable summaries  
   - domain summaries  
   - cached fragments  
   - initialization metadata  

in persistence for later use.

4. Generate deterministic personality outputs.  
   - Personality kernels MUST be computed via deterministic mixing functions.  
   - Domain summaries MUST be derived from kernels and fingerprints.  
   - Cached fragments MUST only be regenerated when inputs change.

### 3. Non-Responsibilities

The Personality Compiler MUST NOT:

- produce non-deterministic personality generation  
- create new psychological variables beyond those defined in this specification  
- overwrite numeric drives, mood, arcs, or relationships  
- call any LLM  
- allow fingerprint text to be sent directly to cognition or renderer LLMs  
- generate sexual content (that is reserved for adult-capable renderers)

### 4. Personality Templates

The system MAY support N foundational personality templates (for example, 15 templates).  
Each template MUST define:

- stable tendencies  
- communication patterns  
- conflict styles  
- humour patterns  
- intimacy preferences (for adult contexts)  
- comfort levels  
- emotional regulation tendencies  
- worldview tendencies  

These templates MUST be stored as structured data (e.g., JSON or YAML), not as arbitrary prose blobs.

### 5. Template Mixing

Each agent MUST reference a mixture of templates, for example:

```json
{
  "Nurturer": 0.35,
  "Mediator": 0.20,
  "Thinker": 0.10
}
```

Template mixtures MUST:

- be normalized (weights sum to 1.0)  
- be deterministic  
- be used to compute the personality kernel

### 6. Personality Kernel (Numeric)

The personality kernel MUST include numeric variables describing, at minimum:

- sociability tendency  
- emotional volatility  
- dominance  
- conscientiousness  
- openness  
- directness vs indirectness  
- introspection tendency  
- humour activation  
- conflict avoidance tendency  
- intimacy assertiveness (adults only)  
- intimacy responsiveness (adults only)  
- trust baseline  
- forgiveness baseline  

The exact list MUST remain stable across the system and be documented in the implementation.

### 7. Stable Personality Summary (Semantic)

The compiler MUST generate a stable semantic summary (approximately 150–250 tokens) that describes:

- communication style  
- emotional style  
- how the person typically reacts to stress  
- what they fear losing  
- how they connect to others  
- how they argue  
- what makes them soften  
- how they recover from conflict  

This summary MUST:

- be cached and persisted  
- be regenerated ONLY when the personality kernel or fingerprint changes  
- be provided to cognition and renderer for every call that involves this agent

### 8. Domain Summaries

The compiler MUST generate domain summaries for at least:

- emotion regulation  
- conflict style  
- humour style  
- communication style  
- intimacy/sexuality style (adult scenes ONLY)

Each domain summary MUST:

- be small (approximately 50–120 tokens)  
- be cached and persisted  
- be used by cognition and/or renderer when relevant  
- never be overwritten directly by LLM output

### 9. Dynamic Activation Packets

At runtime, agents require short-lived adjustments to their personality expression.

Dynamic activation packets MUST be derived deterministically from:

- drives  
- mood  
- arcs  
- relevant episodic memories  
- biographical memories  
- relationship edges  
- personality kernel  

Dynamic packets:

- MUST NOT involve any LLM calls  
- MUST be short (approximately 30–80 tokens when converted to semantic form)  
- MUST be passed into cognition LLM calls alongside the stable and domain summaries

### 10. Integration With Cognition Flow

For each cognition call, the cognition LLM MUST receive, in semantic form:

1. Stable personality summary  
2. Domain summaries (at least those relevant to the current event)  
3. Dynamic activation packet  
4. Relationship summaries  
5. Relevant memory snippets  
6. Current event context  

Cognition MUST be implemented as described in `docs/cognition_flow.md`, with the Personality Compiler outputs supplying the personality-related context.

### 11. Integration With Renderer

The renderer LLM MUST receive, in addition to the perception packet and event context:

- stable personality summary  
- relevant domain summaries  
- dynamic activation packet  

Renderer MUST NOT see intimacy/sexuality domain summaries unless:

- the renderer is an adult-capable model, AND  
- the current scene is explicitly marked as sexual/intimate in the world state.

### 12. Initialization of Agents

At world creation, the Personality Compiler MUST:

- generate each agent’s personality kernel  
- generate all stable and domain summaries  
- cache all fragments  
- create initial relationship edges (based on provided relationship maps and template-derived defaults)  
- create initial biographical memory packs  
- write an initialization log that can be used for debugging and tests

### 13. Persistence Rules

The persistence layer MUST store, for each agent:

- personality kernel (numeric vector)  
- stable personality summary (text)  
- domain summaries (text)  
- cached context fragments  
- template mixture weights  
- optional fingerprint references  

These fields MUST be persisted across restarts and MUST be part of any world snapshot.

### 14. Test Requirements

The test suite MUST include, at minimum:

- kernel determinism tests (same inputs → same kernel)  
- summary determinism tests (same kernel+fingerprint → same summaries)  
- caching behaviour tests (summaries recompute only when inputs change)  
- integration tests verifying:
  - cognition receives personality packets  
  - renderer receives personality packets  
  - raw fingerprint text is NEVER included in LLM prompts  

These tests MUST be linked back to the relevant clauses in this section of the specification.

