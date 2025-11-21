# SIMULATION IMPLEMENTATION BLUEPRINT  
_For the coding LLM with full access to the repo, schema, and seed files._

You are an LLM with full read–write access to the backend codebase, database schema (from `SCHEMA.md`), and the following data inputs:

- `Personalities.txt` – 15 personality archetypes  
- `Sim Baseline.docx` – baseline world and relationship state  
- `George_Profile.txt` – system rules for handling the real George  
- `Rebecca Master Profile.csv` – structured facts about Rebecca  
- `Rebecca Ferguson - Connections.csv` – Rebecca’s connection graph  
- `Rebecca_Fingerprint.json` – distilled trait/number fingerprint for Rebecca  

Your task is to **modify the existing PFEE codebase and seed the database** so that:

1. Agents (especially Rebecca and a small core cast) behave as autonomous, realistic people shaped by their personalities, relationships, memories, and arcs.  
2. The world starts from the baseline described in the documents.  
3. George is present as the *real user* and is never simulated internally.  
4. PFEE uses the seeded data in every perception cycle.  
5. The system evolves over time, not only when the user types.

All instructions below are **mandatory**. Do not improvise beyond them.


---

## SECTION 1 – HIGH-LEVEL GOALS

1.1. Implement a **data mapping pipeline** that converts the provided files into:
- `agents` rows  
- `relationships` rows  
- `memories`  
- `arcs`  
- `intentions`  
- `calendars`  
- `pfee_influence_fields`  
- `locations`  
- `objects`

1.2. Enforce the **“George is not simulated”** rule across PFEE:
- George has no simulated inner life, no simulated memories, no arcs, no intentions.  
- Others can have memories and feelings about George.  
- PFEE never generates internal state *for* George.

1.3. Extend PFEE so characters show **autonomy over time**:
- Drives, mood, and influence fields evolve between events.  
- Relationships and arcs change gradually.  
- Agents sometimes initiate interactions based on internal pressure and context.

1.4. Make sure PFEE **consumes the seeded data**:
- world_state_builder reads the right tables.  
- semantic mapping uses personality, relationships, arcs, memories, and influence fields.  
- cognition input contains semantic summaries derived from those.  

1.5. Provide **tests** that verify all of the above.


---

## SECTION 2 – DATA MAPPING: RAW FILES → INTERNAL REPRESENTATION

You must implement a **deterministic mapping layer**. This is *not* runtime code for PFEE; this is seeding/initialisation logic.

### 2.1 Rebecca’s Personality (Fingerprint + Master Profile)

Inputs:
- `Rebecca_Fingerprint.json` – trait names and numeric values.  
- `Personalities.txt` – 15 archetypes.  
- `Rebecca Master Profile.csv` – structured facts (type, subtype, text, context).

Target fields in `agents` for Rebecca:

- `agents.personality_kernel`:  
  - Compact JSON with:
    - Big Five–like traits or your derived trait dimensions  
    - Core motivations  
    - Core fears  
    - Core tensions  
  - Use `Rebecca_Fingerprint.json` as the primary numerical source.  
  - Use `Personalities.txt` only to label or describe the resulting kernel in words (e.g. “70% Visionary, 30% Healer”).

- `agents.personality_summaries`:  
  - JSON with short natural-language summaries grouped by theme, derived only from the master profile and fingerprint:
    - `self_view`  
    - `love_style`  
    - `career_style`  
    - `conflict_style`  
    - `public_image`  
    - `private_self`  

- `agents.drives`:  
  - Numeric drive levels and sensitivities, inferred from fingerprint:
    - Examples: attachment, autonomy, achievement, creativity, recognition, privacy, security, novelty.  
  - Use a consistent 0–1 or 0–100 scale.  
  - Store as JSON.

- `agents.mood`:  
  - Baseline valence/arousal (e.g. `valence`, `arousal`), plus disposition (optimism, anxiety tendency).  
  - Derived from fingerprint and baseline doc.

- `agents.domain_summaries`:  
  - JSON summary fields by domain:
    - `career`  
    - `family`  
    - `romance`  
    - `friends`  
    - `fame_and_public_life`  
    - `creativity`  
    - `health_and_body`  

- `agents.status_flags`:  
  - Booleans or tags:
    - `is_celebrity = true`  
    - `is_partner_of_george = true`  
    - `relationship_status = "exclusive"`  
    - `lives_with_george = true`  
    - `relationship_is_public = false` (start hidden, as per baseline)

Implementation requirement:

- Implement a **one-time mapping function** (used in the seed script) that:
  - Loads Rebecca_Fingerprint.json.
  - Loads Rebecca Master Profile.csv.
  - Computes these JSONs deterministically.
  - Writes them to the `agents` table for Rebecca’s row.


### 2.2 Rebecca’s Memories and Arcs

Use `Rebecca Master Profile.csv` plus `Sim Baseline.docx`.

Rules:

- For each key life event (origin stories, turning points, serious episodes), create a `memories` row:
  - `agent_id` = Rebecca’s agent id.  
  - `type` = `"biographical"` or `"episodic"`.  
  - `content` = short, precise description.  
  - `tags` = JSON list of themes (e.g. `["career", "love", "public_image"]`).  
  - `salience` = numeric (higher for pivotal events like first meeting, moving in).  
  - `time_reference` = approximate date or relative period if available.

- Group related facts into **arcs**:
  - e.g. `arc_name = "Becoming famous"`, `arc_name = "Secret relationship with George"`, etc.  
  - `arcs` table should store:
    - `agent_id`  
    - `name`  
    - `description`  
    - `status` (active, completed, dormant)  
    - `importance` (numeric)  
    - JSON field with:
      - `core_tension`  
      - `desired_outcomes`  
      - `fears`  
      - `progress` (initially 0–0.3 depending on story stage)  

- Link key memories to arcs via either:
  - a join table (if present) or  
  - storing `arc_ids` inside memories’ JSON field.

Implementation:

- Create a mapping script that:
  - Scans all rows in the master profile.  
  - Categorises them into either `memories`, `arcs`, `domain_summaries`, or `personality_traits`.  
  - Writes them into the correct tables.


### 2.3 Rebecca’s Relationships (Connections CSV)

Input: `Rebecca Ferguson - Connections.csv`.

Target: `relationships` table.

Rules:

- Each row in the connections file describing a person X and some form of connection to Rebecca becomes:
  - a `relationships` row with:
    - `source_agent_id` = Rebecca  
    - `target_agent_id` = agent for X (create agent rows if missing; minimal personality is fine for now).  
    - Numeric fields (warmth, trust, attraction, familiarity, tension, volatility, comfort) mapped from the connection strength/category.

- Define a **mapping table** from connection categories/weights to numeric values:
  - Example:
    - “family / very close” → warmth 0.9, trust 0.9, familiarity 1.0, tension 0.3, volatility 0.2  
    - “professional / cordial” → warmth 0.4, trust 0.6, familiarity 0.5, tension 0.2, volatility 0.2  
    - “strained” → warmth 0.2, trust 0.3, tension 0.8, volatility 0.7  
  - Implement this mapping centrally so the same category always yields the same numeric vector.

- For **George specifically**:
  - Override with the baseline:  
    - warmth, trust, attraction, familiarity very high, tension low, volatility low.  
  - Mark the relationship as romantic/exclusive in a JSON field.

Implementation:

- Implement a deterministic function used by the seed script:
  - Reads the connections CSV.  
  - Ensures agents exist for each named person.  
  - Computes relationship vectors using the mapping table.  
  - Inserts/updates the `relationships` rows.


### 2.4 Other Agents (Lucy, Nadine, etc.)

Use Sim Baseline + George_Profile and any known notes.

Rules:

- For **Lucy** and **Nadine**:
  - Create full `agents` rows.
  - Assign personality archetypes based on the user’s high-level descriptions (if present); otherwise choose from archetypes logically.
  - Populate:
    - `personality_kernel`  
    - `personality_summaries`  
    - `drives`  
    - `mood` (baseline)  
    - `domain_summaries`  
    - `status_flags` (e.g. `is_family`, `is_ex_partner_of_george`).

- Seed `relationships` rows:
  - Lucy ↔ George  
  - Lucy ↔ Rebecca (if appropriate)  
  - Nadine ↔ George  
  - Nadine ↔ Lucy  
  - With numeric vectors consistent with the baseline narrative (co-parenting, past relationship, etc.).

- Seed a small number of **memories** and **arcs**:
  - Lucy: childhood, school, relationship with both parents.  
  - Nadine: history with George, co-parenting, current life tension level.

For less important or unknown people (friends, celebrities, etc.), you may generate:

- Simple `agents` rows with:
  - 1 archetype  
  - 1–2 domain summaries  
  - Minimal drives/mood  
  - Relationships only if they matter to Rebecca or George.

Implementation:

- Provide a function in the seed script that takes a “character template” (name, type, brief description) and produces a minimal but consistent `agents` row plus relationships.


---

## SECTION 3 – GEORGE: RULES AND IMPLEMENTATION

George is the real user. The system must **never** simulate his inner life.

### 3.1 Marking George in Data

- In the `users` table, identify the row that corresponds to the real George.
- In the `agents` table, create a corresponding row representing George’s physical presence in the world.
- Add a **flag** to the `agents` row:
  - Either `is_real_user = true` in a JSON field, or a dedicated boolean column if you choose to add one.

### 3.2 Prohibited for George

All PFEE and Autonomy-related code must enforce:

- No `memories` rows with `agent_id = george_agent_id`.  
- No `arcs` with `agent_id = george_agent_id`.  
- No `intentions` with `agent_id = george_agent_id` created or updated by PFEE.  
- No `pfee_influence_fields` row for George.  
- No `personality_kernel` generated for George.  
- No `personality_summaries` generated for George.  
- No modifications to George’s internal numeric drives or mood.

### 3.3 Allowed for George

- `agents` row with:
  - Publicly known info (degrees, job, age) that *others* can know.  
  - Location information (where his body is).  
- `relationships` where others have feelings about George.  
- Memories for other people referencing George.

Implementation:

- In PFEE modules that read/update psychology:
  - Add explicit checks: if `agent.is_real_user` is true, **skip** internal updates, skip memory creation, skip arc updates, skip influence field modifications.

- In world_state_builder:
  - Still include George as a physical agent in the scene.  
  - Mention his public facts where relevant, but do not treat them as internal psychology.


---

## SECTION 4 – WORLD SEEDING: LOCATIONS, OBJECTS, BASELINE

### 4.1 Locations from Sim Baseline

Create `locations` rows for the Cookridge house and immediate surroundings, for example:

- `cookridge_house_lounge`  
- `cookridge_house_kitchen`  
- `cookridge_house_hallway`  
- `cookridge_house_entryway`  
- `cookridge_house_bedroom`  
- `cookridge_house_bathroom`  
- `cookridge_house_rebeccas_office`  
- `cookridge_house_studio`  
- `cookridge_house_lucys_room`  
- `cookridge_house_garden_front`  
- `cookridge_house_garden_back`  
- `driveway`  
- `double_garage`

Each location must have:
- A human-readable `name`.  
- A `type` (e.g. `"room"`, `"garden"`, `"driveway"`).  
- An `adjacency` JSON listing connected location IDs (doorways, paths).

Use the layout in the baseline document to set adjacency logically.

### 4.2 Objects

Seed `objects` with important items:

- Sofa, dining table, bed, desk, guitars, amps, computer, etc.  
- Each object:
  - `location_id` = where it is.  
  - Type and name.  
  - Optional attributes if the schema allows.

### 4.3 Initial Positions

At world start:

- George: in a sensible room (e.g. lounge or bedroom).  
- Rebecca: in another plausible room (e.g. lounge, office, or kitchen), depending on the baseline scenario you choose.  
- Lucy: either not present (lives elsewhere, visits) or in her room depending on baseline.  
- Others: initial locations that make narrative sense (e.g. not all in the same room unless that’s intended).

Implementation:

- Seed script must:
  - Create the locations and adjacency.  
  - Create objects.  
  - Set `agents.current_location_id` for each agent.


---

## SECTION 5 – AUTONOMY ENGINE BEHAVIOUR

Implement an **Autonomy Engine** module (or set of functions) that PFEE or the outer loop can call regularly.

Goals:

- Adjust drives, mood, and influence fields over time.  
- Adjust relationships slightly over time.  
- Advance arcs and intentions.  
- Decide when an agent wants to initiate interaction.

### 5.1 Inputs

- Current world time.  
- Agents’ `drives`, `mood`, `influence_fields`, `relationships`, `arcs`, `intentions`.  
- Calendars (upcoming or past events).  
- Recent memories (last N episodic events).

### 5.2 Rules (High-Level)

Implement the following classes of rules:

1. **Drive regulation**  
   - Drives slowly return toward a baseline if nothing reinforces or frustrates them.  
   - Specific events or memories can push drives up or down (e.g. neglecting a valued relationship raises attachment drive pressure).

2. **Mood drift**  
   - Mood slowly reacts to:
     - recent positive/negative interactions.  
     - progress or stagnation in arcs.  
   - Use small numeric changes each time step.

3. **Relationship evolution**  
   - If interactions are warm and consistent, gradually increase warmth and trust.  
   - If conflict/tension events accumulate, gradually raise tension and volatility.  
   - Use caps and smoothing, avoid wild jumps.

4. **Arc progression**  
   - If behaviour and events are aligned with an arc’s “desired outcome”, slowly raise `progress`.  
   - If things oppose it, create internal tension (stored in arcs or influence fields).

5. **Influence field updates**  
   - Unresolved topics (e.g. secrecy vs going public) gradually increase pressure over time.  
   - When pressure exceeds a threshold, mark the topic as “ripe” for conversation or action.

6. **Initiative decision**  
   - For each agent (except George), compute an “initiative score” based on:
     - drive pressures  
     - unresolved tensions in influence fields  
     - important arcs with low progress  
   - If the score passes a threshold and context allows, mark the agent as wanting to initiate a perception event.

Implementation details:

- Place these rules in a dedicated module (e.g. `autonomy_engine.py`).
- Provide functions like:
  - `update_agent_psychology_over_time(session, world_time)`  
  - `compute_initiative_candidates(session, world_time)`

PFEE or the outer loop will call these periodically.


---

## SECTION 6 – PFEE INTEGRATION CHANGES

Modify existing PFEE modules so they use the seeded data and autonomy outputs.

### 6.1 world_state_builder

Update world_state_builder to:

- Use real locations and adjacency from the DB, not hardcoded defaults.  
- For the current user (George), fetch:
  - present location  
  - other agents present in that location  
- For each present agent:
  - load `drives`, `mood`, `personality_kernel`, `personality_summaries`, `domain_summaries`, `status_flags`.  
  - load relevant `relationships` to George and others present.  
  - load active `arcs`, especially those related to the current situation.  
  - load recent, high-salience memories relevant to:
    - the user  
    - the current location  
    - the current topics stored in influence fields.

- Build a world_state dict that explicitly includes:
  - physical context (where, when, who)  
  - numeric internal state (not for George)  
  - relationships  
  - active arcs  
  - active influence field entries.

### 6.2 Semantic Mapping (PFEESemanticMapper)

Ensure semantic mapping:

- Converts numeric drives, mood, relationships, arcs, and influence fields into structured semantic descriptions:
  - short phrases, tags, and short paragraphs describing:
    - “how this person tends to be”  
    - “how they currently feel”  
    - “what themes are active for them”  
    - “how their relationship to George feels right now”.

- Draws from:
  - `personality_summaries`  
  - `domain_summaries`  
  - `status_flags`  
  - arcs and memories (for context)  
  - relationship vectors.

- Does **not** expose raw numeric values (0.82 etc.) or internal field names.

The output must be usable as part of the cognition prompt.

### 6.3 Cognition Eligibility and Input Builder

- Ensure that the functions deciding “who is eligible for cognition” use:
  - initiative signals from the Autonomy Engine.  
  - drive pressures.  
  - influence field topics.  
  - arcs and relationships.

- The final cognition input must contain:
  - description of the physical scene.  
  - semantic descriptions of each agent’s inner state (except George).  
  - active arcs and tensions.  
  - relevant memories.

Cognition must see a rich, yet concise summary of “what is going on” from each agent’s perspective.

### 6.4 Consequence Integration

- When cognition returns outputs (thoughts, intentions, relationship changes, mood changes, arc updates, memories):

  - Apply them to:
    - `intentions`  
    - `relationships`  
    - `arcs`  
    - `memories`  
    - `drives`  
    - `mood`  
    - `pfee_influence_fields`

- Ensure:
  - No inner updates are applied to George.  
  - Changes are validated against world_state and your validation module.  
  - Episodic memories are added only for agents, not George.  
  - Relationship drift is consistent with the Autonomy rules.


---

## SECTION 7 – OUTER LOOP / TIME PROGRESSION

Implement a simple outer loop process (e.g. a background task or scheduled job):

- On a fixed interval (e.g. every N seconds/minutes of real time, mapped to M minutes of world time):

  1. Advance world time using `TimeAndContinuityManager`.  
  2. Call Autonomy Engine to update agents’ psychological state.  
  3. Ask Autonomy Engine who wants to initiate.  
  4. For each candidate, run PFEE’s perception orchestrator:
     - Build world_state.  
     - Build cognition input.  
     - Call cognition.  
     - Validate and integrate consequences.  
     - Log the cycle.

This outer loop must:

- Never invent George’s initiative.  
- Only use candidate agents (not George) for autonomous actions.  
- Respect time continuity rules (no spontaneous big jumps without instructions).


---

## SECTION 8 – TEST SUITE (SUMMARY OF WHAT MUST BE COVERED)

Implement tests that verify:

1. Rebecca’s seeded personality, drives, mood, and relationships match the mapping rules.  
2. Rebecca’s key memories and arcs exist and have correct salience and status.  
3. George has no arcs, no influence fields, no memories as agent, no personality kernel from PFEE.  
4. PFEE’s world_state includes the seeded Cookridge locations and correct adjacency.  
5. Semantic mapping uses Rebecca’s seeded traits and relationships when building cognition input.  
6. Autonomy Engine:
   - changes drives/mood slowly over time  
   - adjusts relationships  
   - advances arcs  
   - identifies initiative candidates  
7. PFEE perception cycles triggered by autonomy decisions:
   - produce deterministic results given fixed cognition outputs  
   - update DB as expected  
   - never violate the George rules.  

(You may reuse and extend the earlier detailed test suite spec already provided.)

---

## SECTION 9 – NON-NEGOTIABLE CONSTRAINTS

- Do not invent internal state for George beyond what is explicitly allowed.  
- Do not bypass the mapping rules; all data from files must be explicitly mapped.  
- Do not expose raw internal numeric values to the LLM in prompts.  
- Do not create new schema tables unless absolutely necessary; use the existing schema as designed.  
- Any extension to PFEE must remain deterministic given the same starting database state and the same cognition outputs.

---

End of blueprint.
Follow every instruction above literally and systematically.
Do not optimise for brevity.
Do not improvise system behaviour beyond what is specified.
