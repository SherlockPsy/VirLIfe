# FULL DATA-MAPPING SPECIFICATION  
# (RAW FILES → DATABASE SCHEMA FIELDS)

# PURPOSE
# You must implement a deterministic, lossless, unambiguous mapping from:
#   - Personalities.txt
#   - Sim Baseline.docx
#   - George_Profile.txt
#   - Rebecca Master Profile.csv
#   - Rebecca Ferguson - Connections.csv
#   - Rebecca_Fingerprint.json
#
# into the following schema fields:
#   - agents
#   - relationships
#   - memories
#   - arcs
#   - intentions
#   - calendars
#   - pfee_influence_fields
#   - locations
#   - objects
#
# This specification tells you EXACTLY how to convert every part of the input data
# into the correct database state for the baseline world. No improvisation,
# no summarisation, no invention of facts. Only structured conversion.

###################################################################################################
# 1. AGENT CREATION AND ATTRIBUTE MAPPING
###################################################################################################

# 1.1 CREATE CANONICAL AGENT ROWS
# Create an `agents` row for each of the following:
#   - George (REAL USER – special rules later)
#   - Rebecca Ferguson (PRIMARY ANCHOR AGENT)
#   - Lucy (daughter)
#   - Nadine (ex-partner)
#   - Any close contacts explicitly mentioned in Sim Baseline (e.g., friends, collaborators)
#   - Any individuals directly connected to Rebecca in the Connections CSV whose connection
#     type implies meaningful influence (family, close friends, recurring collaborators).
#   - Any other auxiliary individuals may be seeded as “minimal agents”.

# The following fields MUST be populated for all non-George agents:
#   - identity fields: full name, gender if known, approx age if known
#   - personality_kernel (JSON)
#   - personality_summaries (JSON)
#   - drives (JSON)
#   - mood (JSON)
#   - domain_summaries (JSON)
#   - status_flags (JSON)
#   - origin metadata (JSON): specify “seeded_from” with file sources

# George’s agent row MUST omit or nullify psychological fields. (Full details in section E.)

###################################################################################################
# 1.2 PERSONALITY ARCHETYPES (Personalities.txt)
###################################################################################################

# The file Personalities.txt contains 15 archetypes. Each archetype includes:
#   - essence summary
#   - typical behaviours
#   - strengths
#   - vulnerabilities
#   - core drives
#   - tension points
#   - emotional coloration

# Mapping rule:
#   - You MUST parse all 15 archetypes into a canonical internal structure:
#       {
#         "name": ...,
#         "core_traits": [...],
#         "motivations": [...],
#         "fears": [...],
#         "drives": {...},
#         "tensions": [...],
#         "behavioural_style": ...
#       }
#   - This parsed structure MUST NOT be stored raw in the DB.
#   - It MUST be used to construct personality_kernel for each non-George agent.
#   - Rebecca’s archetype blend MUST be determined using Rebecca_Fingerprint.json as the anchor.

###################################################################################################
# 1.3 REBECCA'S PERSONALITY (Rebecca_Fingerprint.json)
###################################################################################################

# Rebecca_Fingerprint.json contains a structured numerical trait system.
# YOU MUST use the fingerprint as the PRIMARY numerical input for:
#   - personality_kernel
#   - drives baseline & sensitivities
#   - mood baseline tendencies
#   - domain_summaries
#   - behavioural markers in personality_summaries
#   - status_flags

# The fingerprint must be mapped to the following kernel keys:
#   personality_kernel = {
#     "trait_dimensions": {
#         "<dimension_name>": <value>,   # Each dimension from fingerprint preserved
#     },
#     "core_motivations": [...],         # Extract from fingerprint + profile text
#     "core_fears": [...],
#     "internal_conflicts": [...],
#     "archetype_blend": {
#         "<archetype_name>": <percentage>
#     }
#   }

# NOTE:
#   - archetype_blend MUST be computed by cosine similarity or nearest-match scoring
#     between fingerprint traits and archetype descriptors from Personalities.txt.
#   - This computation MUST be deterministic: given the same fingerprint and text,
#     produce the same blend.

###################################################################################################
# 1.4 PERSONALITY_SUMMARIES (Rebecca Master Profile.csv + Fingerprint)
###################################################################################################

# personality_summaries MUST be a JSON object with EXACT keys:
#   - self_view
#   - love_style
#   - career_style
#   - conflict_style
#   - public_image
#   - private_self

# For each key, you must:
#   1. Extract all facts from the master profile CSV that belong to relevant categories.
#   2. Compress them into 4–8 sentences per field.
#   3. Never invent facts.
#   4. Use fingerprint tendencies to choose emphasis.

# Example mapping process (non-exhaustive):
#   CSV subtype “Personality” → self_view, conflict_style
#   CSV category “Career” → career_style, public_image
#   CSV category “Fame/Public Life” → public_image
#   CSV category “Romance” → love_style
#   CSV category “Family” → private_self

###################################################################################################
# 1.5 DRIVES (Fingerprint + Archetypes)
###################################################################################################

# The drives field must have keys:
#   {
#     "attachment": {"baseline": x, "sensitivity": y},
#     "autonomy": {"baseline": x, "sensitivity": y},
#     "achievement": {...},
#     "creativity": {...},
#     "recognition": {...},
#     "privacy": {...},
#     "security": {...},
#     "novelty": {...}
#   }

# Mapping rules:
#   - PRIMARY: fingerprint numeric values → baseline
#   - SECONDARY: archetype pressures → sensitivity
#   - CONSISTENCY: values must be in 0–1 or 0–100 scale (choose one globally)

###################################################################################################
# 1.6 MOOD (Fingerprint + Baseline doc)
###################################################################################################

# mood JSON MUST contain:
#   {
#     "baseline_valence": ...,
#     "baseline_arousal": ...,
#     "anxiety_prone": ...,
#     "frustration_prone": ...,
#     "optimism_tendency": ...
#   }

# Derive all values from fingerprint categories (emotional reactivity, stability, etc.)
# and supporting descriptions in the CSV and baseline document.

###################################################################################################
# 1.7 DOMAIN_SUMMARIES (Master Profile CSV)
###################################################################################################

# domain_summaries MUST have keys:
#   - career
#   - family
#   - romance
#   - friends
#   - fame_and_public_life
#   - creativity
#   - health_and_body

# For each key:
#   - Extract raw lines from the CSV matching the domain.
#   - Condense into a structured paragraph (not summary, but compressed factual content).
#   - No invented material.

###################################################################################################
# 1.8 STATUS_FLAGS (Baseline doc + Profile)
###################################################################################################

# status_flags MUST include:
#   {
#     "is_celebrity": true,
#     "is_partner_of_george": true,
#     "relationship_status": "exclusive",
#     "lives_with_george": true,
#     "relationship_is_public": false,
#     ...other factual flags derived from the baseline
#   }

# These flags help PFEE make correct decisions quickly.

###################################################################################################
# 1.9 RELATIONSHIPS (Rebecca Ferguson - Connections.csv)
###################################################################################################

# Mapping specification:
#   For each row in connections CSV:
#     1. Create or ensure existence of the target agent.
#     2. Map connection category + strength to a numeric vector:
#         {
#           "warmth": ...,
#           "trust": ...,
#           "attraction": ...,
#           "familiarity": ...,
#           "tension": ...,
#           "volatility": ...,
#           "comfort": ...
#         }
#
#     You MUST create a deterministic mapping:
#       - Identify all categories used in the CSV.
#       - Assign a numeric tuple for each category.
#       - Multiply or modulate by the strength value (if provided).
#
# SPECIAL RULE:
#   George’s relationship vector MUST override the original mapping:
#     - warmth, trust, familiarity, attraction: MAX
#     - tension: LOW
#     - volatility: VERY LOW
#     - comfort: HIGH
#   All derived from baseline document.

###################################################################################################
# 1.10 MEMORIES (Rebecca Master Profile.csv + Baseline doc)
###################################################################################################

# You MUST create memories using:
#   - episodic events
#   - biographical facts
#   - origin facts
#   - turning points
#   - career milestones
#   - relational milestones

# Format:
#   memories table requires:
#     agent_id
#     type ("biographical" / "episodic")
#     content
#     tags (JSON)
#     salience (0–1)
#     time_reference (nullable)

# All memories must be:
#   - directly extracted from CSV or Baseline doc
#   - never invented
#   - grouped by theme

###################################################################################################
# 1.11 ARCS
###################################################################################################

# Arcs represent ongoing tensions or life themes.

# You MUST create arcs for:
#   - Rebecca’s fame/private-life tension
#   - Relationship secrecy vs going public
#   - Career evolution
#   - Personal emotional evolution
#   - Any strong ongoing theme from the CSV

# Arc format:
#   {
#     "name": ...,
#     "description": ...,
#     "status": "active",
#     "importance": x,
#     "arc_state": {
#         "core_tension": ...,
#         "desired_outcomes": [...],
#         "fears": [...],
#         "progress": ...
#     }
#   }

###################################################################################################
# 1.12 INFLUENCE FIELDS
###################################################################################################

# Create a row in pfee_influence_fields for every non-George agent.

# Each field contains:
#   {
#     "unresolved_topics": {
#         "<topic>": {
#             "pressure": <numeric>,
#             "tags": [...],
#             "last_updated": <timestamp>
#         }
#     },
#     "background_bias": {
#         "warmth_bias": ...,
#         "avoidance_bias": ...,
#         "assertiveness_bias": ...,
#         ...
#     }
#   }

# Sources:
#   - topics from arcs
#   - tensions from fingerprint
#   - contact pressure from connections CSV
#   - unresolved issues from Baseline (e.g. secrecy vs going public)

###################################################################################################
# 1.13 CALENDARS
###################################################################################################

# For Rebecca, populate calendar entries:
#   - work routines
#   - travel obligations
#   - personal commitments
#   - recurring artistic practice
#   - any known scheduled events

# Format:
#   {
#     "agent_id": ...,
#     "title": ...,
#     "start_time": ...,
#     "end_time": ...,
#     "recurrence": <RRULE or null>,
#     "metadata": {...}
#   }

# Lucy and Nadine may have:
#   - visits
#   - custody schedules
#   - personal routines

###################################################################################################
# 1.14 INTENTIONS
###################################################################################################

# For non-George agents ONLY:
#   Seed initial intentions as JSON:
#     {
#       "agent_id": ...,
#       "type": "internal" / "external",
#       "description": ...,
#       "strength": <0–1>,
#       "target_agent_id": nullable,
#       "created_at": ...
#     }

# George MUST have zero intentions seeded.

###################################################################################################
# 1.15 LOCATIONS AND OBJECTS
###################################################################################################

# Extract locations from Baseline doc:
#   - Each room in Cookridge house becomes a location.
#   - Gardens, driveway, garage too.
#   - Add adjacency using the physical layout.

# Extract objects from Baseline doc (e.g. guitars, amps, furniture).

# Format:
#   objects table rows:
#     {
#       "name": ...,
#       "type": ...,
#       "location_id": ...,
#       "metadata": {...}
#     }

###################################################################################################
# END OF SECTION A
###################################################################################################


````markdown
# SECTION B — SEED-SCRIPT SPECIFICATION  
# (HOW TO POPULATE THE DATABASE FROM THE FILES AND MAPPING RULES)

# PURPOSE
# You must implement a deterministic, idempotent seed script that:
#   - Starts from an empty (or clean) database.
#   - Populates ALL required tables with the baseline world.
#   - Uses the mapping rules defined in SECTION A (data-mapping specification).
#   - Can be safely re-run without duplicating entities or corrupting the world.
#
# This document tells you EXACTLY what the seed script must do, in what order,
# and how it must behave. No improvisation, no skipping steps, no "creative" resets.


###################################################################################################
# B.0 GENERAL REQUIREMENTS
###################################################################################################

1. The seed script must live in a dedicated module in the backend, for example:
   - `backend/seeding/seed_baseline_world.py`
   or a logically equivalent path used by the project.

2. The script must:
   - Use the project’s standard async database layer (likely async SQLAlchemy).
   - Reuse existing model definitions from `backend.persistence.models` (or equivalent).
   - Call the mapping logic defined in SECTION A as helper functions, not re-implement it.

3. Idempotency:
   - The script must be safe to run multiple times.
   - You must choose and implement ONE of these strategies and document it clearly:
     - STRATEGY 1: **Wipe-and-reseed**  
       - Before seeding, delete all rows from the affected tables (or drop and recreate schema for them), then seed from scratch.  
       - This ensures the world is always re-created exactly.
     - STRATEGY 2: **Upsert-based**  
       - Check for the existence of a special "baseline world" marker row in a `world_metadata` table or equivalent.  
       - If found, skip seeding or update rows in-place without duplication.

   - STRATEGY 1 is simpler and RECOMMENDED unless your environment forbids deletes.

4. Determinism:
   - Any random choices (for example, assigning archetypes to minor agents) must use a fixed seed or avoid randomness entirely.
   - Given the same input files and same code, running the script must produce the same database state.

5. Logging:
   - The script must log key stages: start, each major step, and end.
   - Log counts inserted or updated for important tables (agents, relationships, memories, arcs, etc.).


###################################################################################################
# B.1 SCRIPT ENTRY POINT AND STRUCTURE
###################################################################################################

The seed script must expose a clear, single entry function, for example:

```python
async def seed_baseline_world(engine) -> None:
    """
    Seed the database with the baseline world using the mapping
    rules defined in SECTION A and these seeding rules.
    """
    ...
````

Inside this function, do the following high-level steps in order:

1. Create an AsyncSession from the engine.
2. Optionally run a "wipe" step if using STRATEGY 1.
3. Create or update the baseline `world` record.
4. Seed `locations` and `objects`.
5. Seed `agents` (George, Rebecca, Lucy, Nadine, others).
6. Seed `relationships`.
7. Seed `memories` and `arcs`.
8. Seed `pfee_influence_fields`.
9. Seed `calendars`.
10. Seed initial `intentions` (non-George).
11. Set initial positions for agents.
12. Commit all changes.
13. Log summary.

Each of these stages must call dedicated helper functions (e.g. `_seed_locations`, `_seed_agents`, etc.) that encapsulate the logic.

###################################################################################################

# B.2 WORLD INITIALISATION

###################################################################################################

### B.2.1 Create / Update the World Row

1. Inspect the `worlds` table (or equivalent) defined in `SCHEMA.md`.

2. Create one baseline `world` row, with:

   * A unique `world_id`, e.g. `"baseline_world"` or an integer primary key.
   * `name` set to something like `"George_Baseline_World"`.
   * `current_time` set according to the baseline:

     * Use the starting date and time from `Sim Baseline.docx`.
       If an exact date is not specified, choose a clear approximate, e.g. "today at 18:00", and FIX IT so that it is deterministic.
   * Any additional metadata fields describing:

     * that this world is the baseline world
     * the version of the seed script used.

3. If STRATEGY 2 (upsert) is used:

   * Check whether this world row already exists (by name or marker field).
   * If it exists, update its `current_time` and metadata if needed; otherwise create it.

###################################################################################################

# B.3 SEEDING LOCATIONS

###################################################################################################

### B.3.1 Read and Interpret Baseline Layout

1. Load `/mnt/data/Sim Baseline.docx`.
2. Extract all described physical areas of the Cookridge house and surroundings:

   * Lounge
   * Kitchen
   * Hallway
   * Entryway
   * Bedroom
   * Bathroom
   * Lucy’s room
   * Rebecca’s office
   * Studio / music room
   * Garden (front, back, side, decking)
   * Driveway
   * Double garage
3. For each distinct room/area, assign a stable identifier:

   * e.g. `"cookridge_lounge"`, `"cookridge_kitchen"`, etc.

### B.3.2 Insert Location Rows

For each identified location:

1. Create or update a row in the `locations` table with:

   * `id` (primary key).
   * `world_id` pointing to the baseline world created in B.2.
   * `name`: e.g. `"Lounge"` or `"Cookridge House – Lounge"`.
   * `type`: e.g. `"room"`, `"garden"`, `"driveway"`, `"garage"`.
   * `metadata` JSON that may include:

     * `"house": "Cookridge"` or similar.
     * `"floor": "ground"`, `"floor": "first"`, etc.

2. Build an adjacency graph based on the physical layout described in the baseline:

   * For example:

     * Lounge is adjacent to Hallway and Kitchen.
     * Hallway is adjacent to Entryway, Lounge, and maybe stairs.
     * Bedroom is adjacent to Landing/Hallway upstairs.
     * Garden areas are adjacent to Lounge or Kitchen depending on the description.
   * Write the adjacency list into each location’s `adjacency` JSON field, e.g.:

     * `"adjacent_to": ["cookridge_kitchen", "cookridge_hallway"]`.

3. Ensure the adjacency graph is:

   * Symmetric where appropriate (if A connects to B, B should connect to A, unless you intentionally model one-way connections).
   * Consistent: no references to non-existent locations.

### B.3.3 Validation

After seeding locations:

1. Query all locations for the baseline world.
2. Assert that:

   * All required rooms exist.
   * adjacencies are valid (no broken IDs).
3. Log the count and list of seeded location IDs.

###################################################################################################

# B.4 SEEDING OBJECTS

###################################################################################################

### B.4.1 Identify Significant Objects

Using `Sim Baseline.docx` and `George_Profile.txt`, identify any significant, recurring, or psychologically relevant objects, e.g.:

* Sofa, armchairs, dining table.
* Bed, wardrobe, bedside table, lamps.
* Desks (George’s desk, Rebecca’s desk).
* Musical instruments (guitars, amps, microphones, recording equipment) in the studio.
* Computer(s), screens, office equipment.
* Any characteristic decorative pieces that matter to interactions.

### B.4.2 Insert Object Rows

For each such object:

1. Assign a stable identifier: e.g. `"sofa_lounge"`, `"george_bed"`, `"rebecca_desk"`.

2. Insert or update a row in the `objects` table:

   * `world_id` = baseline world ID.
   * `location_id` = the correct room’s ID.
   * `name` = a human-readable label.
   * `type` = category, e.g. `"furniture"`, `"instrument"`, `"device"`.
   * `metadata` JSON that may include:

     * `"owner": "George"` or `"Rebecca"` if appropriate.
     * `"importance": <0–1>` if needed later for salience.

3. Do not overfill; focus on:

   * objects that can be reasonably referenced in cognition or in interactions.
   * objects tied to key arcs (e.g. musical instruments, workspace items).

###################################################################################################

# B.5 SEEDING AGENTS

###################################################################################################

The seed script must create agents for:

* George (user avatar, real person, special rules).
* Rebecca Ferguson.
* Lucy.
* Nadine.
* Any additional core contacts from the baseline (optional, but recommended).
* Any supporting contacts required by Rebecca’s connections mapping.

### B.5.1 Agent Factory / Helper

Implement a helper function for creating/updating an agent row:

```python
async def upsert_agent(session, *, name: str, world_id: Any, role: str, is_real_user: bool = False, **kwargs) -> Agent:
    """
    Create or update an agent row by name and world_id.
    Populate fields according to role (e.g., 'primary', 'family', 'supporting').
    Do NOT generate inner state for is_real_user=True, that is George.
    """
```

This helper must:

1. Check if an agent with this name and world_id already exists.
2. If yes, update its fields (except those intentionally immutable).
3. If no, create a new row with the given data.

### B.5.2 George Agent

1. Using George_Profile.txt and Sim Baseline.docx, create an agent row:

   * `name`: `"George"`.
   * `world_id`: baseline world.
   * external fields: age, education, job title, etc.
   * `is_real_user = true` flag (in JSON or dedicated column).
2. Psychological fields:

   * `personality_kernel` = NULL or `{}`.
   * `personality_summaries` = NULL or minimal external-only info.
   * `drives` = NULL or neutral.
   * `mood` = NULL or neutral.
   * `domain_summaries` = can include external factual context (career, skills) but MUST NOT be used later as inner psychology by PFEE.
   * `status_flags` should include `{"is_real_user": true}`.
3. No `memories`, `arcs`, `intentions`, or `pfee_influence_fields` should be created for George at seeding time.

### B.5.3 Rebecca Agent

1. Call the mapping layer from SECTION A to construct:

   * personality_kernel
   * personality_summaries
   * drives
   * mood
   * domain_summaries
   * status_flags

2. Use `upsert_agent` to create/update her row:

   * `name`: `"Rebecca Ferguson"`.
   * `role`: `"primary_partner"`.
   * `world_id`: baseline world.
   * `is_real_user`: False.
   * psychological JSON fields from mapping output.

3. Confirm that her `status_flags` include:

   * `is_celebrity = true`
   * `is_partner_of_george = true`
   * `relationship_status = "exclusive"`
   * `lives_with_george = true`
   * `relationship_is_public = false`

### B.5.4 Lucy Agent

1. Use baseline text to set:

   * `name`: `"Lucy"`.
   * `role`: `"daughter"`.
   * `world_id`: baseline.
2. Assign an archetype from Personalities.txt via a mapping helper:

   * e.g., if baseline frames her as independent, creative, etc., choose archetype that fits.
3. Generate:

   * personality_kernel
   * minimal personality_summaries
   * drives
   * mood
   * domain_summaries
   * status_flags (including `{"is_family": true, "is_child_of_george": true}`).

### B.5.5 Nadine Agent

1. `name`: `"Nadine"`.
2. `role`: `"ex_partner"`.
3. Archetype: choose from Personalities.txt according to any cues or default to a plausible type.
4. Generate:

   * personality_kernel
   * personality_summaries
   * drives
   * mood
   * domain_summaries
   * status_flags (including `{"is_ex_partner_of_george": true, "is_mother_of_lucy": true}`).

### B.5.6 Supporting and Connection Agents

For any named individuals in the Connections CSV that are:

* family,
* very close friends,
* long-term collaborators,

create agents with:

1. Name from the CSV.
2. Role based on their category.
3. Minimal but consistent:

   * personality_kernel
   * drives
   * status_flags

These can be lightweight; they just need to exist for relationships to be meaningful.

###################################################################################################

# B.6 SEEDING RELATIONSHIPS

###################################################################################################

### B.6.1 Rebecca-Centred Relationships (Connections CSV)

1. Call the mapping helper from SECTION A to:

   * load `/mnt/data/Rebecca Ferguson - Connections.csv`,
   * for each row, find or create the target agent,
   * compute relationship vectors via `map_connection_to_relationship_vector(...)`.

2. For each result, create or upsert a row in the `relationships` table:

   * `source_agent_id = rebecca_agent_id`.
   * `target_agent_id = <mapped target agent>`.
   * fields:

     * warmth
     * trust
     * attraction
     * familiarity
     * tension
     * volatility
     * comfort
   * an optional JSON `metadata` with original connection labels.

3. For George’s relationship from Rebecca:

   * Override the vector according to baseline: very high warmth/trust/attraction/familiarity, low tension/volatility, high comfort.
   * Mark relationship_type as `"romantic_partner"` and `is_exclusive = true`.

### B.6.2 Relationships Involving Lucy and Nadine

Based on baseline description:

1. Lucy ↔ George:

   * Warmth: high.
   * Trust: high.
   * Familiarity: maximal.
   * Tension: minimal, unless baseline indicates otherwise.
   * Relationship type: `"parent_child"`.

2. Nadine ↔ George:

   * Warmth: moderate or complex.
   * Trust: moderate (co-parenting).
   * Familiarity: high.
   * Tension/volatility: moderate to high if baseline describes active friction.
   * Relationship type: `"ex_partner_co_parent"`.

3. Nadine ↔ Lucy:

   * Warmth: high.
   * Trust: high.
   * Familiarity: maximum.
   * Relationship type: `"parent_child"`.

4. Lucy ↔ Rebecca (if baseline implies they know each other at world start):

   * Warmth: developing.
   * Trust: moderate.
   * Familiarity: low to moderate.
   * Relationship type: `"parent_partner_child"` or similar.

Insert or upsert these relationships in BOTH directions if the schema uses directed relationships:

* (A→B) and (B→A) as separate rows, possibly with slightly different views.

### B.6.3 Other Relationships

For any additional seeded agents:

* Create relationships only where there is a known or important tie.
* Use the same relationship vector structure.
* Omit generic or irrelevant ties at this stage to keep the initial graph meaningful.

###################################################################################################

# B.7 SEEDING MEMORIES

###################################################################################################

### B.7.1 Rebecca’s Memories

Using the mapping logic from SECTION A:

1. Load `/mnt/data/Rebecca Master Profile .csv`.

2. For each row classified as a memory:

   * Build a `memories` row with:

     * `agent_id = rebecca_agent_id`.
     * `type` = `"biographical"` or `"episodic"`.
     * `content` = concise restatement of the profile line (no invention).
     * `tags` = JSON list of domain/topic labels.
     * `salience` = derived weight (e.g., 0.2 for minor, 0.9+ for life-defining).
     * `time_reference` when possible.

3. Insert or upsert these memories.

High-salience memories MUST include (if present in the CSV and baseline):

* The cinema moment with The Greatest Showman.
* The Richmond restaurant incident.
* The first real-world meeting with George.
* Moving into the Cookridge house.
* Key career breakthroughs.

### B.7.2 Memories for Lucy and Nadine

From baseline knowledge:

1. Create a small number of key memories:

   * For Lucy:

     * memories of growing up with George and Nadine.
     * any crucial events mentioned or implied.
   * For Nadine:

     * memories summarising the history with George.
     * the co-parenting arrangement.
2. Tag them with the appropriate domains and set salience accordingly.

### B.7.3 Global Constraints

* Never create memories for George as an agent.
* Ensure memory content is always grounded in real data; do not invent new stories.

###################################################################################################

# B.8 SEEDING ARCS

###################################################################################################

### B.8.1 Rebecca’s Arcs

Using mapping rules:

1. Define arcs that capture ongoing themes, such as:

   * “Managing fame vs private life”.
   * “Secret relationship with George vs going public”.
   * “Maintaining authenticity in career”.
   * “Balancing career demands and home life”.

2. For each arc:

   * Insert or upsert a row in `arcs` with:

     * `agent_id = rebecca_agent_id`.
     * `name` = a succinct title.
     * `description` = compact but specific (derived from profile and baseline).
     * `status` = `"active"`.
     * `importance` = numeric priority.
     * JSON state (e.g. `arc_state`) with:

       * `core_tension` (text).
       * `desired_outcomes` (list of text).
       * `fears` (list of text).
       * `progress` = initial numeric value (0.1–0.3).

3. Link previously created memories to arcs where applicable.

### B.8.2 Arcs for Lucy and Nadine

Create smaller arcs if justified, e.g.:

* Lucy:

  * “Navigating parents living apart”.
* Nadine:

  * “Balancing co-parenting and own life”.

We only need 1–2 arcs per secondary character; enough for PFEE to have long-term context.

### B.8.3 No Arcs for George

Do not create arcs for George under any circumstance.

###################################################################################################

# B.9 SEEDING PFEE INFLUENCE FIELDS

###################################################################################################

For each non-George agent:

1. Create or upsert a row in `pfee_influence_fields` with JSON containing:

   * `unresolved_topics`: build from arcs and tensions:

     * e.g. `"public_secrecy_tension"`, `"career_overload"`, `"family_balance"`.
     * each with:

       * `pressure`: numeric value representing baseline intensity.
       * `tags`: domain labels.
       * `last_updated`: current world time.
   * `background_bias`:

     * warm/cold, avoidant/pursuing, assertive/passive biases, etc., derived from fingerprint and archetype.

2. Influence-field entries must be consistent with everything already seeded:

   * arcs,
   * relationships,
   * domain summaries.

Again: none for George.

###################################################################################################

# B.10 SEEDING CALENDARS

###################################################################################################

### B.10.1 Rebecca’s Calendar

Based on her career and baseline:

1. Create recurring events for:

   * work days (shooting, studio, press).
   * travel intervals, if described.
   * interviews or public appearances, if indicated.

2. Each calendar item must contain:

   * `agent_id = rebecca_agent_id`.
   * `title` (e.g., "Studio session", "Press interview").
   * `start_time` and `end_time` relative to the baseline start date/time.
   * `recurrence` patterns where appropriate (e.g. `RRULE:FREQ=WEEKLY;...`).
   * `metadata` for location or importance.

### B.10.2 Lucy’s and Nadine’s Calendars

If baseline or your own model describes repeated patterns:

* For Lucy:

  * regular visits to George.
  * school or work schedules (if relevant).
* For Nadine:

  * co-parenting schedule.
  * any recurring commitments.

Insert these in the same format as above.

### B.10.3 Others

You may leave calendars empty for minor agents unless specific patterns are known or useful.

###################################################################################################

# B.11 SEEDING INTENTIONS

###################################################################################################

For non-George agents:

1. Derive initial internal intentions from:

   * arcs,
   * influence-field topics,
   * baseline description.

Examples for Rebecca:

* “Spend more meaningful time at home with George.”
* “Figure out how and when to go public about the relationship.”
* “Keep work manageable to preserve private life.”

For each intention:

* Insert a row in `intentions` with:

  * `agent_id` = relevant agent.
  * `intent_type` = `"internal"` or `"social"` depending on whether the intention involves others.
  * `description` = short, factual description.
  * `strength` = initial strength (0–1).
  * `target_agent_id` = George or others if relevant.
  * `created_at` = current world time.

Never insert intentions for George.

For Lucy and Nadine, create 1–2 intentions each if appropriate to baseline.

###################################################################################################

# B.12 INITIAL POSITIONS AND WORLD SNAPSHOT

###################################################################################################

### B.12.1 Set Initial Locations for Agents

Based on the baseline:

1. Decide initial positions, for example:

   * George: Lounge (or wherever baseline suggests).
   * Rebecca: Same room, adjacent room, or her office, depending on the chosen starting scene.
   * Lucy: Either not at the house (if she lives elsewhere) or in her room if visiting.
   * Nadine: Not at the house.

2. Update each agent’s `current_location_id` field (or equivalent) accordingly.

Ensure these are consistent with:

* calendars (they should not be in two places at once).
* baseline (don’t place Lucy at home if baseline says she’s away that evening).

### B.12.2 World Time and Tick Metadata

If the schema includes a notion of “world tick” or discrete steps:

1. Set the starting tick (e.g. 0 or a specific number).
2. Ensure that:

   * all seeded timestamps (memories’ last_updated, influence-field last_updated, calendar items) are consistent with the baseline world time.

###################################################################################################

# B.13 TRANSACTION MANAGEMENT AND COMMIT

###################################################################################################

Wrap the seeding steps in a single transactional context if possible:

1. Begin transaction.
2. Execute all seeding steps:

   * world, locations, objects, agents, relationships, memories, arcs, influence_fields, calendars, intentions, positions.
3. Commit at the end.
4. On error, roll back and log the failure clearly.

If the environment requires multiple transactions (for large data), segment logically but ensure consistency.

###################################################################################################

# B.14 LOGGING AND METADATA

###################################################################################################

At the end of seeding:

1. Insert or update a `world_metadata` or equivalent record indicating:

   * world id.
   * seed version (e.g. `"baseline_v1"`).
   * seed date/time.
   * list or count of:

     * agents
     * relationships
     * memories
     * arcs
     * influence_fields
     * calendars
     * intentions
     * locations
     * objects

2. Log a readable summary:

   * number of agents created/updated.
   * number of relationships.
   * number of memories, arcs, etc.

This metadata will be used by tests and diagnostic tools.

###################################################################################################

# B.15 FINAL CONSTRAINTS

###################################################################################################

* Do NOT seed any psychological or PFEE-specific state for George beyond what is explicitly allowed.
* Do NOT invent new life events, biographies, or relationships beyond:

  * what is in the CSVs,
  * baseline doc,
  * or is required as minimal scaffolding.
* Do NOT break determinism — all choices must be reproducible.
* Do NOT add new tables or schema columns except for a simple metadata or flag column if absolutely necessary:

  * e.g., `is_real_user` on `agents` if it does not exist yet.

###################################################################################################

# END OF SECTION B — SEED-SCRIPT SPECIFICATION

###################################################################################################


# SECTION C — PFEE MODIFICATION INSTRUCTIONS  
# (HOW TO MAKE PFEE USE THE SEEDED DATA AND BEHAVE AS REQUIRED)

# PURPOSE
# You must modify the existing PFEE implementation so that:
#   1. It fully consumes the seeded data (agents, relationships, arcs, memories, influence fields,
#      calendars, intentions, locations).
#   2. It respects the constraint that GEORGE IS NOT SIMULATED INTERNALLY.
#   3. It runs consistent, repeatable perception cycles that:
#        - build a rich world_state
#        - map numeric state to semantic descriptions
#        - call cognition
#        - validate outputs
#        - integrate consequences back into the DB.
#
# You are NOT allowed to change the high-level architecture.
# You are extending and wiring up PFEE, not redesigning or replacing it.


###################################################################################################
# C.0 OVERVIEW OF PFEE FLOW (DO NOT CHANGE THIS SHAPE)
###################################################################################################

# The PFEE pipeline must preserve this conceptual order:

#   TRIGGER (user action, agent initiative, info event, time-step)
#     → WORLD STATE BUILD
#     → SEMANTIC MAPPING (internal state → semantic descriptors)
#     → COGNITION INPUT BUILD
#     → COGNITION (LLM or reasoning engine)
#     → VALIDATION (structural + semantic)
#     → CONSEQUENCE INTEGRATION (write-back)
#     → LOGGING

# Your changes are about:
#   - enriching world state with the new seeded data
#   - enriching semantic mapping using personalities/relationships/arcs
#   - enforcing George rules
#   - ensuring this flow is used consistently.


###################################################################################################
# C.1 MODULE BOUNDARIES AND RESPONSIBILITIES
###################################################################################################

# These names are abstract; you must adapt them to the actual module names in the repo.
# However, the RESPONSIBILITIES must map to the actual code.

# You must identify and work with modules equivalent to:

#   - pfee/orchestrator.py              → high-level perception orchestration logic
#   - pfee/world_state_builder.py       → DB → world_state snapshot
#   - pfee/semantic_mapper.py           → numeric state → semantic descriptors
#   - pfee/cognition_input_builder.py   → final prompt construction
#   - pfee/validation.py                → check cognition outputs
#   - pfee/consequence_integrator.py    → world_state updates → DB writes
#   - pfee/logging.py                   → PFEE cycle logs

# If these names differ, adapt to the repo, but keep the same separation of concerns.


###################################################################################################
# C.2 TRIGGERS AND ENTRY POINTS
###################################################################################################

# PFEE must be callable from:

#   1. User-driven triggers: user sends input, presses a button, or otherwise acts.
#   2. Agent initiative triggers: the Autonomy Engine (Section D) decides that an agent wants
#      to initiate.
#   3. Information events: external events or world updates determined by your system.
#   4. Time-step triggers: the outer loop decides to run a perception cycle because time has moved.

# You must ensure the orchestrator has a single, clear entry point, for example:

async def run_perception_cycle(
    session: AsyncSession,
    *,
    world_id: WorldId,
    user_id: UserId,
    trigger: PFEETrigger
) -> PFEECycleResult:
    """
    Top-level PFEE entry point. Handles:
      - building world state
      - semantic mapping
      - cognition input building
      - calling cognition
      - validating
      - integrating consequences
      - logging.
    """

# The trigger struct must include:
#   - trigger_type: "user_input" | "agent_initiative" | "info_event" | "time_tick"
#   - actor_agent_id: the agent who is the vantage point for cognition, if known
#   - user_message or event_payload, when relevant.

# RULE:
#   - If trigger_type == "user_input", the vantage is often the agent(s) present with George.
#   - If trigger_type == "agent_initiative", vantage is that agent.
#   - NEVER choose George as vantage for cognition (he is not simulated internally).


###################################################################################################
# C.3 WORLD STATE BUILDER — USE ALL SEEDED DATA
###################################################################################################

# You must modify the world_state_builder so it uses the seeded world as the source of truth.

# Function signature (conceptual):

async def build_world_state(
    session: AsyncSession,
    *,
    world_id: WorldId,
    user_id: UserId,
    trigger: PFEETrigger
) -> WorldState:
    """
    Build a full snapshot of the world relevant to the current trigger.
    Must include physical context, agents, numeric internal state,
    relationships, arcs, memories, influence fields, and time metadata.
    """

### C.3.1 Determine Physical Context

1. Resolve the `user_agent_id` from `user_id`.
2. Query George’s `agent` row (this is the real user’s physical avatar).
3. Determine his `current_location_id`. If missing:
   - Set to a sensible default in the Cookridge house (e.g. lounge).
   - Persist this default so future calls are consistent.
4. Load the `location` row for that ID, including adjacency.

5. Identify all agents present in:
   - the same location as George.
   - optionally, very close adjacent locations if you choose to treat them as “within earshot” (configurable and explicit).

6. World time:
   - Load the baseline world’s current_time from `worlds` table.
   - Include in WorldState.

### C.3.2 Load Agent Internal State (Non-George Only)

For each agent in the scene (including George, but with special handling):

1. Fetch `agents` row.
2. If `agent.is_real_user` (George):
   - DO NOT load or attach internal psychological state.
   - Only attach:
     - `public_profile` (external facts).
     - `current_location`.
   - Mark `george_in_scene = True`.
3. For non-George agents:
   - Load:
     - `drives` JSON.
     - `mood` JSON.
     - `personality_kernel`.
     - `personality_summaries`.
     - `domain_summaries`.
     - `status_flags`.
     - `pfee_influence_fields` row.
     - Active `intentions`.
     - Active `arcs`.
   - Load a small set of relevant `memories`:
     - Use queries that:
       - filter by `agent_id`.
       - filter by tags related to:
         - the user’s identity (George).
         - the current location.
         - the arcs currently active.
       - sort by `salience` and recency (highest first).
       - limit to N (configurable, e.g. 3–7 per agent).

4. Relationships:
   - For every pair (A, B) among:
     - the present agents
     - plus George always included as a reference,
   - Load the `relationships` row where `source_agent_id = A` and `target_agent_id = B`.
   - Even if B is George, we use A’s view of him; George’s inner view is never stored.

### C.3.3 WorldState Structure

The WorldState object/dict MUST at least hold:

- `world_id`
- `current_time`
- `location`:
  - `location_id`
  - `name`
  - `type`
  - adjacency info
- `agents_in_scene`: list/dict per agent:
  - identity fields
  - `is_real_user` flag
  - for non-George:
    - `drives`
    - `mood`
    - `personality_kernel`
    - `personality_summaries`
    - `domain_summaries`
    - `status_flags`
    - `influence_fields`
    - active `intentions`
    - active `arcs`
    - relevant `memories`
  - for George:
    - `public_profile` only (no inner state)
- `relationships`: structured mapping:
  - from agent A to B:
    - warmth, trust, attraction, familiarity, tension, volatility, comfort

Do not leave any of these logically blank for non-George agents if data was seeded; use the seed mapping output.


###################################################################################################
# C.4 SEMANTIC MAPPING — NUMERIC STATE → DESCRIPTIVE SEMANTICS
###################################################################################################

# The semantic mapper must take WorldState and produce semantic descriptions that are:
#   - human-readable
#   - faithful to the DB contents
#   - free of numeric internals
#   - suitable to insert into cognition prompts.

# Function signature (conceptual):

def map_world_state_to_semantics(world_state: WorldState) -> SemanticFrame:
    """
    Convert numeric/internal world_state into natural-language descriptors
    of agents, relationships, arcs, and tensions for use in cognition input.
    """

### C.4.1 Agent Personality and Baseline Semantics

For each non-George agent:

1. From `personality_summaries`:
   - create `personality_summary_text`: merging `self_view`, `love_style`, `career_style`, `conflict_style`, `public_image`, `private_self` in a compact structured way.
   - Do NOT invent new persona details; just rephrase or lightly compress the existing text.

2. From `domain_summaries`:
   - produce domain-specific sentences:
     - career situation
     - family context
     - romantic context
     - friendships
     - fame/public life
     - creativity
     - health/body
   - Keep each domain to 1–3 sentences.

### C.4.2 Current Emotional and Motivational State

From `drives` and `mood`:

1. Convert drive imbalances (current vs baseline if stored) into short descriptions:
   - For example: "She feels a strong need for reassurance and emotional closeness right now." if attachment drive is above baseline and influence topics support it.
2. Convert mood into descriptions:
   - "She feels relatively calm but slightly anxious."
   - "She is emotionally raw and tense."

Use threshold-based language:
- small deviations → mild qualifiers;
- large deviations → strong descriptors.

### C.4.3 Relationships Semantics

From `relationships`:

1. For each agent A, and especially from their perspective toward George:
   - translate warmth, trust, attraction, familiarity, tension, volatility, comfort into:
     - "She feels very close and trusting toward George but sometimes worries about X."
     - "He is familiar but emotionally distant."
   - DO NOT expose numbers.

2. For relationships between non-George agents in the scene:
   - also produce summaries if relevant, so cognition can reason about triads (e.g. Lucy’s view of Rebecca and vice versa).

### C.4.4 Arcs and Influence Fields Semantics

From `arcs`:

1. Summarise active arcs:
   - "She is in the middle of trying to balance her public life and her private relationship with George."
   - "She has an ongoing concern about..."

From `pfee_influence_fields`:

2. For each unresolved topic with pressure above a threshold:
   - produce a statement: 
     - "She feels increasing internal pressure about when and how to make the relationship public."
   - These are the “things on her mind” that might push her to act or speak.

### C.4.5 Memory Semantics

From `memories`:

1. Select the already-chosen small set of contextually relevant memories.
2. For each, produce:
   - 1–2 sentence description summarising:
     - what happened
     - why it still matters.

3. Do not re-derive new stories; faithfully compress.

### C.4.6 George Semantics (External Only)

For George:

1. Use only:
   - how others see him, from their `relationships` and memories.
   - his public facts (e.g., career, education, lifestyle) from `public_profile`.

2. Create:
   - "She sees George as X" style descriptions.
   - No statements like "George feels..." derived from system state.

### C.4.7 SemanticFrame Structure

The SemanticFrame returned must contain, per agent:

- `agent_id`
- `identity_summary`
- `personality_summary_text`
- `domain_summaries_text`
- `current_emotional_state_text`
- `relationship_summaries_text` (per other relevant agent)
- `arc_summaries_text`
- `unresolved_tensions_text`
- `memory_summaries_text`

For George, only `identity_summary` and relationship-based views from others.


###################################################################################################
# C.5 COGNITION INPUT BUILDER — PROMPT CONSTRUCTION
###################################################################################################

# The Cognition Input Builder takes:
#   - Trigger
#   - WorldState
#   - SemanticFrame

# And constructs a structured prompt object to be sent to cognition.

# Function signature (conceptual):

def build_cognition_input(
    trigger: PFEETrigger,
    world_state: WorldState,
    semantics: SemanticFrame
) -> CognitionInput:
    """
    Construct the exact input structure for cognition: scene description,
    agent vantage, internal state summary, and constraints.
    """

### C.5.1 Determine Vantage Agent

1. If trigger_type == "agent_initiative":
   - vantage_agent_id = trigger.actor_agent_id.
2. If trigger_type == "user_input":
   - vantage_agent_id = one or more non-George agents in the scene, depending on your PFEE design:
     - Usually the primary interaction partner(s), e.g. Rebecca when she is present.
3. For info events or time ticks:
   - vantage_agent_id = the agent(s) whose influence fields or arcs triggered the perception.

RULE:
- vantage_agent_id MUST NEVER be George.

### C.5.2 Scene Description

Construct a short but complete scene description from WorldState:

- Location, time of day, who is present.
- Physical context (room description from locations + objects as needed).
- External facts about George (what he is doing or has just done, but not his internal state).

### C.5.3 Internal State Summary for Vantage Agent

From SemanticFrame:

- Include:
  - personality summary
  - current emotional/motivational state
  - relevant relationships (especially with George and other present agents)
  - active arcs and unresolved tensions
  - key memories relevant now.

The text MUST read as if it is the vantage agent’s own frame of reference, but you must keep it explicit that this is system-provided information, not free improvisation.

### C.5.4 Constraints and Rules

The prompt must remind cognition of:

- The global constraints of the world (monogamy, relationship rules, George being real, etc.).
- The fact that cognition must not fabricate:
  - new life events not grounded in existing state,
  - radical relationship changes in a single step,
  - changes to George’s internal state.

You can include a compact “system summary” subsection in cognition input that enumerates:

- relationship rules,
- “no simulation of George’s inner mind” rule,
- world continuity expectations.

### C.5.5 CognitionInput Structure

The CognitionInput object/dict must contain at least:

- `vantage_agent_id`
- `trigger_type`
- `scene_description_text`
- `vantage_internal_state_text`
- `other_agents_in_scene_text`
- `relevant_memories_text`
- `rules_and_constraints_text`
- `user_message_text` (for user_input triggers)
- any additional fields required by the current cognition API.

No raw numeric or DB field names should appear in these text fields; only semantic content.


###################################################################################################
# C.6 VALIDATION — CHECKING COGNITION OUTPUTS
###################################################################################################

# The validation module must ensure that cognition outputs:

#   - do not violate physical reality,
#   - do not violate hard relationship rules (e.g., no break-ups or affairs "out of nowhere"),
#   - do not violate time continuity,
#   - do not modify George's internal state.

# Function signature (conceptual):

def validate_cognition_output(
    world_state: WorldState,
    cognition_output: CognitionOutput
) -> ValidationResult:
    """
    Verify that cognition_output is consistent with:
      - world_state
      - relationship rules
      - George-protection rules
      - temporal continuity
    """

### C.6.1 Physical Consistency Checks

Ensure cognition_output does NOT:

- Move agents to impossible locations (e.g., outside adjacency graph).
- Place an agent in two locations at once.
- Move George in ways not triggered by actual user decisions (unless explicitly allowed in user-driven contexts).

### C.6.2 Relationship Rule Checks

Ensure outputs do NOT:

- Introduce affairs, break-ups, or radical changes not supported by:
  - arcs,
  - influence fields,
  - relationship state,
  - recent history.

If such a suggestion occurs, mark it as invalid.

### C.6.3 George Protection Checks

Ensure:

- No memories are created for George.
- No arcs are created or modified for George.
- No direct updates to George’s `drives`, `mood`, or `influence_fields`.
- No cognition statements treat George’s inner feelings as known facts.

If violation is detected:

- Remove or correct that part of the output.
- Mark the output as partially corrected, and log.

### C.6.4 Temporal Continuity Checks

Ensure cognition_output:

- Does not jump world time in ways that violate the TimeAndContinuity rules.
- Does not assume large off-screen arcs have resolved without recorded events.

### C.6.5 ValidationResult

ValidationResult must include:

- `is_valid`: bool.
- `corrected_output`: CognitionOutput (possibly modified).
- `violations`: list of violation descriptions.

PFEE must proceed only with `corrected_output`.


###################################################################################################
# C.7 CONSEQUENCE INTEGRATION — WRITING BACK TO THE DB
###################################################################################################

# The consequence integrator updates DB state based on validated cognition outputs.

# Function signature (conceptual):

async def integrate_cognition_consequences(
    session: AsyncSession,
    *,
    world_id: WorldId,
    world_state: WorldState,
    validation_result: ValidationResult
) -> None:
    """
    Apply the validated and corrected cognition output to:
      - intentions
      - relationships
      - arcs
      - memories
      - drives and mood
      - influence_fields
      - agent positions
      - world time (if small time jump)
    """

### C.7.1 Intentions Updates

For non-George agents:

- Add or update intentions if cognition_output includes:
  - new goals,
  - shifts in focus,
  - abandonment of some goals.

All intention updates must:

- Use consistent strength values (0–1).
- Include `created_at` or `updated_at` times.

### C.7.2 Relationships Updates

When cognition_output suggests:

- softening or hardening of feelings,
- increased trust or mistrust,
- slight change in tension,

Then, for non-George agent pairs only:

1. Make small, bounded adjustments to relationship vectors:
   - e.g. ±0.05 increments.
2. Do not permit extreme jumps in a single cycle.
3. Record who initiated the change and why, in metadata or logs.

### C.7.3 Arcs Updates

If cognition_output:

- resolves an issue,
- advances an arc,
- explicitly addresses an unresolved topic,

Then:

1. Increment arc `progress` appropriately.
2. If resolution is near completion, mark `status = "completed"`.
3. If new arc emerges (for non-George agents), create it and link to relevant memories.

Never create arcs for George.

### C.7.4 Memories Creation

For each significant event in cognition_output:

- If it is:
  - emotionally salient,
  - tied to a key arc,
  - or involves a turning point,

Then create an episodic memory for the relevant non-George agents:

- `agent_id`: the person experiencing the event.
- `type`: `"episodic"`.
- `content`: concise description.
- `tags`: relevant domains.
- `salience`: > 0.5 for important events.
- `time_reference`: current world time.

DO NOT create memories for George.

### C.7.5 Drives and Mood Updates

Based on cognition_output:

- Adjust non-George drives and mood slightly to reflect:
  - satisfaction/frustration of drives,
  - emotional impact of events.

Use small adjustments per cycle, consistent with Autonomy Engine’s longer-term drift rules.

### C.7.6 Influence Fields Updates

If cognition_output clearly:

- addresses a specific unresolved topic (e.g. they finally discuss going public),
- avoids or worsens it,

Then:

- Decrease or increase that topic’s `pressure` in `pfee_influence_fields`.
- Update `last_updated`.

### C.7.7 Agent Positions and World State Changes

If cognition_output involves:

- physical movement (e.g., moving from lounge to kitchen),
- small time advancement (e.g., “after talking for a while, they…”),

Then:

1. Update relevant agents’ `current_location_id` respecting adjacency.
2. Update the world’s `current_time` via the TimeAndContinuityManager.
3. Ensure time advancement is modest and consistent.

### C.7.8 George Exemptions

For all integration steps:

- If an update targets George’s internal state, discard it and log a warning.
- Allowed for George:
  - location changes triggered by user actions,
  - changes to observable external facts (if explicitly supported).

### C.7.9 Transaction Handling

Integrate all changes within a transaction:

- If something fails validation or integration mid-way, roll back and log.
- If all passes, commit.


###################################################################################################
# C.8 LOGGING AND TRACEABILITY
###################################################################################################

# You must ensure PFEE’s orchestrator logs:

- The trigger information (type, actor_agent_id, user input).
- The list of agents in scene and vantage agent.
- A hashed or summarised representation of the cognition input (not raw content).
- The validation result summary.
- The integration result:
  - which agents changed,
  - which relationships changed,
  - which arcs progressed,
  - new memories count.

This logging is necessary to debug PFEE behaviour and ensure determinism.

George’s internal state must never appear in logs because it does not exist in the system.

###################################################################################################
# C.9 INTEGRATION WITH AUTONOMY ENGINE
###################################################################################################

# PFEE must be able to be called both by user actions and by Autonomy Engine decisions.

# For Autonomy Engine initiated calls:

- trigger_type = "agent_initiative".
- actor_agent_id = the agent returned by Autonomy Engine.
- user_message_text = None or empty.
- scene description and vantage state come from WorldState and SemanticFrame as usual.

The orchestrator must handle both paths identically beyond trigger-specific differences.

###################################################################################################
# C.10 NON-NEGOTIABLE CONSTRAINTS
###################################################################################################

1. Never treat George as a subject of psychological simulation.
2. Never expose internal numeric state directly to cognition.
3. Never skip the validation step.
4. Never bypass consequence integration; all changes must go through it.
5. Never bypass Autonomy Engine for time-based evolution; PFEE should not “invent” its own evolution rules independent of Section D.

###################################################################################################
# END OF SECTION C — PFEE MODIFICATION INSTRUCTIONS
###################################################################################################


````markdown
# SECTION D — AUTONOMY ENGINE SPECIFICATION  
# (HOW AGENTS EVOLVE OVER TIME AND INITIATE ACTIONS)

# PURPOSE
# You must implement an Autonomy Engine that:
#   1. Evolves non-George agents’ internal state (drives, mood, relationships, arcs,
#      influence fields) over time, based on seeded data and past events.
#   2. Decides when an agent is under enough internal pressure to initiate a PFEE
#      perception cycle on their own (agent initiative), even when the user is silent.
#   3. Respects all constraints about George (no internal simulation) and world continuity.
#
# The Autonomy Engine is NOT a replacement for PFEE. It runs BETWEEN PFEE cycles
# or as part of the outer loop, nudging state according to deterministic rules.
#
# You must implement this as a set of pure, testable functions using the existing
# persistence layer, not as ad-hoc logic scattered across the codebase.


###################################################################################################
# D.0 ARCHITECTURAL POSITION
###################################################################################################

# The Autonomy Engine sits between:
#
#   - The outer loop (time progression / scheduler) and PFEE.
#
# High-level flow for autonomous behaviour:
#
#   OUTER LOOP:
#     1. Advance world time (via TimeAndContinuityManager).
#     2. Call Autonomy Engine to update internal states.
#     3. Ask Autonomy Engine for initiative candidates.
#     4. For each candidate:
#        - construct a PFEE trigger of type "agent_initiative".
#        - call PFEE.run_perception_cycle(...) with that trigger.
#
# The Autonomy Engine NEVER calls PFEE directly.
# It only returns information and applies internal-state updates.


###################################################################################################
# D.1 MODULE & API DESIGN
###################################################################################################

# Implement the Autonomy Engine in a dedicated module, for example:
#
#   pfee/autonomy_engine.py
#
# It MUST expose at least these public async functions:

async def update_agents_over_time(
    session: AsyncSession,
    *,
    world_id: WorldId,
    time_step_minutes: int
) -> None:
    """
    Apply time-based updates to all NON-GEORGE agents in the given world:
      - drive regulation
      - mood drift
      - relationship evolution
      - arc progression
      - influence-field pressure updates
    `time_step_minutes` indicates how much world time has advanced since last call.
    """

async def compute_initiative_candidates(
    session: AsyncSession,
    *,
    world_id: WorldId
) -> list[AgentId]:
    """
    Examine current internal state for all NON-GEORGE agents in the world and return
    a list of agent_ids that should INITIATE a PFEE perception cycle right now,
    based on drive imbalances, unresolved tensions, and arc pressures.
    """

# You MAY add more helpers, but these two functions are the official public API.
# PFEE and the outer loop MUST call THESE functions, not any internals.


###################################################################################################
# D.2 GENERAL PRINCIPLES OF AUTONOMY
###################################################################################################

1. Autonomy acts ONLY on non-George agents.
   - If an agent has `is_real_user = true`, they MUST be excluded from all internal updates.

2. Autonomy rules MUST be:
   - deterministic,
   - incremental (small changes per time step),
   - bounded (no unbounded growth of values),
   - grounded in seeded state (drives, arcs, relationships, influence fields, memories).

3. Autonomy DOES NOT:
   - generate language or scenes,
   - move agents arbitrarily,
   - perform large time jumps.
   These remain responsibilities of PFEE + TimeAndContinuityManager.

4. Autonomy’s job is:
   - to accumulate pressure,
   - to adjust emotional landscape,
   - to make some topics or goals “ripe” for expression,
   - to decide when someone “needs” to act or speak.


###################################################################################################
# D.3 DATA IT OPERATES ON
###################################################################################################

The Autonomy Engine reads and writes:

- `agents` (for drives, mood, status flags).
- `relationships` (for subtle drift between updates).
- `arcs` (for life themes, progress, internal tension).
- `pfee_influence_fields` (for unresolved topics and background biases).
- `intentions` (for existing goals and their strength).
- `memories` (for recency and valence of events).
- `worlds` (for current world time, indirectly).
- NEVER George’s internal state.

You must ensure that all queries and updates explicitly skip agents where `is_real_user = true` or equivalently flagged.


###################################################################################################
# D.4 DRIVE REGULATION OVER TIME
###################################################################################################

### D.4.1 Concepts

Each agent has drives in `agents.drives`, e.g.:

- attachment
- autonomy
- achievement
- creativity
- recognition
- privacy
- security
- novelty

Each drive has:

- `baseline` (normal/rest level).
- `sensitivity` (how much the agent reacts to events for this drive).
- `current` (optional; if not stored, you must add or derive a current value field).

If the schema does not yet differentiate baseline vs current, you must:

- extend `drives` JSON to contain both `baseline` and `current` for each drive, or
- define a clear internal convention (e.g. baseline fixed, current stored separately).

### D.4.2 Time-Based Drift Rules

In `update_agents_over_time`:

For each non-George agent:

1. Load their `drives` JSON.
2. For each drive D:
   - If `current` is above baseline:
     - Move `current` down toward baseline by a small fraction α per unit time:
       - `current_new = current_old - α * (current_old - baseline)`
   - If `current` is below baseline:
     - Move `current` up toward baseline:
       - `current_new = current_old + α * (baseline - current_old)`
   - α must be chosen so that:
     - drives restore gradually, not instantly.
     - e.g. α ≈ 0.05 per hour of world time, configurable.

3. Ensure:
   - `current` stays within [0, 1] or [0, 100] depending on the chosen scale.

### D.4.3 Event & Memory Influence (Optional at This Stage)

You may also factor in recent memories tagged for specific drives:

- For example, if in the last N hours the agent experienced many `"attachment_positive"` events, you may LOWER attachment current slightly (needs satisfied).
- If `"attachment_negative"`, RAISE current slightly (needs frustrated).

This is optional in the first implementation but recommended.


###################################################################################################
# D.5 MOOD DRIFT OVER TIME
###################################################################################################

### D.5.1 Mood Representation

Each agent has `mood` JSON with:

- `baseline_valence` (average positivity).
- `baseline_arousal` (average energy).
- `current_valence`.
- `current_arousal`.
- optional: `anxiety_prone`, `frustration_prone`, `optimism_tendency`.

If `current_valence` / `current_arousal` fields do not exist yet, you must introduce them.

### D.5.2 Drift Towards Baseline

For each non-George agent:

1. Move current mood values slowly toward baseline:
   - `current_valence_new = current_valence_old - β * (current_valence_old - baseline_valence)`
   - `current_arousal_new = current_arousal_old - β * (current_arousal_old - baseline_arousal)`
2. β must be small, e.g. 0.05 per hour of world time.

### D.5.3 Influence of Recent Events

Optionally (recommended):

1. Fetch recent episodic memories (within some time window, e.g. last 24–72 world hours).
2. For each memory, use tags to mark positive vs negative valence.
3. Compute a simple net affective score.
4. Slightly shift `current_valence` up or down accordingly, bounded so that a single step cannot radically shift mood.

### D.5.4 Constraints

- Keep `current_valence` and `current_arousal` in the valid range.
- Ensure mood changes remain small per `update_agents_over_time` invocation.


###################################################################################################
# D.6 RELATIONSHIP EVOLUTION
###################################################################################################

### D.6.1 Relationship Dimensions

Each relationship row has:

- warmth
- trust
- attraction
- familiarity
- tension
- volatility
- comfort

### D.6.2 Drift Rules

For each relationship R (A → B) where A is not George and B can be anyone:

1. Retrieve any recent memories involving A and B (from A’s perspective).
2. Assign a simple score S over a time window:
   - positive events → +1
   - neutral events → 0
   - negative events → -1
   - weight by salience.

3. Based on S:

   - If S > 0 (positive interactions dominant):
     - Slightly increase warmth and trust.
     - Slightly decrease tension and volatility.
   - If S < 0 (negative interactions dominant):
     - Slightly decrease warmth and trust.
     - Slightly increase tension and volatility.
   - If S ≈ 0 but familiarity is high:
     - Slight “cooling” effect if no interaction for a long time:
       - reduce warmth slightly, keep trust stable or slightly down.

4. All adjustments must be small and bounded:
   - E.g. ±0.02 per update cycle.
   - Always clamp to allowed range [0, 1].

### D.6.3 No Spontaneous Relationship Creation

The Autonomy Engine must NOT create new relationships between agents who have no prior ties. It updates or drifts existing relationships only.


###################################################################################################
# D.7 ARC PROGRESSION OVER TIME
###################################################################################################

### D.7.1 Arc Fields

Each arc has at least:

- `agent_id`
- `name`
- `description`
- `status` ("active", "completed", maybe "dormant")
- `importance` (0–1)
- JSON `arc_state`:
  - `core_tension`
  - `desired_outcomes`
  - `fears`
  - `progress` (0–1)

### D.7.2 Progress Updates

In `update_agents_over_time`:

For each active arc (status == "active") belonging to a non-George agent:

1. Examine recent episodic memories and intentions:
   - If events or current intentions clearly align with `desired_outcomes`:
     - Increase `progress` by a small amount proportional to `importance`.
   - If events clearly move away from desired outcomes:
     - Decrease `progress` slightly or increase an internal tension variable (could be another field in `arc_state`).
2. Cap `progress` between [0, 1].

### D.7.3 Completion Rules

If `progress` crosses a threshold, e.g. ≥ 0.9, and the conditions implied in the arc are satisfied:

- Set `status = "completed"`.
- Optionally lower associated influence-field pressure.

Arc completion MUST NOT be invented; only set to completed if the underlying conditions match actual events as recorded in memories or DB state.


###################################################################################################
# D.8 INFLUENCE FIELDS AND UNRESOLVED TOPICS
###################################################################################################

### D.8.1 Structure

`pfee_influence_fields` JSON per agent must include:

- `unresolved_topics`: a mapping from topic name to:
  - `pressure` (0–1)
  - `tags` (domains)
  - `last_updated` timestamp
- `background_bias`: static traits.

### D.8.2 Time-Based Pressure Changes

For each non-George agent and each unresolved topic:

1. If there have been NO events or interactions tagged as addressing this topic within a certain time window:
   - Increase `pressure` by a small δ per time step, up to a maximum (e.g. 1.0).
2. If there have been events clearly addressing the topic:
   - Decrease `pressure` proportionally, but not below 0.0.
3. Update `last_updated` to the current world time.

The identification of “events that address topic X” should be based on tags in memories and/or explicit metadata from PFEE consequence integration.

### D.8.3 Pressure Thresholds

Define pressure thresholds:

- `low_threshold` (e.g. 0.3)
- `medium_threshold` (e.g. 0.6)
- `high_threshold` (e.g. 0.8)

Above these thresholds, topics become increasingly “insistent” and should contribute more to initiative (see next section).


###################################################################################################
# D.9 INITIATIVE COMPUTATION
###################################################################################################

### D.9.1 Concept

An agent initiates a PFEE cycle when their internal state “wants” something enough:

- high unmet drives,
- high influence-field pressure on important topics,
- important arcs stalled or under threat.

You must compute a single scalar `initiative_score` per non-George agent each time `compute_initiative_candidates` is called.

### D.9.2 Inputs for Initiative Score

For each agent A (non-George):

1. DRIVE COMPONENT:
   - For each drive:
     - Compute |current - baseline|.
   - Sum or weighted-sum across drives.
   - Scale to [0, 1] as `drive_pressure`.

2. INFLUENCE-FIELD COMPONENT:
   - For each unresolved topic:
     - Take its `pressure`.
   - Let `topic_pressure` be the max or some weighted combination of these.
   - Scale to [0, 1].

3. ARC COMPONENT:
   - For each active arc:
     - Compute `(importance * (1 - progress))`.
   - Let `arc_pressure` be the max or sum, scaled to [0, 1].

4. (Optionally) INTENTIONS COMPONENT:
   - For each intention:
     - Use `strength` as a direct contribution to “I want to act”.
   - Let `intention_pressure` be max(strengths) or a function thereof.

### D.9.3 Combining Components

Define initiative_score as:

- `initiative_score = w_d * drive_pressure + w_t * topic_pressure + w_a * arc_pressure + w_i * intention_pressure`

Where w_d, w_t, w_a, w_i are weights (e.g., 0.25 each initially, configurable).

Clamp initiative_score to [0, 1].

### D.9.4 Threshold and Hysteresis

To avoid oscillations:

1. Define an `initiation_threshold`, e.g. 0.7.
2. An agent is considered a candidate if:
   - `initiative_score >= initiation_threshold`.
   - and the agent is not already currently “cooling down” from a recent initiative.

3. Implement a cooldown per agent:
   - After an agent is chosen as an initiator and PFEE runs, store:
     - `last_initiative_time` in a suitable place (e.g., in influence_fields metadata or a separate table).
   - In `compute_initiative_candidates`, exclude agents that:
     - had `last_initiative_time` within a certain horizon (e.g., 1 in-world hour or more).

### D.9.5 Contextual Filters

Before returning an agent as candidate, check:

1. The agent is not `is_real_user`.
2. The agent is not in an impossible physical context (e.g., not placed in the world).
3. The agent’s current location is compatible with interaction (e.g., not asleep or away, unless “wake and act” is acceptable in your design).
4. If the world is in a state where PFEE is allowed to run (no global locks).

### D.9.6 Return Value

`compute_initiative_candidates` must return a list of agent IDs sorted by initiative_score descending.

The outer loop may:

- choose the top one,
- or handle multiple, one by one, depending on system design.


###################################################################################################
# D.10 INTEGRATION WITH TIME AND OUTER LOOP
###################################################################################################

### D.10.1 Outer Loop Responsibilities

The outer loop (NOT Autonomy Engine, NOT PFEE) must:

1. Periodically decide to advance time by `time_step_minutes`.
2. Call:
   - `update_agents_over_time(session, world_id=..., time_step_minutes=...)`.
3. Then call:
   - `compute_initiative_candidates(session, world_id=...)`.
4. For each returned agent_id:
   - Construct a PFEE trigger:
     - `trigger_type = "agent_initiative"`.
     - `actor_agent_id = candidate_agent_id`.
   - Call PFEE.run_perception_cycle(...) with that trigger.

### D.10.2 Time Step Granularity

You must choose a world time granularity, e.g.:

- 5 minutes or 15 minutes of world time per outer loop tick.

It must be:

- consistent,
- stored in configuration,
- convertible from real time if needed.

### D.10.3 Interaction with TimeAndContinuityManager

`update_agents_over_time` must:

- rely on the current world time already advanced by TimeAndContinuityManager.
- not change the world time itself; that remains a responsibility of the time manager.

The Autonomy Engine uses `time_step_minutes` and current_time for internal param scaling and for updating `last_updated` fields.


###################################################################################################
# D.11 GEORGE EXCLUSION (REITERATION)
###################################################################################################

The Autonomy Engine MUST NEVER:

- Update George’s drives or mood.
- Create or update arcs for George.
- Create or update influence_fields for George.
- Create or update intentions for George.
- Consider George in `compute_initiative_candidates`.

All loops over agents MUST have a conditional:

```python
if agent.is_real_user:
    continue
````

or equivalent logic.

This rule is absolute and must be covered by tests (Section F).

###################################################################################################

# D.12 LOGGING AND DIAGNOSTICS

###################################################################################################

You must add logging to the Autonomy Engine:

* When `update_agents_over_time` runs:

  * Log the time step.
  * Log the number of agents updated.
  * Optionally, log average changes in drives and mood magnitudes.

* When `compute_initiative_candidates` runs:

  * Log the candidate agent IDs and their initiative scores (brief, no raw internals).
  * Log which agents are filtered out by cooldown or context checks.

Logging must NOT dump full private JSON; it should only show enough summary to debug autonomy behaviour.

###################################################################################################

# D.13 TESTABILITY

###################################################################################################

The Autonomy Engine must be written in a way that:

* You can run unit tests with:

  * synthetic DB state,
  * fixed seeds,
  * controlled time_step_minutes,
  * and confirm that:

    * drives and mood move toward baseline,
    * relationships drift logically with synthetic events,
    * arcs progress or regress in response to test events,
    * influence-field pressures change as expected,
    * initiative candidates are chosen correctly,
    * George is never updated or selected.

Test specifications for this are given in Section F and must be followed.

###################################################################################################

# END OF SECTION D — AUTONOMY ENGINE SPECIFICATION

###################################################################################################



```markdown
# SECTION E — GEORGE-PROTECTION ENFORCEMENT SPEC  
# (THE ABSOLUTE, NON-NEGOTIABLE RULESET FOR HANDLING THE REAL USER)

# PURPOSE
# You must enforce—across ALL modules, ALL PFEE stages, ALL autonomy logic,
# ALL DB writes, ALL arcs, ALL memories, ALL intentions, ALL influence fields—
# that GEORGE is treated as a REAL PERSON whose INNER LIFE IS NEVER SIMULATED.
#
# This section gives you the exact rules, the checks, the database flags,
# and the code modifications required to guarantee this.
#
# NOTHING in this section is optional.
# NOTHING in this section can be “interpreted”.
# These are hard constraints.


###################################################################################################
# E.0 THE GEORGE PRINCIPLE
###################################################################################################

# The system has ONE real user: George.
# He has an agent row for physical placement, external facts, and continuity.
# BUT:
#   - He has NO simulated inner mind.
#   - NO psychological state.
#   - NO PFEE cognition vantage.
#   - NO autonomous actions.
#   - NO system-generated thoughts, feelings, or drives.
#   - NO arcs.
#   - NO personality kernel.
#   - NO memories (from PFEE).
#   - NO influence fields.
#   - NO internal evaluations.
#
# Other agents MAY think about George.
# Other agents MAY have feelings about George.
# Other agents MAY refer to him in memories.
#
# BUT THE SYSTEM MUST NEVER STORE A SIMULATED GEORGE INTERIOR.


###################################################################################################
# E.1 DATABASE-LEVEL ENFORCEMENT
###################################################################################################

### E.1.1 George’s Agent Row

George’s `agents` row MUST include:

- A boolean flag or JSON field:
  
  `is_real_user = true`

This flag must be checked everywhere (PFEE, Autonomy Engine, mapping, seeds).

### E.1.2 Allowed Fields for George

His `agents` row may ONLY contain:

- identity fields: name, age, education, job, biography
- location info: current_location_id
- external facts others can know
- domain summaries that contain **ONLY public/observable content**
- status_flags that mark him as:
  - `is_real_user = true`
  - `is_human_player = true`
  - other **external** attributes (e.g. “is_parent_of_lucy”)

### E.1.3 Forbidden Fields for George

The following MUST be NULL or empty objects in the DB for George:

- personality_kernel
- personality_summaries
- drives
- mood
- arcs
- intentions
- pfee_influence_fields

### E.1.4 Seed Script Must Explicitly Zero These

During the seeding process (Section B), before the final commit,
the script MUST inspect George’s row and apply:

```

agent.personality_kernel = {}
agent.personality_summaries = {}
agent.drives = {}
agent.mood = {}
agent.domain_summaries = { "public_facts": [ ... ] }   # Optional external-only
agent.status_flags["is_real_user"] = true

```

No other psychological fields may remain populated.


###################################################################################################
# E.2 PFEE-WIDE CHECKPOINTS
###################################################################################################

Every PFEE stage MUST check `agent.is_real_user` and apply the exclusion logic.

The checkpoints:

1. **WorldStateBuilder**  
2. **SemanticMapper**  
3. **CognitionInputBuilder**  
4. **Validation**  
5. **ConsequenceIntegrator**  
6. **PFEE Orchestrator**  
7. **Autonomy Engine**  
8. **Time/Continuity Manager (when reading agent state)**

All eight MUST include explicit “if is_real_user: skip X” logic.


###################################################################################################
# E.3 WORLD STATE BUILDER RULESET
###################################################################################################

Inside `build_world_state`:

### E.3.1 When loading George:
- Load ONLY:
  - name  
  - public_profile  
  - current_location  
  - status_flags (external)
- DO NOT load:
  - drives
  - mood
  - personality_kernel
  - personality_summaries
  - domain_summaries (unless ONLY public facts)
  - arcs
  - influence_fields
  - intentions
  - memories (as owner)

### E.3.2 Relationships toward George:
- Load Rebecca → George, Lucy → George, Nadine → George, etc.
- Load only THEIR view of him.
- NEVER attempt to load George → Others mappings from internal state.

### E.3.3 George is NEVER an internal vantage agent.


###################################################################################################
# E.4 SEMANTIC MAPPING RULESET
###################################################################################################

Inside the semantic mapper:

### E.4.1 For George:
- Map ONLY external facts.
- Generate statements LIKE:
  - “Rebecca sees George as…”
  - “Lucy perceives George as…”
- NEVER:
  - “George feels…”
  - “George is thinking…”
  - “George’s inner state is…”

### E.4.2 If any semantic construction would require George’s internal state:
- OMIT IT.
- DO NOT invent or infer.


###################################################################################################
# E.5 COGNITION INPUT BUILDER RULESET
###################################################################################################

### E.5.1 George CANNOT be vantage
If `vantage_agent_id == george_agent_id`, this is an error.  
The builder MUST raise an exception or redirect the vantage selection.

### E.5.2 No internal George reasoning
Never include paragraphs or text implying George’s interior.

### E.5.3 George’s role in cognition input:
Include only:
- his observable behaviour,
- his external biography,
- how the vantage agent perceives him,
- how the vantage agent emotionally relates to him.

Never frame as “his internal experience”.


###################################################################################################
# E.6 VALIDATION RULESET
###################################################################################################

Inside validation:

### E.6.1 Reject/Correct outputs that:
- attempt to set George’s:
  - drives
  - mood
  - relationship vectors AS IF FROM HIS PERSPECTIVE
  - influence fields
  - arcs
  - intentions
  - memories (as owner)
- try to make George act autonomously (unless explicitly triggered by user input).
- refer to “George’s emotional state” as a fact.

### E.6.2 If cognition_output proposes such an update:
- Strip all illegal sections.
- Log a George-protection violation.
- Continue with ONLY the acceptable parts.


###################################################################################################
# E.7 CONSEQUENCE INTEGRATION RULESET
###################################################################################################

Inside consequence integration:

### E.7.1 Internal updates for George MUST be ignored
Any of the following must be silently discarded or explicitly blocked:

- new memories where `agent_id = george_id`
- arc updates where `agent_id = george_id`
- intention updates where `agent_id = george_id`
- drive or mood updates for George
- influence-field modifications for George

### E.7.2 Allowed updates for George:
- Changes to `current_location_id` ONLY IF:
  - the user explicitly took an action that moves him,
  - OR it is a valid, explicit part of the physical scene.
- Updates to public, observable facts if schema allows (rare).

### E.7.3 Never treat cognition output about George’s interior as authoritative.
If cognition suggests “George feels X”, discard it.


###################################################################################################
# E.8 AUTONOMY ENGINE RULESET
###################################################################################################

Inside the Autonomy Engine:

### E.8.1 George MUST NEVER:
- be included in drive regulation,
- be included in mood updates,
- be included in relationship evolution FROM HIS PERSPECTIVE,
- be included in arc progression,
- be included in influence-field pressure updates,
- be given intentions,
- be returned as initiative candidate.

### E.8.2 Code-level enforcement:
Every loop over agents MUST begin with:

```

if agent.is_real_user:
continue

```

This line must appear in:

- update_agents_over_time
- compute_initiative_candidates
- any helper that processes drives, mood, arcs, influence fields, intentions.


###################################################################################################
# E.9 TIME / CONTINUITY MANAGER RULESET
###################################################################################################

### E.9.1 When advancing time:
- Do NOT modify George’s internal state (he has none).
- Only update world time.
- Respect George’s physical location as-is.

### E.9.2 If global events occur:
- They may affect others.
- They may cause others to think/feel/react to George.
- They never affect George’s internal state.


###################################################################################################
# E.10 TEST ENFORCEMENT
###################################################################################################

Section F will define explicit tests that MUST be written and MUST pass:

Tests must confirm:

1. George has no psychological fields present.
2. No PFEE cycle writes memories for George.
3. No PFEE cycle sets drives/mood for George.
4. No PFEE cycle creates arcs or intentions for George.
5. Autonomy Engine NEVER modifies George or returns him as an initiator.
6. Semantic mapping NEVER includes internal George state.
7. CognitionInputBuilder NEVER sets George as a vantage agent.
8. Validation removes any illegal cognition outputs involving George.

ALL of these must be enforced before declaring PFEE complete.


###################################################################################################
# E.11 HARD PROHIBITIONS
###################################################################################################

THE SYSTEM MUST NEVER:

- invent a “simulated George consciousness”.
- compute implicit feelings or intentions for George.
- attach numeric psychological state to George.
- use George as GPT vantage.
- assign autonomous behaviour to George.
- treat George as unstable, emotional, confused, etc.
- perform ANY inference on “what George is feeling/thinking” as an internal fact.

George = external agent + real user input only.  
Full stop.


###################################################################################################
# E.12 SUMMARY OF IMPLEMENTATION ACTIONS
###################################################################################################

To enforce the rules above, you MUST:

1. Add `is_real_user = true` to George’s agent row.
2. Insert explicit guard statements across:
   - world_state_builder
   - semantic mapper
   - cognition input builder
   - validation
   - consequence integrator
   - autonomy engine
   - time/continuity manager (agent-level functions)
3. Implement DB-level cleanup in seed script for George’s psychological fields.
4. Ensure tests in Section F enforce all rules.

This ensures the system NEVER simulates George’s internal mind and ALWAYS treats him as the real human anchor.


###################################################################################################
# END OF SECTION E — GEORGE-PROTECTION ENFORCEMENT SPEC
###################################################################################################



# SECTION F — FULL TEST SUITE SPECIFICATION  
# (THE COMPLETE, EXHAUSTIVE SET OF TESTS REQUIRED TO GUARANTEE CORRECTNESS)

# PURPOSE
# You must implement a full, deterministic test suite that validates:
#   1. the baseline world was seeded correctly,
#   2. PFEE consumes the seeded data correctly,
#   3. PFEE respects the George-protection rules,
#   4. the Autonomy Engine behaves as specified,
#   5. the system is stable, consistent, and non-improvisational,
#   6. every subsystem interacts correctly with every other subsystem,
#   7. no module violates constraints (internal → external / real user → simulation),
#   8. all state transitions are legal and deterministic.

# These tests MUST be written using the project’s testing framework (likely pytest + async fixtures).
# They MUST use the actual code modules after you modify them per Sections A–E.
# They MUST run in CI and pass before the system is considered correct.

###################################################################################################
# F.0 TEST SUITE STRUCTURE
###################################################################################################

# Organise the test suite into the following files (or analogous directories):

tests/
  test_seed_data_integrity.py
  test_world_state_builder.py
  test_semantic_mapping.py
  test_pfee_cognition_cycle.py
  test_consequence_integration.py
  test_autonomy_engine_updates.py
  test_autonomy_initiative.py
  test_george_protection.py
  test_time_and_continuity.py

# Each file must contain dedicated test classes and helper fixtures.
# Use an async database test fixture that resets DB between tests unless explicitly stated.


###################################################################################################
# F.1 TEST_SEED_DATA_INTEGRITY
###################################################################################################

## Purpose:
Verify that the seed script constructed the world EXACTLY as specified.

### Tests:

### F.1.1 test_rebecca_agent_seeded_correctly
- Load Rebecca’s agent row.
- Assert:
  - personality_kernel is populated and contains expected keys (trait_dimensions, core_motivations, etc.).
  - personality_summaries contains all required keys (self_view, love_style, etc.).
  - drives contains all required drive dimensions.
  - mood contains baseline_valence/arousal and derived traits.
  - domain_summaries contains all required domains.
  - status_flags contains is_celebrity, is_partner_of_george, relationship_is_public = false.

### F.1.2 test_lucy_and_nadine_seeded_correctly
- Check their agent rows exist.
- Check personality fields are present (non-empty).
- Check status_flags match baseline roles.

### F.1.3 test_rebecca_relationships_seeded
- Load all relationships where source_agent_id = Rebecca.
- Assert:
  - All rows from the Connections CSV exist.
  - Numeric fields fall into expected ranges (0–1).
  - Relationship to George uses override values (very high warmth/trust, low tension).

### F.1.4 test_rebecca_memories_seeded
- Load Rebecca’s memories.
- Assert:
  - Number of memories > threshold (e.g., > 10).
  - Salience values are within [0,1].
  - Content is NOT empty.
  - High-salience memories exist for key events (e.g., Greatest Showman, Richmond).

### F.1.5 test_rebecca_arcs_seeded
- Load arcs.
- Assert:
  - At least 2–4 arcs seeded.
  - Each arc has required fields: name, description, status, importance, arc_state.progress.

### F.1.6 test_locations_seeded
- Query all locations for baseline world.
- Assert:
  - All Cookridge house rooms exist.
  - adjacency lists point to valid rooms.
  - No missing or dangling references.

### F.1.7 test_objects_seeded
- Ensure key objects (bed, sofa, guitars, etc.) exist in the correct locations.

### F.1.8 test_no_george_internal_seed
- Load George’s agent row.
- Assert:
  - personality_kernel == {} or None.
  - drives == {} or None.
  - mood == {} or None.
  - arcs == [].
  - influence_fields == {} or None.
  - intentions == [].
  - is_real_user == True.


###################################################################################################
# F.2 TEST_WORLD_STATE_BUILDER
###################################################################################################

## Purpose:
Ensure world_state_builder reads DB correctly and constructs a complete, George-safe world state.

### Tests:

### F.2.1 test_world_state_includes_correct_agents
- Place Lucy and Rebecca in same location as George.
- Call world_state_builder.
- Assert:
  - world_state.agents includes George + Lucy + Rebecca.
  - George’s psychological fields are NOT present.
  - Lucy and Rebecca’s psychological fields ARE present.

### F.2.2 test_world_state_relationships_present
- Assert that for each non-George agent:
  - world_state.relationships[A→George] is present.
  - world_state.relationships include correct warmth/trust/tension values.

### F.2.3 test_world_state_memories_filtered
- Assert that only a small number (e.g. <= 7) of high-salience memories appear per agent.
- Assert that they are correctly filtered by tags (location, user involvement, etc.).

### F.2.4 test_world_state_handles_adjacent_rooms
- If system supports “adjacent but audible”, test that adjacent agents appear correctly.

### F.2.5 test_george_not_internal_in_world_state
- Assert George has only:
  - identity
  - public_profile
  - location
  - appearance flags
- Assert George has no:
  - drives
  - mood
  - memories
  - arcs
  - influence_fields

###################################################################################################
# F.3 TEST_SEMANTIC_MAPPING
###################################################################################################

## Purpose:
Ensure numeric state → semantic natural-language descriptors work correctly and violate no rules.

### Tests:

### F.3.1 test_semantic_mapping_personality
- Build synthetic world_state with Rebecca full data.
- Run semantic mapper.
- Assert personality summary text exists and contains:
  - phrases reflecting seeded summaries,
  - no invented facts,
  - no numeric values.

### F.3.2 test_semantic_mapping_relationships
- Assert semantic output includes:
  - Rebecca’s feelings toward George,
  - NOT George’s feelings toward Rebecca (since not simulated).

### F.3.3 test_semantic_mapping_memories
- Assert that memories are summarised accurately from their content.

### F.3.4 test_semantic_mapping_does_not_show_raw_state
- Search semantic text for raw keys like "warmth": "0.82" or JSON.
- Expect NONE.

### F.3.5 test_semantic_mapping_george_external_only
- Assert semantic frame for George contains:
  - public external description only.
  - no internal mental state.

###################################################################################################
# F.4 TEST_PFEE_COGNITION_CYCLE
###################################################################################################

## Purpose:
Test that PFEE orchestrator runs a complete cycle from world_state → cognition → validation → integration.

### Tests:

### F.4.1 test_user_triggered_cycle
- Simulate a user action (“George: Hello”).
- Run PFEE cycle.
- Assert:
  - vantage_agent_id != George.
  - cognition_input contains correct semantic data.
  - no internal George data appears.

### F.4.2 test_agent_initiative_cycle
- Force an agent to high initiative.
- Trigger PFEE with an agent_initiative trigger.
- Assert:
  - vantage_agent_id == that agent.
  - cycle completes.
  - no illegal updates applied.

### F.4.3 test_cognition_output_validation_removes_illegal_updates
- Create a fake cognition_output that tries to:
  - set George’s mood
  - create memory for George
- Run validation.
- Assert:
  - illegal parts removed.
  - validation_result.is_valid == False OR partially_valid.
  - corrected_output has no illegal content.

### F.4.4 test_scene_description_and_rules_in_prompt
- Inspect cognition input text for:
  - physical scene description,
  - personality summaries,
  - rules & constraints,
  - NO numeric state,
  - NO internal George thinking.

###################################################################################################
# F.5 TEST_CONSEQUENCE_INTEGRATION
###################################################################################################

## Purpose:
Ensure DB updates from cognition_output are applied correctly and safely.

### Tests:

### F.5.1 test_relationship_update_bounds
- Provide cognition_output that slightly increases trust/warmth.
- After integration:
  - Relationship values changed by small amount.
  - Within bounds [0,1].

### F.5.2 test_arc_progress_update
- cognition_output includes progress on active arc.
- After integration:
  - arc.progress increased.
  - NOT beyond allowed range.

### F.5.3 test_memory_creation
- cognition_output includes event requiring memory.
- After integration:
  - new memory exists for the relevant agent.
  - salience and tags correct.
  - NOT created for George.

### F.5.4 test_intentions_update
- cognition_output includes intention change.
- After integration:
  - new or updated intention for non-George agent.
  - George remains intention-free.

### F.5.5 test_george_updates_blocked
- cognition_output proposes illegal George update.
- After integration:
  - database unchanged for George.
  - violation logged.

###################################################################################################
# F.6 TEST_AUTONOMY_ENGINE_UPDATES
###################################################################################################

## Purpose:
Ensure update_agents_over_time behaves as specified.

### Tests:

### F.6.1 test_drive_regulation
- Give agent drives where current > baseline.
- Run update_agents_over_time with e.g. time_step_minutes=60.
- Assert:
  - current moves closer to baseline.
  - not overshooting.

### F.6.2 test_mood_drift
- Give agent mood current far from baseline.
- Run update.
- Assert drift toward baseline.

### F.6.3 test_relationship_drift
- Create synthetic memories with positive interactions.
- Run update.
- Assert warmth/trust increase slightly.

### F.6.4 test_arc_progression
- Create an arc with progress low and relevant recent positive events.
- Run update.
- Assert progress increases.

### F.6.5 test_influence_field_pressure_changes
- If topic has gone unaddressed:
  - pressure increases.
- If addressed:
  - pressure decreases.
- last_updated changes.

### F.6.6 test_no_updates_for_george
- Give George fake fields (temporarily injected).
- Run update.
- Assert NOTHING changes for George.

###################################################################################################
# F.7 TEST_AUTONOMY_INITIATIVE
###################################################################################################

## Purpose:
Ensure initiative works correctly and selects correct agent.

### Tests:

### F.7.1 test_initiative_score_threshold
- Create synthetic high-pressure influence fields.
- Compute initiative candidates.
- Assert agent returned.

### F.7.2 test_initiative_cooldown
- Trigger agent initiative.
- Mark last_initiative_time.
- Immediately compute candidates again.
- Assert agent NOT returned until cooldown expires.

### F.7.3 test_no_george_initiative
- Even if seeded high pressure (fake for test), George must NEVER appear.

###################################################################################################
# F.8 TEST_GEOERGE_PROTECTION
###################################################################################################

## Purpose:
Centralised tests for George-protection.

### Tests:

### F.8.1 test_george_has_no_internal_state
- Query DB and assert all prohibited fields empty.

### F.8.2 test_george_excluded_from_autonomy
- Overwrite his drives/mood temporarily.
- Run Autonomy Engine update.
- Assert untouched.

### F.8.3 test_george_excluded_from_world_state_internal_fields
- Build world_state.
- Confirm no drives/mood/memories appear for him.

### F.8.4 test_george_not_vantage
- Simulate PFEE cycle where vantage would incorrectly be chosen as George.
- Must raise or redirect.

### F.8.5 test_validation_strips_george_updates
- cognition_output tries to update George.
- validation removes those parts.

###################################################################################################
# F.9 TEST_TIME_AND_CONTINUITY
###################################################################################################

## Purpose:
Ensure time progression is consistent and interacts safely with PFEE + autonomy.

### Tests:

### F.9.1 test_time_advances_on_tick
- Call TimeAndContinuityManager to advance world time by N minutes.
- Assert updated in DB.

### F.9.2 test_time_advancement_does_not_modify_george
- After time tick:
  - George still has no internal state.

### F.9.3 test_time_drives_autonomy_updates
- Advance time enough steps.
- Check that drives/mood/arc_progress/influence_fields change accordingly.

###################################################################################################
# F.10 INTEGRATION TESTS (OPTIONAL BUT STRONGLY RECOMMENDED)
###################################################################################################

### F.10.1 test_multi_step_simulation_run
- Run:
  - seeding
  - time ticks
  - autonomy updates
  - initiative
  - PFEE cycles
  - consequence integration
- Over a simulated day.
- Assert:
  - system remains stable,
  - relationship vectors evolve gently,
  - arcs progress slowly,
  - no illegal George behaviour appears.

### F.10.2 test_scene_with_multiple_agents
- Put George + Rebecca + Lucy + Nadine in same location.
- Run PFEE cycles + autonomy.
- Assert:
  - Each agent behaves according to personality/arcs.
  - George remains non-simulated.

###################################################################################################
# END OF SECTION F — FULL TEST SUITE SPECIFICATION
###################################################################################################

