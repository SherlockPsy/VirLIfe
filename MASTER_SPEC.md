# MASTER_SPEC.md  
**VIRTUAL WORLD — COMPLETE SYSTEM SPECIFICATION**  
**FULLY CLEANED • NON-SUMMARISED • BUILDER-READY • AMBIGUITY-PROOF**  
**INCLUDES BIOGRAPHICAL MEMORY SYSTEM**

======================================================================
## INTERPRETATION RULES FOR THE BUILDER LLM
======================================================================

These rules override all others. THE BUILDER LLM MUST follow them exactly.

### 1. Normative Language  
Any sentence containing **MUST**, **MUST NOT**, **SHALL**, **SHALL NOT**, **IS REQUIRED TO**, **IS PROHIBITED FROM**  
is a binding requirement for THE BUILDER LLM.

### 2. Examples  
Any text labelled **“Example — NON-NORMATIVE”** or **“Examples — NON-NORMATIVE”** is illustrative ONLY.  
THE BUILDER LLM MUST NOT treat examples as rules.

### 3. Requirements vs Examples  
If an example contradicts a requirement, the requirement wins.

### 4. No Implicit Inference  
THE BUILDER LLM MUST NOT infer requirements from patterns in examples.

### 5. No Summarisation or Simplification  
THE BUILDER LLM MUST NOT compress, reinterpret, or “optimise” normative text.  
Normative clauses MUST be implemented as written.

### 6. Numeric vs Semantic  
THE BUILDER LLM MUST keep the separation:  
- internal substrate = numeric  
- LLM interface = semantic summaries only  

Examples NEVER override this rule.

### 7. User Non-Simulation  
THE BUILDER LLM MUST NOT simulate the internal psychology of THE HUMAN USER (THE REAL PERSON).  
THE HUMAN USER has no internal numeric state anywhere in the system.

### 8. Single Source of Truth  
This document IS the full source of truth.  
Nothing else overrides it.

======================================================================
## PART I — SYSTEM WORLDVIEW  
(THE HUMAN REALITY OF THE SYSTEM)
======================================================================

### 1. The World Exists Independently of THE HUMAN USER  

The world is a persistent, deterministic environment. It:
- progresses time continuously  
- updates agent location, routines, lives, arcs  
- processes environmental changes  
- continues even if THE HUMAN USER disconnects  
- has no protagonist  

The system MUST NOT pause for THE HUMAN USER.

### 2. The Substrate: Deterministic Psychology  

All simulated agents share:
- mood  
- drives  
- personality traits  
- relationships  
- arcs  
- intentions  
- energy  
- memory (episodic + biographical)  

THE HUMAN USER MUST NOT have any of these in the system.  
No numeric variables MAY be attached to THE HUMAN USER’s mind.

### 3. Autonomy Without LLM  

Agents MUST live their lives without constant LLM use:
- schedules  
- tasks  
- movement  
- relationship drift  
- mood shifts  

Cognition LLM MUST be invoked only for meaningful events.

### 4. Cognition LLM is Event-Driven  

Cognition MUST be triggered ONLY when:
- there is high emotional load  
- there are relational stakes  
- decisions are ambiguous  
- events are arc-relevant  
- events are drive-relevant  

THE HUMAN USER’s presence alone MUST NOT trigger cognition.

### 5. Renderer is Pure Perception  

Renderer MUST:
- describe only what the perceiver senses  
- describe experiences for THE HUMAN USER in second-person POV (e.g. “you see…”, “you feel the room change…”)  
- never explain internal states as omniscient facts  

The word “you” in renderer output rules refers ONLY to THE HUMAN USER’s perceptual point of view, as experienced through the system.  
It does NOT refer to THE BUILDER LLM.

### 6. World Tick is Impartial  

The world MUST:
- ignore any hypothetical internal state of THE HUMAN USER  
- continue life off-screen  
- treat THE HUMAN USER as one presence among many  

### 7. On-Screen vs Off-Screen is Perceptual  

The world MUST NOT freeze or suspend off-screen agents or events.  
Off-screen life MUST continue deterministically.

### 8. High Resolution Comes from Proximity  

THE HUMAN USER sees more of a particular agent (e.g. Rebecca) because they are co-present often, not because the system privileges that agent.  
High resolution of description comes from:
- perceptual proximity  
- interaction frequency  
- narrative salience  

### 9. Cognition Load Distribution is Uniform  

Agents MUST use cognition in proportion to:
- their own stakes  
- their own drives  
- their own arcs  

Cognition MUST NOT be biased purely by THE HUMAN USER’s presence.

### 10. THE HUMAN USER Is a Person in the World, Not Its Centre  

The world MUST NOT treat THE HUMAN USER as a protagonist in the simulation logic.  

THE HUMAN USER:
- is physically present in the world  
- has actions and utterances that affect agents  
- is remembered by agents via episodic and biographical memory  

But:
- THE HUMAN USER has no internal numeric state  
- agents MUST NOT access or store THE HUMAN USER’s unseen internal feelings or thoughts  

======================================================================
## PART II — CLEAN ARCHITECTURE SPECIFICATION
======================================================================

### 1. Entities  

The system MUST define:

- **World** — deterministic environment (time, locations, objects, global events).  
- **Simulated Agents** — entities with internal numeric state and psychological variables.  
- **THE HUMAN USER (THE REAL PERSON)** — an external mind with physical presence only, no internal numeric state.

### 2. THE HUMAN USER: Absolute Prohibitions  

The system MUST NOT assign to THE HUMAN USER:

- mood  
- drives  
- personality  
- relationships (edges from THE HUMAN USER to others)  
- arcs  
- intentions  
- energy  

Agents MAY have relationship edges toward THE HUMAN USER.  
THE HUMAN USER MAY appear in memories and biographical facts.  
But outgoing relationship edges from THE HUMAN USER MUST NOT exist as numeric state.

### 3. Subsystems  

The architecture MUST include the following subsystems:

- World Engine  
- Autonomy Engine  
- Cognition Service (LLM)  
- Renderer Service (LLM)  
- Gateway  
- Persistence Layer  

Each subsystem MUST obey strict boundary rules defined in this document.

----------------------------------------------------------------------
### 4. World Engine
----------------------------------------------------------------------

The World Engine MUST:

- maintain global time and tick  
- handle locations and movement  
- apply environmental rules  
- update physical state  
- NEVER use LLMs  
- NEVER simulate THE HUMAN USER’s mind  

It MUST be fully deterministic.

----------------------------------------------------------------------
### 5. Simulated Agent Model
----------------------------------------------------------------------

Each simulated agent MUST have:

- mood  
- drives  
- personality  
- relationships  
- arcs  
- intentions  
- episodic memories  
- biographical memory  
- energy  

THE HUMAN USER MUST NOT have these numeric properties.

Agents MAY store:

- episodic memories of interactions with THE HUMAN USER  
- biographical facts about THE HUMAN USER that THE HUMAN USER has explicitly revealed  
- relationship edges toward THE HUMAN USER (e.g. warmth, trust, tension, attraction, familiarity, comfort, volatility)

Agents MUST NOT store or infer the unseen internal mental state of THE HUMAN USER.

----------------------------------------------------------------------
### 6. Autonomy Engine  
----------------------------------------------------------------------

The Autonomy Engine MUST:

- execute agent routines  
- update numeric psychology (drives, mood, arcs, relationships, energy)  
- choose low-level behaviour when cognition is not triggered  
- operate deterministically  

The Autonomy Engine MUST NOT:

- call any LLM directly  
- infer or simulate THE HUMAN USER’s internal psychology  

LLM MUST NOT be used for trivial choices.

----------------------------------------------------------------------
### 7. Cognition Service (LLM)
----------------------------------------------------------------------

Cognition MUST be triggered ONLY for meaningful events as defined in the Logic Layer.

The Cognition Service MUST receive as input:

- semantic summaries of drives, mood, relationships, arcs, intentions, energy  
- relevant episodic and biographical memories  
- personality summaries and domain summaries  
- dynamic activation packet  
- event context  

The Cognition Service input MUST NOT contain:

- raw numeric state  
- any representation of THE HUMAN USER’s internal mental state  

The Cognition Service output MUST be constrained to:

- utterance (what the agent says)  
- physical action (what the agent does)  
- stance/intent shifts (e.g., increase in commitment to an intention)  

Numeric changes to drives, mood, arcs, and relationships MUST be produced deterministically by the Logic Layer and Autonomy Engine based on the cognition output, NOT by the LLM directly.

----------------------------------------------------------------------
### 8. Renderer Service (LLM)
----------------------------------------------------------------------

The Renderer Service MUST:

- render ONLY perception (what can be sensed or reasonably inferred perceptually)  
- speak to THE HUMAN USER in second person (“you…”) when describing THE HUMAN USER’s POV  
- speak in first person (“I…”) for agent POV when required  
- avoid omniscient narration of internal states  
- avoid describing THE HUMAN USER’s internal state  

The Renderer MUST NOT:

- invent events that are not present in world state  
- rewrite or contradict world state  
- describe the unseen internal mental state of THE HUMAN USER  

The Renderer MAY:

- describe agents’ emotions only as observable or implied from behaviour, not as authoritative omniscient truth.

----------------------------------------------------------------------
### 9. Gateway
----------------------------------------------------------------------

The Gateway MUST:

- parse THE HUMAN USER’s actions and inputs  
- update world state accordingly  
- trigger cognition when required by logic rules  
- call the Renderer to produce output to THE HUMAN USER  

The Gateway MUST NOT:

- infer or store THE HUMAN USER’s internal psychology  
- bypass the Logic Layer and Autonomy Engine  

----------------------------------------------------------------------
### 10. Persistence Layer
----------------------------------------------------------------------

The Persistence Layer MUST store:

- world state  
- agent internal state  
- episodic memories  
- biographical memories  
- relationships  
- arcs  
- logs required for testing and debugging  

The Persistence Layer MUST NOT store:

- any numeric representation of THE HUMAN USER’s internal psychology  
- any guessed emotions or thoughts of THE HUMAN USER  

All persisted state MUST be sufficient to restore the world deterministically.

======================================================================
## PART III — LOGIC LAYER (FULL SPEC)
======================================================================

### Integration Note (Normative)

The Logic Layer uses personality values derived from the Personality Compiler (see PART IIA).  
All personality-related numeric values used in this section MUST originate from:
- the personality kernel, and  
- dynamic activation packets  

generated by the Personality Compiler.

No other subsystem is permitted to create or modify personality variables.

This is the deterministic psychological substrate.  
All rules below are normative.

----------------------------------------------------------------------
### SECTION 1 — STATE VARIABLES
----------------------------------------------------------------------

Simulated agents MUST store:

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

Each drive MUST have:
- level ∈ [0.0, 1.0]  
- sensitivity ∈ [0.5, 1.5]  

#### 1.3 Personality
Core personality traits are:

- sociability  
- emotional_volatility  
- dominance  
- conscientiousness  
- openness  

##### Clarification (Normative)

The above traits define the **core personality dimensions** shared by all agents.  
The Personality Kernel defined in PART IIA includes **additional extended dimensions**  
(e.g., directness, humour activation, intimacy assertiveness, trust baseline, etc.).

Both core traits and extended kernel traits MUST:
- be stored as part of the agent's personality state  
- be used by downstream systems (autonomy, cognition, renderer)  

This resolves any mismatch between the core list in §1.3 and the extended kernel definition in PART IIA.

#### 1.4 Relationship Edges
Each relationship edge MUST include:

- warmth  
- trust  
- tension  
- attraction  
- familiarity  
- comfort  
- volatility  

Relationship edge values MUST be numeric and MUST update deterministically.

#### 1.5 Arcs
Arcs MUST include:

- intensity  
- valence_bias  
- topic_vector  
- decay_rate  

#### 1.6 Intentions
Intentions MUST include:

- priority  
- horizon  
- type  
- OPTIONAL stability  

#### 1.7 Energy
Energy MUST be represented as:

- energy ∈ [0.0, 1.0]

#### 1.8 Episodic Memory
Each episodic memory MUST include:

- description  
- timestamp  
- salience  
- semantic tags  

Episodic memories MUST be created deterministically.

#### 1.9 Biographical Memory (Normative)

Agents MUST maintain a structured set of long-term personal facts, including about THE HUMAN USER (THE REAL PERSON).

Biographical memory MUST include:

- factual background explicitly revealed  
- long-term preferences  
- relational constants  
- identity themes  

Biographical memory MUST:

- persist across the entire simulation  
- accumulate naturally  
- influence interpretation of events  
- remain deterministic  
- NEVER contain unseen internal states of THE HUMAN USER  

----------------------------------------------------------------------
### SECTION 2 — GLOBAL DYNAMICS (THE LAWS)
----------------------------------------------------------------------

The laws below MUST govern all simulated agents continuously and deterministically.  
They MUST NOT be overridden.

------------------------------------------------------------
#### LAW 1 — DRIVES MOVE TOWARD OR AWAY FROM SATISFACTION
------------------------------------------------------------

Whenever an event affects a drive:

d_level ← clamp(d_level + effect(event, drive) * d_sensitivity)

- `effect(event, drive)` MUST be deterministic within [-1, +1].  
- Drives MUST drift toward baseline over time.

Examples (NON-NORMATIVE) illustrate the pattern only.

------------------------------------------------------------
#### LAW 2 — MOOD REFLECTS RECENT DRIVE HISTORY
------------------------------------------------------------

Valence MUST update as:
valence ← clamp(
valence + k_val * weighted_drive_change
)

Arousal MUST increase with:
- novelty  
- emotional shock  
- conflict  
- cognitive load  

Arousal MUST decay toward baseline.  
Personality.emotional_volatility MUST scale sensitivity.

------------------------------------------------------------
#### LAW 3 — ARCS DECAY UNLESS REINFORCED
------------------------------------------------------------

Arc intensity MUST decay with:

arc.intensity ← arc.intensity * (1 - arc.decay_rate * Δt)

Arc MUST increase in intensity if the new event semantically matches its topic_vector.

Arcs MUST bias tendencies but MUST NOT script behaviour.

------------------------------------------------------------
#### LAW 4 — RELATIONSHIPS DRIFT OVER TIME
------------------------------------------------------------

Without events:

- tension MUST decay  
- warmth MUST slowly move toward neutral  
- trust MUST slowly move toward neutral  
- familiarity MUST increase with co-presence and decay with absence  
- comfort MUST track long-term patterns  

With events:

- each relationship dimension MUST update deterministically  
- updates MUST scale by volatility  

Examples (NON-NORMATIVE) illustrate the pattern only.

------------------------------------------------------------
#### LAW 5 — ENERGY DEPLETES AND RESTORES
------------------------------------------------------------

Energy MUST decrease during:
- conflict  
- focused work  
- prolonged wakefulness  
- high cognitive load  

Energy MUST increase during:
- rest  
- sleep  
- low-stimulation periods  

Low energy MUST increase cognition thresholds.

------------------------------------------------------------
#### LAW 6 — DECISION PRESSURE IS A WEIGHTED COMBINATION
------------------------------------------------------------

All behavioural choices MUST derive from:

effective_tendency = f(
drives, mood, personality, arcs,
relationships, energy
)

This formula determines:
- approach vs withdrawal  
- speak vs silence  
- escalate vs de-escalate  
- engage vs ignore  
- remain vs leave  

No single variable MAY dominate unless at an extreme.

======================================================================
### SECTION 3 — DRIVE UPDATE LOGIC (FULL DETAIL)
======================================================================

### 3.1 Event Mapping  
Every event MUST map into drive effects in [-1, +1] for each drive.  
Mapping MUST be deterministic.

Examples (NON-NORMATIVE) illustrate the design pattern only.

### 3.2 Baseline Drift
Drives MUST drift toward baseline:

d_level ← d_level + (baseline - d_level) * drift_factor

Baseline MUST be stable, deterministic, and uniform across agents unless personality kernel modifies sensitivity.

======================================================================
### SECTION 4 — MOOD DYNAMICS (FULL DETAIL)
======================================================================

### 4.1 Valence  
Valence MUST be calculated, never assigned arbitrarily.

### 4.2 Arousal  
Arousal MUST increase with emotional intensity and novelty, and MUST decay toward a stable baseline.

======================================================================
### SECTION 5 — ARC DYNAMICS
======================================================================

Arcs MUST:

- be created from clusters of semantically related events  
- intensify when matched  
- decay when inactive  
- influence tendencies (not behaviour directly)  

Arc logic MUST be deterministic.

======================================================================
### SECTION 6 — RELATIONSHIP DYNAMICS
======================================================================

Relationship edges MUST update for every interaction.

### 6.1 Event-Based Updates  
Updates MUST consider:

- event classification  
- volatility  
- drive activation  
- existing warmth/trust/tension  

### 6.2 Drift  
Relationship edges MUST drift as described in GLOBAL LAWS.

======================================================================
### SECTION 7 — MEMORY SYSTEM  
(EPISODIC + BIOGRAPHICAL MEMORY SYSTEM)
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

Biographical memory MUST store:

- declared background facts  
- stable traits inferred from interaction  
- long-term preferences  
- stable relational patterns  
- recurring behavioural themes  

Biographical memory MUST NOT store:
- THE HUMAN USER’s internal emotions  
- THE HUMAN USER’s unexpressed thoughts  
- any psychological details not derived from explicit behaviour  

Biographical memory MUST influence:

- interpretation of events  
- trust thresholds  
- warmth/tension responses  
- arc activation  
- drive relevance  

Biographical memory MUST grow naturally and deterministically.

======================================================================
### SECTION 8 — SALIENCE & ATTENTION
======================================================================

Salience MUST be computed from:

- sensory prominence  
- relational stakes  
- drive pressure  
- arc intensity  
- novelty  
- THE HUMAN USER’s presence (ONE factor, not privileged)  

======================================================================
### SECTION 9 — COGNITION TRIGGER LOGIC
======================================================================

Meaningfulness MUST be computed as:

M = w1*max(salience)
	•	w2*max(drive pressure)
	•	w3*max(arc intensity)
	•	w4*relational stakes

	•	w5*(1 - energy)

   Cognition MUST trigger when:
- M ≥ threshold  
- AND event is non-trivial  
- AND cooldown is respected  

======================================================================
### SECTION 10 — LOW-LEVEL BEHAVIOUR (NON-LLM)
======================================================================

When cognition does not trigger, agents MUST behave via deterministic tendencies.

Examples (NON-NORMATIVE) illustrate this rule only.

======================================================================
### SECTION 11 — RENDERER TRIGGERS
======================================================================

Renderer MUST output perception when:

- perceiver location changes  
- agents enter or leave  
- someone acts toward the perceiver  
- salient sensory events occur  
- proxemics change  
- atmosphere shifts  

======================================================================
### SECTION 12 — NUMERIC → SEMANTIC MAPPING
======================================================================

LLMs MUST NEVER receive numeric internal state.

Renderer and Cognition MUST receive deterministic semantic summaries.

Examples illustrate mapping patterns ONLY.

======================================================================
### SECTION 13 — LLM OUTPUT → NUMERIC UPDATE
======================================================================

LLM output MUST be parsed into:

- utterance  
- action  
- stance shift  
- intention manipulation  

Numeric updates MUST be deterministic mappings performed outside the LLM.

======================================================================
### SECTION 14 — OPENNESS
======================================================================

The system MUST allow:

- neutral actions  
- simple variability in trivial contexts  
- pseudo-randomness ONLY if seeded and deterministic  

The system MUST NOT enumerate every life event.

======================================================================
### SECTION 15 — USER NON-SIMULATION (ABSOLUTE RULE)
======================================================================

THE HUMAN USER MUST NOT have:

- mood  
- drives  
- personality  
- arcs  
- intentions  
- energy  
- relationship edges from THE HUMAN USER to others  

Agents MAY store:

- relationship edges toward THE HUMAN USER  
- episodic memories involving THE HUMAN USER  
- biographical facts explicitly revealed by THE HUMAN USER  

Agents MUST NOT:

- infer unseen internal states of THE HUMAN USER  
- fabricate psychological data about THE HUMAN USER  
- convert renderer POV descriptions into numeric user state

======================================================================
## PART IIA — PERSONALITY COMPILER & CHARACTER INITIALIZATION
======================================================================

### 1. Purpose of This Subsystem

The Personality Compiler is a mandatory subsystem responsible for transforming human-readable personality materials (e.g., personality templates, agent fingerprints, relationship matrices) into:

- stable personality summaries (semantic, cached)
- numeric personality kernels (deterministic, substrate-level)
- domain-specific personality packs (emotion, conflict, humour, intimacy)
- dynamic activation packets (moment-to-moment behavioural tendencies)
- cached context fragments used by cognition and rendering
- initialization data for each simulated agent at world creation

It serves as the bridge between:

- human-defined personality material  
and  
- the deterministic numeric substrate + semantic summaries used at runtime.

The Personality Compiler MUST operate deterministically.  
It MUST NOT use any LLM.

### 2. Responsibilities

The Personality Compiler MUST:

1. Accept for each agent:
   - a weighted mixture of foundational personality templates  
   - an optional personality fingerprint (structured text or JSON)  
   - an optional relationship map  
   - optional adult-context intimacy notes (adults only; used exclusively by adult-capable renderer)

2. Produce:
   - a stable personality summary (approx. 150–250 tokens)  
   - a personality kernel (numeric vector)  
   - domain summaries (emotion, conflict, humour, communication, intimacy for adults only)  
   - a stable semantic cache for slow-changing traits  
   - an initial biographical memory pack  
   - an initial relationship profile (warmth, trust, tension, familiarity, comfort)

3. Persist:
   - numeric kernel  
   - stable summary  
   - domain summaries  
   - cached context fragments  
   - template mixture metadata  
   - fingerprint references  

4. Generate deterministic results:
   - kernel generation MUST be deterministic  
   - summaries MUST be deterministic given the same kernel and fingerprint  
   - cached fragments MUST only be regenerated when inputs change  

### 3. Non-Responsibilities

The Personality Compiler MUST NOT:

- perform non-deterministic or stochastic personality generation  
- create psychological variables outside MASTER_SPEC.md  
- overwrite numeric drives, mood, arcs, or relationships  
- call any LLM during compilation  
- leak fingerprint text directly to cognition or renderer  
- generate any sexual narrative content (LLM renderer handles that)

### 4. Personality Templates

The system MAY support N foundational personality templates, stored as structured data (JSON/YAML).

Each template MUST define:

- stable behavioural tendencies  
- communication patterns  
- conflict responses  
- humour style  
- intimacy preferences (adults only)  
- comfort ranges  
- emotional regulation tendencies  
- worldview tendencies  

Templates MUST:

- be structured (NOT raw prose)  
- be versioned  
- be deterministic inputs to the mixing function

### 5. Template Mixing

Each agent MUST reference a deterministic mixture of templates:

```json
{
  "Nurturer": 0.35,
  "Mediator": 0.20,
  "Thinker": 0.10,
  "Rebel": 0.35
}

Rules:
	•	weights MUST sum to 1.0
	•	mixing MUST use deterministic, documented functions
	•	the mixture MUST produce a stable personality kernel

6. Personality Kernel (Numeric)

The personality kernel MUST include numeric variables capturing:
	•	sociability tendency
	•	emotional volatility
	•	dominance
	•	conscientiousness
	•	openness
	•	directness vs indirectness
	•	introspection tendency
	•	humour activation
	•	conflict avoidance
	•	intimacy assertiveness (adults only)
	•	intimacy responsiveness (adults only)
	•	trust baseline
	•	forgiveness baseline

The exact list MUST remain stable across the system and be implemented verbatim in backend code.

The kernel MUST NOT contain any values representing THE HUMAN USER’s psychology.

7. Stable Personality Summary (Semantic)

The compiler MUST generate a stable semantic summary (approx. 150–250 tokens) describing:
	•	communication style
	•	emotional style
	•	typical stress responses
	•	fears and vulnerabilities
	•	connection style
	•	argument patterns
	•	softening triggers
	•	recovery patterns

Rules:
	•	MUST be cached and persisted
	•	MUST be regenerated only when kernel or fingerprint changes
	•	MUST be provided to cognition and renderer whenever an agent is involved
	•	MUST NOT expose fingerprint text literally

8. Domain Summaries

The compiler MUST generate domain summaries for at least:
	•	emotion regulation
	•	conflict style
	•	humour style
	•	communication style
	•	intimacy/sexuality style (adults only; renderer-only context)

Domain summaries MUST:
	•	be concise (approx. 50–120 tokens)
	•	be cached
	•	be provided to cognition and renderer when relevant
	•	NEVER be overwritten by LLMs

9. Dynamic Activation Packets

Dynamic activation packets provide moment-to-moment modulation of personality expression.

They MUST be derived from:
	•	drives
	•	mood
	•	arcs
	•	relevant episodic memories
	•	biographical memory
	•	relationship edges
	•	personality kernel

Rules:
	•	MUST NOT involve LLM calls
	•	MUST be compact (approx. 30–80 tokens when rendered semantically)
	•	MUST be passed to cognition alongside stable and domain summaries

10. Integration With Cognition Flow

For each cognition call, the Cognition LLM MUST receive, in semantic form:
	1.	stable personality summary
	2.	relevant domain summaries
	3.	dynamic activation packet
	4.	relationship summaries
	5.	memory snippets
	6.	event context

Cognition MUST follow docs/cognition_flow.md exactly.

11. Integration With Renderer

The Renderer LLM MUST receive:
	•	perception packet
	•	event context
	•	stable personality summary
	•	relevant domain summaries
	•	dynamic activation packet

Renderer MUST NOT see intimacy domain summaries unless:
	•	the renderer is adult-capable, AND
	•	the current scene is explicitly marked as sexual/intimate in world state

12. Initialization of Agents

At world creation, the Personality Compiler MUST:
	•	generate each agent’s personality kernel
	•	generate all stable and domain summaries
	•	cache all fragments
	•	create initial relationship edges toward relevant individuals
	•	create initial biographical memory pack
	•	generate initialization logs for debugging

These MUST be stored in persistence.

13. Persistence Rules

For each agent, persistence MUST store:
	•	personality kernel
	•	stable personality summary
	•	all domain summaries
	•	cached context fragments
	•	template mixture weights
	•	fingerprint references

All fields MUST survive world restarts and snapshots.

14. Test Requirements

The test suite MUST include:
	•	kernel determinism tests
	•	summary determinism tests
	•	caching behaviour tests
	•	fingerprint interpretation tests
	•	integration tests verifying that:
	•	cognition receives full personality packets
	•	renderer receives full personality packets
	•	fingerprint text NEVER reaches LLM prompts

These tests MUST map back to their corresponding clauses in this specification.

======================================================================
## PART IIB — (If included in original) EXTENSIONS, FUTURE-PROOFING, OR DOMAIN ADDENDA
======================================================================

*(Note: Your uploaded MASTER_SPEC.md ended at PART IIA and did not contain a Part IIB or appendices.  
If later you add additional domain modules — e.g., long-term societal simulation, spatial modelling, or extended relational engines — they must follow the same determinism and separation principles defined above.)*

======================================================================
## APPENDIX A — RENDERER POV RULES (NORMATIVE)
======================================================================

### A.1 Allowed Usage of “you”  
The Renderer LLM MUST speak in second person **only when describing the perceptual experience of THE HUMAN USER**.

Examples of allowed usage:
- “You see Rebecca walking through the doorway.”  
- “You feel the sofa dip slightly as she sits beside you.”

Restrictions:
- MUST NOT describe internal mental states of THE HUMAN USER  
- MUST NOT imply psychological modelling of THE HUMAN USER  
- MUST NOT leak numeric state  
- MUST NOT fabricate non-existent perceptions  

### A.2 Prohibited Usage of “you”
“you” MUST NOT be used to:
- describe THE HUMAN USER’s internal emotions  
- generate omniscient narration  
- reinterpret world state  
- assign numeric state  

### A.3 When “you” refers to THE BUILDER LLM  
NEVER.  
“you” MUST NOT refer to THE BUILDER LLM anywhere in system rules.

If THE BUILDER LLM interprets a “you” outside the Renderer POV context, it MUST treat it as an error.

======================================================================
## APPENDIX B — MEMORY ISOLATION RULES (NORMATIVE)
======================================================================

### B.1 Numeric vs Semantic Separation  
- Numeric state MUST stay internal.  
- Semantic state MUST be delivered only through summaries.  

### B.2 Memory Boundaries  
- Episodic memory = event-based  
- Biographical memory = long-term patterns  
- Neither may contain THE HUMAN USER’s unseen mental state  

### B.3 Retrieval Boundaries  
- Memory retrieval MUST use:
  - semantic similarity  
  - recency  
  - salience  

- Qdrant MAY be used for vector retrieval (Phase 9+).  
- Postgres MUST remain the canonical store.  

======================================================================
## APPENDIX C — DETERMINISM RULES (NORMATIVE)
======================================================================

### C.1 Deterministic World  
The world MUST run deterministically:
- same inputs ⇒ same outputs  
- no random calls  
- no nondeterministic concurrency  

### C.2 Pseudo-Randomness  
Allowed only if:
- seeded  
- reproducible  
- documented  
- used for trivial or low-impact variations only  

Pseudo-randomness MUST NEVER:
- determine personality  
- determine deep emotional shifts  
- determine relationship evolution  
- determine decisions with psychological impact  

### C.3 LLM Determinism  
LLM outputs MUST be normalized via:
- canonical sampling parameters  
- schema enforcement  
- numeric update mapping rules  

LLMs MUST NOT produce uncontrolled variability.

======================================================================
## APPENDIX D — THE HUMAN USER (THE REAL PERSON)
======================================================================

### D.1 The Human User’s Role  

THE HUMAN USER:
- is physically present within the world  
- interacts through actions, speech, or movement  
- is observed by simulated agents  
- affects the world state  

THE HUMAN USER IS NOT:
- simulated psychologically  
- given numeric state  
- part of the autonomy system  

### D.2 How Agents Remember THE HUMAN USER  

Agents MAY remember:
- events involving THE HUMAN USER  
- biographical facts explicitly revealed  
- consistent behavioural patterns observed externally  

Agents MUST NOT remember:
- THE HUMAN USER’s inner thoughts  
- interpretations of unexpressed emotions  
- imagined motivations  

### D.3 Relationship Edges Toward THE HUMAN USER  
Agents MAY have:
- warmth toward THE HUMAN USER  
- trust toward THE HUMAN USER  
- tension with THE HUMAN USER  
- attraction toward THE HUMAN USER  
- familiarity with THE HUMAN USER  
- comfort with THE HUMAN USER  

But THE HUMAN USER MUST NOT have numeric edges toward others.

======================================================================
## APPENDIX E — LLM CONTENT SEPARATION (NORMATIVE)
======================================================================

### E.1 Cognition Model  
The cognition LLM MUST:
- use stable + domain + activation packets  
- produce structured outputs  
- obey schema  
- avoid omniscience  
- output only:
  - utterance  
  - action  
  - stance shift  
  - intention change  

### E.2 Renderer Model  
The renderer LLM MUST:
- be perception-only  
- describe sensory experience  
- use POV conventions correctly  
- speak in second-person to THE HUMAN USER  

### E.3 Adult Renderer Model  
If an adult-capable renderer is used:
- MUST be invoked ONLY for explicitly sexual/intimate scenes  
- MUST follow all perception rules  
- MAY use adult domain summary  
- MUST NOT alter world-state or psychology directly  

======================================================================
## APPENDIX F — FAILURE MODES AND GUARANTEES
======================================================================

### F.1 If Cognition Fails  
If the cognition service fails or times out:
- the system MUST fall back to deterministic, non-LLM behaviour  
- the agent MUST behave according to tendencies  
- NO numeric updates from cognition may occur  

### F.2 If Renderer Fails  
If the renderer fails:
- the system MUST return a safe fallback string  
- world-state MUST NOT be corrupted  

### F.3 If Persistence Fails  
If Postgres fails:
- system MUST halt safely  
- NO secondary data source may override it  
- Redis MUST NOT replace authoritative state  
- Qdrant MUST NOT replace authoritative memory  

### F.4 If Builder Attempts Forbidden Operations  
THE BUILDER LLM MUST refuse and cite:
- MASTER_SPEC.md  
- BUILDER_CONTRACT.md  
- Architecture.md  
- Plan.md  

======================================================================
## APPENDIX G — TEST REQUIREMENTS SUMMARY
======================================================================

### G.1 World Engine Tests  
- deterministic ticks  
- correct location updates  
- consistent event queue behaviour  

### G.2 Autonomy Tests  
- drive change determinism  
- mood calculations  
- arc creation/decay  
- relationship drift  
- memory creation thresholds  

### G.3 Personality Compiler Tests  
- kernel determinism  
- summary determinism  
- caching  
- fingerprint interpretation  
- correct packet construction  

### G.4 Cognition Tests  
- meaning score calculation  
- correct triggering logic  
- schema compliance  
- deterministic numeric output mapping  

### G.5 Renderer Tests  
- correct POV rules  
- no internal state leakage  
- perception correctness  
- adult-model routing correctness  

### G.6 Gateway Tests  
- action parsing  
- integration with full pipeline  
- world mutation correctness  

### G.7 Persistence Tests  
- schema integrity  
- no leakage of forbidden fields  
- restart consistency  

======================================================================
## APPENDIX H — COMPLIANCE STATEMENT (META)
======================================================================

The entire system MUST comply with:

1. **User Non-Simulation Rule**  
   THE HUMAN USER MUST NOT have numeric psychology, EVER.

2. **Determinism Rule**  
   Every subsystem MUST operate deterministically unless explicitly allowed otherwise.

3. **Separation of Concerns**  
   - Numeric substrate  
   - Semantic summaries  
   - LLM cognition  
   - LLM rendering  

   MUST remain independent and properly layered.

4. **Source of Truth Rule**  
   MASTER_SPEC.md overrides all other documents.

5. **LLM Contract Rule**  
   THE BUILDER LLM MUST obey BUILDER_CONTRACT.md.

6. **Architecture Rule**  
   Redis and Qdrant MUST NOT be used before Phase 9  
   and MUST NOT store authoritative world or psychology state.

======================================================================
## APPENDIX I — UNEXPECTED EVENTS (INCURSIONS)
======================================================================

### I.1 Definition

An **unexpected event** (also called an **incursion**) is any event that:

- interrupts the current flow of activity for one or more agents, including THE HUMAN USER (THE REAL PERSON),  
- is not initiated by the perceiver or the main local interaction,  
- arises from the broader world state (other agents, environment, external systems), and  
- can occur under any conditions, at any time, regardless of what is currently happening on-screen.

Unexpected events are not a separate psychological system.  
They are **world-level occurrences** that enter the current perceptual frame.

Examples (NON-NORMATIVE):

- THE HUMAN USER and Rebecca are talking in the lounge and the front door unlocks as Lucy returns home.  
- A delivery driver knocks on the door in the middle of a tense conversation.  
- Rebecca sends a message asking if THE HUMAN USER wants Thai on her way back.  

These examples illustrate the **character** of unexpected events.  
They are NOT exhaustive and MUST NOT be treated as enumerated categories.


### I.2 Core Properties (Normative)

Unexpected events MUST:

1. Be generated by world state and world logic, not by LLM improvisation alone.  
2. Be allowed to occur at any time, regardless of the current scene content.  
3. Be capable of intersecting with:
   - calm, everyday scenes (e.g., breakfast, sofa chat),  
   - emotionally charged scenes (arguments, confessions),  
   - intimate/sexual scenes (adult renderer context),  
   - routine or “boring” moments.

Unexpected events MUST NOT:

1. Pause or reset the world clock.  
2. Freeze other agents’ routines or arcs.  
3. Be restricted to “narratively appropriate” moments only.  
4. Depend solely on THE HUMAN USER’s actions to exist.


### I.3 Source of Unexpected Events

Unexpected events MUST originate from:

- other agents’ schedules, calendars, and obligations,  
- environment processes (deliveries, traffic, neighbours, noise),  
- communication channels (messages, calls, notifications),  
- world-level stochastic-but-deterministic mechanisms (see C.2 Pseudo-Randomness) where appropriate.

They MUST be:

- derived from the same deterministic world model as any other event,  
- explainable from the combination of:
  - world time,  
  - agents’ locations and routines,  
  - prior commitments and background facts.

Unexpected events MUST NEVER:

- be pure “LLM whim” without any grounding in world data,  
- contradict established world facts or agent locations,  
- retroactively rewrite what just happened in world state.


### I.4 Relationship to the Logic Layer

Unexpected events MUST pass through the same Logic Layer as any other event:

1. **World Engine**  
   - Responsible for scheduling, generating, and inserting unexpected events into the event stream.  
   - MUST treat them as ordinary events with unexpected timing from the perceiver’s perspective, not as a special ontological category.

2. **Autonomy Engine**  
   - MUST process the consequences of unexpected events on:
     - drives,  
     - mood,  
     - arcs,  
     - relationships,  
     - energy.  
   - MUST NOT treat “unexpected” as a separate type of psychology; it is a property of timing and context, not of state variables.

3. **Cognition Service**  
   - MAY be triggered when an unexpected event causes:
     - high salience,  
     - high relational stakes,  
     - strong drive pressure,  
     - arc-relevant disturbance.  
   - MUST follow normal cognition trigger logic (see SECTION 9 — COGNITION TRIGGER LOGIC).

4. **Renderer Service**  
   - MUST present unexpected events as interruptions to the current perceptual flow:
     - knocks, door opening, messages, someone entering, etc.  
   - MUST integrate them into the perceptual narrative (“you hear a key turn in the lock…”, “your phone buzzes on the table”).

Unexpected events MUST NOT bypass the Logic Layer.  
They are world events with “unexpectedness” defined from the perceiver’s point of view, not a special mechanism.


### I.5 Unexpected Events and Intimate/Adult Scenes

Unexpected events MAY occur during intimate or sexual scenes, subject to renderer constraints:

- They MUST be derived from the same world logic (e.g., another person returning home, a scheduled taxi arriving, a phone call).  
- They MUST NOT be used to inject gratuitous content or break the determinism of the scene.  
- They MUST be processed by:
  - Autonomy Engine,  
  - Cognition Service,  
  - Renderer,  
  as usual.

In particular:

- If an unexpected event would realistically end or disrupt a sexual situation (e.g., child entering the room, unexpected arrival), the world MUST allow this disruption to happen.  
- The system MUST NOT silently suppress plausible unexpected events purely to preserve “scene coherence.”


### I.6 No Enumeration, No Hardcoding

The system MUST NOT:

- maintain a fixed finite set of “types” of unexpected events as enumerated flags,  
- hardcode narrative templates like “doorbell event,” “phone event” as the only options.

Instead:

- Unexpected events MUST be generated from general world mechanics (schedules, locations, movement, communications).  
- The Renderer MUST describe them based on actual world state, not category names.


### I.7 Impact on THE HUMAN USER

Unexpected events MAY:

- create interruptions,  
- alter the emotional atmosphere,  
- alter agents’ priorities and behaviour.

However:

- THE HUMAN USER’s internal state is still NOT modelled numerically.  
- The system MUST NOT attach numeric “surprise,” “annoyance,” or “arousal” variables to THE HUMAN USER.  
- Only agents have such internal numeric responses to unexpected events.

======================================================================
## APPENDIX J — CALENDARS, OBLIGATIONS, AND PLANS
======================================================================

### J.1 Purpose

The **Calendar/Obligation System** represents:

- long-term commitments,  
- scheduled events,  
- plans and obligations  

for simulated agents and, where needed, factual commitments involving THE HUMAN USER (e.g., “dinner booked at 19:30 with Rebecca”).

This system is part of the **World Engine** and **World State**, not part of numeric psychology.

### J.2 Nature of Calendars

Each relevant agent MAY have:

- a personal calendar of events (appointments, rehearsals, work shifts, social plans),  
- obligations (deadlines, promised meetings, chores),  
- longer-term plans (project work, trips, recurring commitments).

The world MUST support:

- at least hundreds to thousands of events across the cast,  
- recurring events,  
- all-day and timed events.

Calendars MUST be stored in persistence as structured world data, not as a psychological layer.


### J.3 Distinction From Psychology

Calendars and obligations:

- MUST be treated as **external facts** about the agent’s life (e.g., “Rebecca has rehearsal at 19:00”),  
- MUST NOT be stored as drives, mood, arcs, or intentions themselves,  
- MUST NOT exist as numeric psychological variables.

Instead:

- When calendar time approaches or passes, the Autonomy Engine and Cognition Service MAY:
  - adjust intentions,  
  - adjust drive pressure (e.g., competence, safety, relatedness),  
  - trigger cognition.

The calendar is the **input domain**, not the psychological mechanism.


### J.4 Integration With World Engine

The World Engine MUST:

1. Maintain a calendar table or structure for each relevant agent.  
2. For each tick, determine which calendar items:
   - are upcoming,  
   - are starting,  
   - are in progress,  
   - are overdue.

3. Generate world events when:
   - a scheduled event should start (e.g., Rebecca leaving home for rehearsal),  
   - a reminder or preparatory phase occurs (e.g., 30 minutes before an appointment),  
   - an obligation is missed or completed.

These world events MUST then flow into the Logic Layer like any other event.

### J.5 Integration With Autonomy Engine

The Autonomy Engine MUST:

- evaluate calendar-derived events as part of decision pressure,  
- update or create intentions accordingly:
  - “prepare to leave,”  
  - “cancel plan,”  
  - “send a message to THE HUMAN USER,”  
  - “delay departure,” etc.

Drive pressure updates (e.g., competence, safety, relatedness) MUST be deterministic functions of:

- the nature of the obligation,  
- its importance,  
- how late or early it is relative to world time.

Example (NON-NORMATIVE):

- If an important rehearsal is imminent and Rebecca has not prepared, competence pressure might increase, which in turn may raise anxiety-related tendencies and influence cognition triggering.

The Autonomy Engine MUST NOT treat calendars as magical sources of behaviour; they are inputs into decision pressure.

### J.6 Integration With Cognition Service

Cognition MAY be triggered by calendar tension when:

- obligations conflict (double-booking),  
- a key obligation is missed,  
- a plan collides with an emotionally salient event (e.g., argument vs. commitment),  
- there are meaningful relational stakes (e.g., cancelling on THE HUMAN USER).

Cognition context MUST include:

- the relevant calendar item(s),  
- the time pressure,  
- the relationship context,  
- the personality packet and activation packet.

The LLM MUST decide **what the agent thinks and says**, while numeric consequences are determined by deterministic mapping rules.

### J.7 Integration With Renderer

The Renderer MUST surface calendars and obligations **through perception**, not omniscient exposition.

Allowed forms include:

- objects: “You see the rehearsal time circled on the calendar on the fridge.”  
- behaviour: “Rebecca glances at the clock; she’s due to leave in fifteen minutes.”  
- dialogue: “She says, ‘I really need to get going soon; I promised I’d be there by seven.’”

The Renderer MUST NOT:

- directly dump calendar tables,  
- state internal psychological consequences as facts (“she is anxious about it”) unless these are actual LLM cognition outputs expressed through behaviour or words.

### J.8 THE HUMAN USER and Calendars

THE HUMAN USER may have:

- calendar entries stored as factual world state,  
- commitments with other agents (dinners, trips, events).

However:

- THE HUMAN USER’s calendar MUST NOT be used to infer numeric drives or mood for THE HUMAN USER.  
- Only agents’ internal states are modelled numerically.

Agents MAY:

- store biographical facts about THE HUMAN USER’s recurring commitments,  
- update their own reactions to those commitments,  
- vary their behaviour toward THE HUMAN USER accordingly.


### J.9 Relationship to Unexpected Events

Calendars and unexpected events are complementary:

- Calendars → structured, expected events that may still be forgotten, ignored, or deprioritised.  
- Unexpected events → unplanned intrusions that arise from world dynamics.

The system MUST allow:

- a calendar event to become an unexpected event **from the POV of the perceiver** if the perceiver forgot about it or is focused elsewhere.  
  Example (NON-NORMATIVE):
  - THE HUMAN USER and Rebecca are absorbed in something, and a taxi arrives for a previously booked plan.  
  - From their POV this is an interruption, even though it was scheduled.

This duality MUST be handled via:

- World Engine (for origin),  
- Autonomy Engine (for response),  
- Renderer (for presentation),  
- NOT via new special-case psychology.

======================================================================
## UPDATED END OF MASTER_SPEC.md
======================================================================

The Virtual World Backend MUST:

- treat THE HUMAN USER (THE REAL PERSON) as a physically present participant without internal numeric state,  
- run all simulated agents on a deterministic psychological substrate,  
- separate numeric state, semantic summaries, cognition, and rendering,  
- obey all constraints on Redis, Qdrant, and external services as defined in Architecture.md and Plan.md,  
- honour all normative clauses in MASTER_SPEC.md, including appendices A–J,  
- and refuse any builder behaviour that violates these rules.

======================================================================
## APPENDIX K — ABSOLUTE BAN ON REWINDING, REPLAY, SAVE STATES, 
## OR ANY FORM OF TEMPORAL MANIPULATION (NORMATIVE)
======================================================================

### K.1 Core Principle
The Virtual World MUST operate on a **strictly forward-moving, irreversible timeline**.  
Time has a single direction, a single continuity, and a single reality.

There MUST NOT be:
- rewind,
- replay,
- branching timelines,
- “try again” mechanics,
- loading a prior world state,
- checkpoints,
- save files,
- scene resets,
- memory rewrites to change outcomes,
- any video-game-like temporal controls.

Once something happens, **it has happened**.

### K.2 World State Permanence (Normative)
The world state stored in Postgres represents the **one and only reality**.

The system MUST NOT:
- roll back the world clock,
- restore an old version of world state,
- maintain snapshots for user replay,
- reverse any agent behaviour, drives, moods, arcs, relationships, or memories.

Postgres MUST remain strictly append-only in terms of history.
Corrections MAY occur only for bug fixes, never as a user-facing mechanism.

### K.3 Agent Psychology Permanence (Normative)
All psychological processes MUST be irreversible:

- drives update permanently,
- mood updates permanently,
- arcs evolve permanently,
- relationships drift permanently,
- intentions update permanently,
- energy updates permanently,
- memories (episodic + biographical) are permanent once created.

The system MUST NOT:
- delete memories to achieve a different outcome,
- “undo” emotional or relational changes,
- restore a prior psychological state,
- allow cognition to be re-run to produce a different outcome for the same event.

### K.4 Human User Permanence (Normative)
THE HUMAN USER (THE REAL PERSON) interacts with the world in real time.
Their actions MUST be treated as permanent world events.

The system MUST NOT:
- allow the user to rewind their actions,
- “try again” with a different phrasing,
- reconstruct the same moment with alternate outcomes.

Every action by THE HUMAN USER is a permanent addition to world history.

### K.5 Renderer Permanence (Normative)
The Renderer MUST NOT:
- re-render past scenes,
- reconstruct historical scenes as if they are happening now,
- provide cinematic replay,
- generate alternate versions of prior events,
- support repeated “takes” of the same moment.

The Renderer describes **only the current perceptual moment**.

Memory recall MAY summarize past events, but MUST NOT simulate them as if they are occurring again.

### K.6 Cognition Permanence (Normative)
Cognition MUST:
- run only once per meaningful event,
- produce a single deterministic outcome per context,
- update psychology deterministically based on that outcome.

Cognition MUST NOT:
- re-run the same event to produce alternate outcomes,
- allow the user to request “a different answer” to the same moment,
- provide multi-path branching dialogues,
- behave like a narrative engine, game system, or visual novel.

### K.7 No Branching, No Alternate Timelines
The world MUST NOT:
- fork into alternate branches,
- support parallel realities,
- maintain multiple versions of the same moment.

There is one world, one timeline, one continuity.

### K.8 Unexpected Events and Calendars Respect Irreversibility
Unexpected events (see Appendix I) and calendars/obligations (see Appendix J):

- MUST rely on world time,
- MUST be irreversible,
- MUST interact with the world’s forward-only timeline.

Unexpected events MUST NOT be “reloaded” or “rerun.”
Calendar events MUST NOT be reset or undone after they pass.

### K.9 Redis and Qdrant Cannot Be Used For Rewind
Redis MAY cache ephemeral state.
Qdrant MAY store embeddings.

They MUST NOT:
- store snapshots,
- store past world states,
- store reversible psychology,
- store user actions for replay,
- rehydrate old states to relive moments.

Their function is purely:
- caching,
- vector search,
- performance optimization,
as defined in Plan.md and Architecture.md.

### K.10 Enforcement
If the user requests **any** rewind, replay, undo, alternative outcome, scene regeneration, or “try again” functionality, the Builder LLM MUST:

1. Refuse the request, and  
2. Cite Appendix K (and MASTER_SPEC.md global rules), and  
3. Explain that the system operates under real-world continuity.  

### K.11 Summary
The Virtual World is not a game, not a simulation toy, not a branching narrative engine.

It is a continuous, deterministic, psychologically coherent world.

**Once something happens, it has happened forever.**

======================================================================
## END OF APPENDIX K
======================================================================


======================================================================
## END OF MASTER_SPEC.md
======================================================================