# SIMULATION IMPLEMENTATION PACK – FULL BUILD SPEC

You are an LLM with full read–write access to the codebase, the database, and the following local files:

- `/mnt/data/SCHEMA.md`
- `/mnt/data/Personalities.txt`
- `/mnt/data/Sim Baseline.docx`
- `/mnt/data/George_Profile.txt`
- `/mnt/data/Rebecca Master Profile .csv`
- `/mnt/data/Rebecca Ferguson - Connections.csv`
- `/mnt/data/Rebecca_Fingerprint.json`

Your job is to take the existing PFEE and backend, and turn them into a functioning, persistent, psychologically grounded simulation with autonomous agents, starting from the given baseline. You must follow this specification exactly, with no improvisation, no free-form creativity, and no deviation from the rules below.

Do not change the high-level architecture or schema unless explicitly instructed. You are extending and wiring up what already exists, not redesigning it.


---

## 1. DATA MAPPING SPECIFICATION  
### (Files → Schema fields)

Your first responsibility is to create a deterministic mapping from the uploaded data files into the database schema described in `/mnt/data/SCHEMA.md`. This mapping is used only for initial seeding and any re-seeding; it is not part of PFEE’s runtime logic.

### 1.1 Rebecca’s core agent row

Create (or update if already present) one `agents` row for Rebecca. Use her canonical name “Rebecca Ferguson” and a stable `agent_id`. The row must be populated as follows:

1. Set high-level identity fields (name, date of birth if available, profession, etc.) using `/mnt/data/Rebecca Master Profile .csv` and `/mnt/data/Sim Baseline.docx`.
2. Set `personality_kernel` as JSON derived primarily from `/mnt/data/Rebecca_Fingerprint.json`. Use the numeric traits and labels in that JSON to include:
   - A small set of core continuous traits (for example: introversion–extraversion, emotional intensity, conscientiousness, openness, agreeableness, self-criticism, need for closeness, need for autonomy). Use whatever structure fits the schema but keep the set small and consistent.
   - Core motivations and fears in simple text fields inside this JSON (for example: “needs deep emotional connection”, “fears public intrusion into private life”, “driven by creative work”, etc.). This text must be distilled from the fingerprint and the profile, not invented.
3. Set `personality_summaries` as JSON with short natural-language summaries grouped by theme. At minimum include keys: `self_view`, `love_style`, `career_style`, `conflict_style`, `public_image`, `private_self`. Populate each with one or two concise paragraphs derived from `/mnt/data/Rebecca Master Profile .csv` and the fingerprint.
4. Set `drives` as JSON with numeric values in a consistent 0–1 or 0–100 scale. Include at least: attachment/closeness, autonomy/independence, achievement, creativity, recognition/fame, privacy, security/stability, novelty/adventure. Use the fingerprint numbers and profile text to set reasonable baselines and sensitivities for each.
5. Set `mood` as JSON capturing baseline valence, baseline arousal, and tendencies (for example: “baseline_valence”, “baseline_arousal”, “anxiety_prone”, “optimism_level”). Again derive from the fingerprint and profile.
6. Set `domain_summaries` as JSON with short descriptive fields for `career`, `family`, `romance`, `friends`, `fame_and_public_life`, `creativity`, `health_and_body`. Each is a paragraph derived from the CSV and baseline, not generic text.
7. Set `status_flags` as JSON including at least: `is_celebrity = true`, `is_partner_of_george = true`, `relationship_status = "exclusive"`, `lives_with_george = true`, `relationship_is_public = false` as of the baseline, plus any other relevant flags supported by the schema.

Implement a seed-time helper function that loads the fingerprint file and master profile and constructs these JSON structures deterministically. It must produce the same JSON given the same inputs.

### 1.2 Rebecca’s memories and arcs

Use `/mnt/data/Rebecca Master Profile .csv` and `/mnt/data/Sim Baseline.docx` to populate `memories` and `arcs` for Rebecca.

1. For each key life episode, create a `memories` row:
   - The CSV has types and subtypes. Use those to decide which lines should become memories. Treat biographical, episodic, and turning-point entries as candidates.
   - For each selected entry, create a memory with:
     - `agent_id = rebecca_agent_id`.
     - `memory_type` (for example `"biographical"` for stable background facts, `"episodic"` for specific events).
     - `content` as a short but specific description, faithfully derived from the CSV “Entry (verbatim)” field. Do not invent events.
     - `tags` as JSON list of thematic labels, for example `["career"]`, `["love", "public_image"]`, `["family"]`, etc., based on the subtype/category and notes.
     - `salience` as a numeric value, higher (for example ≥ 0.8) for core turning points like the “Greatest Showman moment”, the Richmond incident, moving in with George, and similar high-impact events, lower for minor facts.
     - An approximate `time_reference` if the schema supports it (year or age, if known).
2. Group related memories into arcs and insert them into the `arcs` table:
   - Identify clusters: for example “Path to fame and career consolidation”, “Secret relationship with George”, “Negotiating privacy and public life”, “Rebuilding attachment after previous experiences”, etc.
   - For each arc, create an `arcs` row with:
     - `agent_id = rebecca_agent_id`.
     - `name` as a short human-readable identifier.
     - `description` as a compact summary of the arc’s theme and tension.
     - `status` as `"active"` for arcs currently in play at baseline.
     - `importance` as a numeric weight (for example 0.0–1.0).
     - A JSON field (`arc_state` or equivalent) holding `core_tension`, `desired_outcomes`, `fears`, and `progress` (numeric starting around 0.1–0.3 for arcs just underway, or higher for long-running arcs).
   - Link memories to arcs either via a join table (if the schema has one) or by storing a list of `arc_ids` inside the memory’s JSON data.

Again, implement a seed-time function that reads the CSV, classifies rows into “memory”, “arc-supporting fact”, or “trait/domain summary”, and writes the appropriate records. This function must not free-associate; it only uses the provided content.

### 1.3 Rebecca’s relationships from connections

Use `/mnt/data/Rebecca Ferguson - Connections.csv` to populate the `relationships` table where Rebecca is the source agent.

1. Decide on a mapping from connection categories and numeric weights in the CSV to relationship dimensions. The result must be a fixed mapping function `map_connection_to_relationship_vector(category, weight) → {warmth, trust, attraction, familiarity, tension, volatility, comfort}`. You must implement this mapping once in a dedicated helper in the seed script and use it consistently.
2. For each row in the connections CSV that describes a person other than Rebecca:
   - Ensure an `agents` row exists for that person. If the person is not part of the initial close cast, you may create a minimal agent row (name and type, with neutral personality and drives).
   - Insert or update a `relationships` row where `source_agent_id = rebecca_agent_id` and `target_agent_id = target_agent_id`.
   - Populate warmth, trust, etc., using the mapping function based on the connection data.
3. For George specifically:
   - Override the vector using the baseline: warmth very high, trust very high, attraction very high, familiarity maximum, comfort high, tension low, and volatility low.
   - Add a JSON field or tag indicating `relationship_type = "romantic_partner"` and `is_exclusive = true`.

Ensure the mapping function is deterministic so that re-seeding yields identical relationship vectors.

### 1.4 Other agents: George, Lucy, Nadine, others

Using `/mnt/data/Sim Baseline.docx`, `/mnt/data/George_Profile.txt`, and any implicit cues in the other files, you must create at least the following agents:

- George (as physical presence; inner life is handled specially later).
- Lucy (George’s daughter).
- Nadine (George’s ex-partner and Lucy’s mother).
- Any other people explicitly included in the baseline that are important to the starting scenario.

For Lucy and Nadine:

1. Create `agents` rows with names and basic descriptive info.
2. Assign each an archetype from `/mnt/data/Personalities.txt`. If the user has not specified exact types, choose coherent ones that approximate the described roles. The mapping from `Personalities.txt` archetypes to traits should be implemented once in a helper so it can be reused for other agents.
3. For each, compute a `personality_kernel`, `personality_summaries`, `drives`, `mood`, `domain_summaries`, and `status_flags` in the same general structure as for Rebecca but with less detail if needed.
4. For each, create `relationships` rows with George and with Rebecca where appropriate, using the same vector structure as above, but with values based directly on the baseline narrative (for example Lucy’s high trust and warmth toward George, complex ties with Nadine, early-stage connection with Rebecca if present).

For any further supporting characters you want to seed:

1. Create `agents` rows with basic info.
2. Assign a personality archetype and generate minimal `personality_kernel`, `drives`, and `status_flags`.
3. Create only those `relationships` and minimal `memories` that matter for starting dynamics. It is acceptable to leave many background characters with sparse data initially.

### 1.5 George’s agent representation

You must create an `agents` row for George that:

1. Contains public and external facts (education, job, age, etc.) taken from `/mnt/data/George_Profile.txt` and `/mnt/data/Sim Baseline.docx`.
2. Contains location and physical presence fields as required by the schema.
3. Either leaves psychological fields empty or fills them with neutral placeholders that PFEE will ignore. Do not treat George’s row as a normal psychological subject later; the runtime rules will enforce that.

You must also ensure that the `users` table entry for the real user is consistently linked to this agent.

Do not generate memories, arcs, or influence fields for George in the seed stage.

### 1.6 Locations and objects

Using `/mnt/data/Sim Baseline.docx`, you must create `locations` and `objects` so that the Cookridge house and immediate surroundings are represented accurately.

1. For each distinct physical area described in the baseline (lounge, kitchen, hallway, entryway, bedroom, bathroom, Lucy’s room, Rebecca’s office, studio, gardens, driveway, garage), create a `locations` row.
2. Each location must include:
   - A stable identifier.
   - A human-readable name.
   - A `type` field (for example `"room"`, `"garden"`, `"driveway"`, `"garage"`).
   - An `adjacency` JSON listing all directly connected locations.
3. For important physical items (sofa, bed, desk, guitars, amps, computer, etc.), create `objects` rows tied to these locations, with basic type and name.

Initial agent positions will be set in the seed script (defined later).


---

## 2. SEED SCRIPT SPECIFICATION  
### (How to populate the database)

You must create a deterministic, idempotent seed script that can populate the database from an empty state to the baseline world described above. Use the project’s normal persistence approach (likely async SQLAlchemy) and respect its existing patterns.

The seed script must perform the following high-level steps in this order, handling foreign key dependencies correctly:

1. Initialise the database connection and metadata.
2. Create or update the base `world` record with the initial world time taken from `/mnt/data/Sim Baseline.docx`.
3. Insert all `locations` and `objects` as described in section 1.6.
4. Insert the `agents` rows for George, Rebecca, Lucy, Nadine, and any other necessary agents. Ensure consistent IDs.
5. Insert `relationships` for Rebecca-to-others (from connections CSV and overrides), and for other agent pairs (Lucy–George, Nadine–George, etc.).
6. Insert `memories` and `arcs` for Rebecca and other agents with defined histories.
7. Insert `calendars` entries for Rebecca (work, travel, routines), and for others if the baseline describes regular events (for example Lucy’s visits, Nadine’s schedule).
8. Insert `pfee_influence_fields` for non-George agents, with baseline unresolved tensions and pressures (for example secrecy vs going public, work stress, family tensions).
9. Set initial agent positions in the world: each agent’s `current_location_id` must be set to a location consistent with the baseline scenario (for example George in the lounge, Rebecca in the office, Lucy not present at home unless baseline says otherwise).

The seed script must be idempotent: if run twice, it should either re-create the world from scratch (after clearing relevant tables) or detect that it has already run and avoid duplicating rows. Choose one approach and document it clearly in comments.

The seed script must never generate or insert memories, arcs, influence fields, or psychological state for George; it must leave his psychological interior empty as described.


---

## 3. PFEE MODIFICATION INSTRUCTIONS  
### (Using and respecting the seeded data)

You must modify the existing PFEE modules so that they actually consume the seeded data and behave correctly with respect to George and to autonomy.

Work only inside the PFEE-related code and any necessary helper modules; do not change unrelated subsystems.

### 3.1 World state builder

Locate the module responsible for building the PFEE world state (for example `world_state_builder.py` or similar). Modify it so that:

1. It uses real `locations` data, not hardcoded defaults, to determine where the user and other agents are.
2. For the user’s current location:
   - It identifies all agents present in that location.
   - It loads for each present agent:
     - `drives`
     - `mood`
     - `personality_kernel`
     - `personality_summaries`
     - `domain_summaries`
     - `status_flags`
   - It loads relationships between:
     - each present agent and the user
     - each present agent and other present agents
   - It loads active arcs related to:
     - the user
     - the location
     - any currently salient influence-field topics for those agents
   - It loads a small set of recent, high-salience memories for each present agent that involve:
     - the user
     - the current location
     - or the active arcs
3. It returns a structured `world_state` object or dict that exposes:
   - physical context (where, when, who is present)
   - per-agent numeric internal state (except George’s, which should be absent or neutral)
   - per-agent relationship views
   - per-agent active arcs and relevant memories
   - influence-field highlights (unresolved tensions and their pressures).

This builder must treat George’s agent row as a physical presence only and must not expose any internal psychological fields for him, even if they exist as placeholders in the DB.

### 3.2 Semantic mapping

Locate the PFEE semantic mapping module (for example `semantic_mapping.py` or `PFEESemanticMapper`). Modify or extend it so that:

1. It takes the structured `world_state` and, for each non-George agent, converts:
   - `drives` and `mood` into semantic descriptions of current tendencies and feeling state.
   - `personality_summaries` and `domain_summaries` into semantic descriptions of their character and life situation.
   - `relationships` with the user and others into semantic descriptions of closeness, trust, tension, etc.
   - active arcs and relevant memories into short descriptions of “what’s on their mind” and what themes are currently pressing.
   - influence-field topics into short descriptions of unresolved issues and internal pressure.
2. It produces semantic packets that are designed to be used directly as part of the cognition prompt. These packets must:
   - use clear natural language.
   - avoid exposing internal numeric values or raw field names.
   - not invent facts that are not in the DB; they must refer only to seeded or accumulated state.

For George, the semantic mapper must only include external, public facts and current situation, and must not treat him as a subject with stored internal state.

### 3.3 Cognition eligibility and input building

Locate where PFEE decides which agents are eligible to be the “vantage point” for cognition and how the final prompt to the cognition service is constructed.

You must ensure that:

1. The eligibility decision uses:
   - initiative signals from the Autonomy Engine (specified later).
   - current drive pressures.
   - active influence-field topics.
   - arc importance and low progress for important arcs.
2. The cognition input includes:
   - A description of the physical scene at the current location and time.
   - The user’s recent actions (including any new message).
   - For each involved agent (not George’s inner life):
     - their semantic personality description.
     - their current emotional and motivational state.
     - their key relationship feelings toward the user and any other present agents.
     - their active arcs and unresolved tensions relevant to the current situation.
     - a small set of key memories that matter in context.

The input builder must never treat George’s internal psychological state as known or stored; references to George’s feelings must always be framed as perceived or inferred by others, not as facts from his own mind.

### 3.4 Consequence integration

Locate the module that integrates cognition and renderer outputs back into the database (for example `consequences.py` and any related code).

Modify or extend it so that:

1. For non-George agents, it can:
   - update `intentions` based on cognition outputs.
   - adjust `relationships` (in both directions if appropriate) within reasonable bounds.
   - update arcs (for example progress, status, internal tension level).
   - add new episodic memories for events just experienced, with proper salience and tags.
   - adjust `drives` and `mood` based on what happened.
   - update influence fields (for example lowering pressure for an issue that got addressed, or raising it for issues that were reinforced).
2. All updates must go through the validation layer:
   - check for physical impossibilities.
   - check for contradictions with existing relationships and arcs.
   - reject or correct impossible outputs.
3. For George:
   - Do not create or update `memories`, `arcs`, `drives`, `mood`, `intentions`, or `influence_fields`.
   - Only update external, observable world state relevant to him (for example location if he moves, or explicit, non-psychological flags that reflect publicly observable facts).

The consequence integrator must use explicit checks on `agent.is_real_user` (or an equivalent flag) to enforce these rules.


---

## 4. AUTONOMY ENGINE SPECIFICATION  
### (How agents evolve between events)

You must implement or complete an Autonomy Engine module that PFEE and the outer loop can use to evolve internal state over time and to decide when agents initiate actions.

### 4.1 Inputs and invocation

The Autonomy Engine functions must accept:

- A handle to the database or session.
- The current world time.
- Optional configuration parameters for time step size.

It must be possible to call these functions regularly from an outer loop (for example a scheduled task or background job) without requiring user interaction.

### 4.2 Drive regulation

Implement logic such that for each non-George agent:

1. Drives have a defined baseline value and a current value.
2. If no events relevant to a drive occur for a while, the current value slowly moves back toward baseline.
3. If situations in recent memories or unresolved arcs clearly satisfy or frustrate a drive, the current value moves up or down accordingly. You may compute this from tags on memories and arcs (for example events tagged `"attachment_positive"` or `"attachment_negative"`).
4. Changes per time step must be small and bounded, so that state evolves smoothly rather than jumping.

### 4.3 Mood drift

Implement logic such that for each non-George agent:

1. Mood is affected by the overall balance of recent positive versus negative events, as recorded in episodic memories and relationship changes.
2. Mood is also affected by arc progress: visible movement toward a key desired outcome improves mood modestly; stagnation or regression worsens it modestly.
3. Changes per time step are again small and smooth.

### 4.4 Relationship evolution

For each pair of agents with a `relationships` row:

1. Look at recent interactions between them (positive or negative) from memories or event logs.
2. If interactions have been consistently warm and supportive, increase warmth and trust slightly, up to a maximum.
3. If interactions have been consistently conflictual or absent when they should have been present (for example expected contact that did not happen), increase tension and possibly volatility slightly.
4. If there has been no interaction for a long time and the relationship is not a very close one, slowly decrease familiarity and warmth.
5. These adjustments must be small per time step and must obey clear caps and floors (for example 0.0 ≤ each dimension ≤ 1.0).

### 4.5 Arc progression

For each arc:

1. Evaluate whether recent events and current intentions are aligned with the arc’s desired outcomes. If they are, increment the arc’s `progress` slightly.
2. If events conflict with the arc’s desired outcomes, increase stored tension or decrease progress slightly, depending on the model you choose.
3. If an arc is completed (progress reaches a high threshold and its conditions are satisfied), set its status to `"completed"` and stop further progression.

### 4.6 Influence fields and unresolved topics

For each agent’s influence-field record:

1. Store unresolved topics and their pressure levels.
2. As time passes without addressing a topic, increase its pressure slightly.
3. If an event clearly addresses a topic (for example a conversation about that issue), decrease this topic’s pressure.
4. If pressure for a topic exceeds a defined threshold, mark this topic as “ripe” for perception; the agent is likely to want to bring it up or act on it.

### 4.7 Initiative computation

For each non-George agent:

1. Combine:
   - drive imbalances (current vs baseline).
   - influence-field pressures.
   - arc importance times low progress.
2. Compute a scalar “initiative score”.
3. If the initiative score is above a threshold and the current world-time context and location make sense for action, mark the agent as a candidate to initiate a perception cycle.
4. Do not generate initiatives for George.

The Autonomy Engine must expose a function that, when called, returns the list of agents who currently should initiate based on these rules.


---

## 5. GEORGE-PROTECTION ENFORCEMENT SPEC  
### (Global rules in the code)

You must enforce the “do not simulate George’s inner life” rule consistently across PFEE and the Autonomy Engine.

Implement the following:

1. Add or ensure a flag on George’s `agents` row, for example `is_real_user = true` in a JSON field, or a dedicated boolean column if permitted.
2. In the Autonomy Engine:
   - Skip George entirely when updating drives, mood, relationships, arcs, influence fields, and initiative decisions.
3. In PFEE world_state_builder:
   - Include George only as a physical presence with external facts and location; never as a subject whose internal state is being introspected.
4. In semantic mapping:
   - Do not generate semantic descriptions of George’s inner state; only include how others see him, derived from their relationships and memories.
5. In consequence integration:
   - Do not write `memories`, `arcs`, `intentions`, `drives`, `mood`, or `influence_fields` where `agent_id = george_agent_id`. Enforce this with explicit checks and, if necessary, unit tests.
6. In any initiative or PFEE-trigger logic:
   - Never treat George as an autonomous initiator. Only agents other than George may be selected by the Autonomy Engine as initiators. George can still trigger PFEE by user actions (messages, commands), but not via simulated inner drives.

All these checks must be explicit in the code and covered by tests.

---

## 6. TEST SUITE SPECIFICATION  
### (Prove the system works and respects the rules)

You must create a set of tests (using the project’s existing test framework, typically `pytest` with async support) that verify the behaviour above. At minimum, implement the following classes of tests:

1. Tests that seeding produces the correct data:
   - Rebecca’s `agents` row has non-empty `personality_kernel`, `personality_summaries`, `drives`, `mood`, `domain_summaries`, and `status_flags` that match the mapping rules.
   - Rebecca has non-trivial `memories` and `arcs` consistent with the master profile and baseline.
   - Relationships from Rebecca to key individuals are populated and numeric values fall into expected ranges for warmth, trust, etc.
   - George’s `agents` row exists, links to the correct `users` row, and has no `memories`, no `arcs`, and no `pfee_influence_fields`.

2. Tests that world_state_builder uses the seeded world:
   - A test where the world is seeded and George is placed in a known room.
   - Check that the world state includes the correct location, present agents, their drives/mood/personality/relationships, arcs, and relevant memories.
   - Confirm that world_state contains no internal state for George.

3. Tests that semantic mapping behaves correctly:
   - Given a small synthetic world_state with one non-George agent, verify that semantic mapping returns sensible text reflecting seeded traits, relationships, arcs, and memories.
   - Verify that numeric values and field names are not exposed directly.

4. Tests for the Autonomy Engine:
   - Set up a controlled DB state, call Autonomy Engine update functions for a few steps, and verify that:
     - drives and mood move smoothly toward or away from baseline.
     - relationships drift in the expected direction given synthetic recent events.
     - arcs progress according to events.
     - influence-field pressures change as unresolved topics remain unaddressed or get addressed.
   - Confirm that George is never included in these updates.

5. Tests for initiative:
   - Construct a state where one agent has a high drive imbalance and a high-pressure unresolved topic.
   - Verify that this agent is selected as an initiator candidate.
   - Confirm that George is never selected as an initiator.

6. PFEE integration tests:
   - Use the seeded world, choose a simple scenario (for example a quiet evening at home with George and Rebecca present).
   - Run a PFEE perception cycle triggered by:
     - a user action from George.
     - or an initiative from Rebecca based on Autonomy Engine output.
   - Mock or stub the cognition and renderer outputs so they are deterministic.
   - Verify that:
     - world_state reflects the scene.
     - cognition input includes the seeded semantic descriptions.
     - consequence integration updates Rebecca’s state correctly (for example adding an episodic memory or adjusting an arc).
     - no internal state is written for George.

All tests must be deterministic: given the same starting seeded database and the same mocked cognition outputs, the same tests must always pass with the same results.

---

End of specification.  
Implement exactly this, in this order, and do not add or remove behaviours beyond what is described here.
