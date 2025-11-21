# Database Schema Documentation

**Database:** PostgreSQL (Railway)  
**Generated:** $(date)  
**Total Tables:** 15

---

## Table of Contents

- [Core World Tables](#core-world-tables)
- [Agent State Tables](#agent-state-tables)
- [PFEE Tables](#pfee-tables)

---

## Core World Tables

### `worlds`
World state management.

**Columns:**
- `id` (integer, PK) - Primary key
- `current_tick` (integer, NOT NULL) - Current world tick
- `current_time` (timestamp with time zone, NOT NULL) - Current world time
- `created_at` (timestamp with time zone) - Creation timestamp
- `updated_at` (timestamp with time zone) - Last update timestamp

**Row Count:** 47

---

### `locations`
Location definitions with adjacency information.

**Columns:**
- `id` (integer, PK) - Primary key
- `name` (varchar, NOT NULL) - Location name
- `description` (text, NOT NULL) - Location description
- `world_id` (integer, FK → worlds.id, NOT NULL) - World reference
- `attributes` (json) - Location attributes/tags
- `adjacency` (json, NOT NULL) - List of connected location IDs

**Foreign Keys:**
- `world_id` → `worlds.id`

**Row Count:** 0

---

### `users`
User accounts (human users only - no internal state).

**Columns:**
- `id` (integer, PK) - Primary key
- `name` (varchar, NOT NULL, UNIQUE) - User name

**Indexes:**
- `users_name_key` - Unique index on `name`

**Row Count:** 1

---

### `agents`
Agent entities with psychological and physical state.

**Columns:**
- `id` (integer, PK) - Primary key
- `name` (varchar, NOT NULL) - Agent name
- `world_id` (integer, FK → worlds.id, NOT NULL) - World reference
- `location_id` (integer, FK → locations.id) - Current location
- `energy` (double precision, NOT NULL, default: 1.0) - Physical energy
- `mood` (json, NOT NULL) - Mood state: `{valence: float, arousal: float}`
- `drives` (json, NOT NULL) - Drive levels: `{drive_name: {level: float, sensitivity: float}}`
- `personality_kernel` (json, NOT NULL) - Core personality traits
- `personality_summaries` (json, NOT NULL) - Stable personality summaries
- `domain_summaries` (json, NOT NULL) - Domain-specific summaries
- `cached_context_fragments` (json, NOT NULL) - Cached context
- `status_flags` (json, NOT NULL) - Status flags
- `last_cognition_timestamp` (timestamp with time zone) - Last cognition call time
- `created_at` (timestamp with time zone) - Creation timestamp
- `updated_at` (timestamp with time zone) - Last update timestamp

**Foreign Keys:**
- `world_id` → `worlds.id`
- `location_id` → `locations.id`

**Row Count:** 0

---

### `objects`
Physical objects in locations.

**Columns:**
- `id` (integer, PK) - Primary key
- `name` (varchar, NOT NULL) - Object name
- `description` (text, NOT NULL) - Object description
- `location_id` (integer, FK → locations.id, NOT NULL) - Location reference
- `state` (json) - Object state

**Foreign Keys:**
- `location_id` → `locations.id`

**Row Count:** 0

---

### `events`
World events with source/target entities.

**Columns:**
- `id` (integer, PK) - Primary key
- `world_id` (integer, FK → worlds.id, NOT NULL) - World reference
- `type` (varchar, NOT NULL) - Event type
- `description` (text, NOT NULL) - Event description
- `source_entity_id` (varchar) - Source entity (format: "agent:1", "user:1", "system", "object:5")
- `target_entity_id` (varchar) - Target entity
- `payload` (json) - Event payload data
- `tick` (integer, NOT NULL) - World tick when event occurred
- `timestamp` (timestamp with time zone, NOT NULL) - Event timestamp
- `processed` (boolean) - Whether event has been processed

**Foreign Keys:**
- `world_id` → `worlds.id`

**Row Count:** 22

---

## Agent State Tables

### `relationships`
Agent-to-agent and agent-to-user relationships.

**Columns:**
- `id` (integer, PK) - Primary key
- `source_agent_id` (integer, FK → agents.id, NOT NULL) - Source agent
- `target_agent_id` (integer, FK → agents.id) - Target agent (if agent-to-agent)
- `target_user_id` (integer, FK → users.id) - Target user (if agent-to-user)
- `warmth` (double precision, default: 0.0) - Warmth metric
- `trust` (double precision, default: 0.0) - Trust metric
- `tension` (double precision, default: 0.0) - Tension metric
- `attraction` (double precision, default: 0.0) - Attraction metric
- `familiarity` (double precision, default: 0.0) - Familiarity metric
- `comfort` (double precision, default: 0.0) - Comfort metric
- `volatility` (double precision, default: 0.0) - Volatility metric

**Foreign Keys:**
- `source_agent_id` → `agents.id`
- `target_agent_id` → `agents.id`
- `target_user_id` → `users.id`

**Row Count:** 0

---

### `memories`
Episodic and biographical memories.

**Columns:**
- `id` (integer, PK) - Primary key
- `agent_id` (integer, FK → agents.id, NOT NULL) - Agent reference
- `type` (varchar, NOT NULL) - Memory type: "episodic" or "biographical"
- `description` (text, NOT NULL) - Memory description
- `timestamp` (timestamp with time zone) - Memory timestamp (nullable for biographical)
- `salience` (double precision, default: 0.0) - Memory salience
- `semantic_tags` (json, default: []) - Semantic tags
- `created_at` (timestamp with time zone) - Creation timestamp

**Foreign Keys:**
- `agent_id` → `agents.id`

**Row Count:** 0

---

### `arcs`
Narrative arcs with intensity and valence.

**Columns:**
- `id` (integer, PK) - Primary key
- `agent_id` (integer, FK → agents.id, NOT NULL) - Agent reference
- `type` (varchar, NOT NULL) - Arc type/name
- `intensity` (double precision, default: 0.0) - Arc intensity
- `valence_bias` (double precision, default: 0.0) - Valence bias
- `topic_vector` (json, default: []) - Semantic keywords or vector representation
- `decay_rate` (double precision, default: 0.1) - Decay rate

**Foreign Keys:**
- `agent_id` → `agents.id`

**Row Count:** 0

---

### `intentions`
Agent intentions with priority and horizon.

**Columns:**
- `id` (integer, PK) - Primary key
- `agent_id` (integer, FK → agents.id, NOT NULL) - Agent reference
- `description` (text, NOT NULL) - Intention description
- `priority` (double precision, default: 0.0) - Intention priority
- `horizon` (varchar, default: "short") - Time horizon: "short", "medium", "long"
- `type` (varchar, default: "action") - Intention type
- `stability` (double precision, default: 0.5) - Stability metric
- `created_at` (timestamp with time zone) - Creation timestamp
- `updated_at` (timestamp with time zone) - Last update timestamp

**Foreign Keys:**
- `agent_id` → `agents.id`

**Row Count:** 0

---

### `calendars`
Agent calendar items (appointments, obligations, plans, routines).

**Columns:**
- `id` (integer, PK) - Primary key
- `agent_id` (integer, FK → agents.id, NOT NULL) - Agent reference
- `title` (varchar, NOT NULL) - Calendar item title
- `description` (text) - Calendar item description
- `start_time` (timestamp with time zone, NOT NULL) - Start time
- `end_time` (timestamp with time zone) - End time (optional)
- `type` (varchar, default: "appointment") - Item type: "appointment", "obligation", "plan", "routine"
- `status` (varchar, default: "pending") - Status: "pending", "active", "completed", "missed", "cancelled"
- `recurrence_rule` (varchar) - Recurrence rule (optional)
- `created_at` (timestamp with time zone) - Creation timestamp
- `updated_at` (timestamp with time zone) - Last update timestamp

**Foreign Keys:**
- `agent_id` → `agents.id`

**Row Count:** 0

---

## PFEE Tables

### `pfee_potentials`
Latent potentials for resolution into concrete entities/events.

**Columns:**
- `id` (integer, PK) - Primary key
- `context_type` (varchar, NOT NULL) - Context type
- `potential_type` (varchar, NOT NULL) - Potential type
- `parameters` (json, NOT NULL) - Potential parameters
- `created_at` (timestamp with time zone) - Creation timestamp
- `resolved_at` (timestamp with time zone) - Resolution timestamp
- `is_resolved` (boolean, NOT NULL, default: false) - Whether potential is resolved

**Row Count:** 0

---

### `pfee_influence_fields`
Cross-time influence fields for persistent agents and systems.

**Columns:**
- `id` (integer, PK) - Primary key
- `agent_id` (integer, FK → agents.id, NOT NULL, UNIQUE) - Agent reference (one per agent)
- `mood_offset` (json, NOT NULL) - Mood offset values
- `drive_pressures` (json, NOT NULL) - Drive pressure values
- `pending_contact_probability` (json, NOT NULL) - Pending contact probabilities
- `unresolved_tension_topics` (json, NOT NULL, default: []) - Unresolved tension topics
- `last_updated_timestamp` (timestamp with time zone) - Last update timestamp
- `created_at` (timestamp with time zone) - Creation timestamp

**Foreign Keys:**
- `agent_id` → `agents.id`

**Indexes:**
- `pfee_influence_fields_agent_id_key` - Unique index on `agent_id`

**Row Count:** 0

---

### `pfee_info_events`
Information events (messages, notifications, etc.).

**Columns:**
- `id` (integer, PK) - Primary key
- `type` (varchar, NOT NULL) - Event type
- `sender_id` (integer) - Sender ID
- `sender_type` (varchar, NOT NULL) - Sender type
- `recipient_id` (integer) - Recipient ID
- `recipient_type` (varchar) - Recipient type
- `content` (json, NOT NULL) - Event content
- `due_time` (timestamp with time zone) - Scheduled delivery time
- `processed` (boolean, NOT NULL, default: false) - Whether event has been processed
- `created_at` (timestamp with time zone) - Creation timestamp

**Row Count:** 0

---

### `pfee_logs`
PFEE operation logs for debugging and monitoring.

**Columns:**
- `id` (integer, PK) - Primary key
- `cycle_id` (varchar) - Perception cycle ID
- `log_type` (varchar, NOT NULL) - Log type
- `component` (varchar, NOT NULL) - Component name
- `message` (text) - Log message
- `metadata` (json, NOT NULL) - Additional metadata
- `created_at` (timestamp with time zone) - Creation timestamp

**Row Count:** 3

---

## Schema Notes

- All tables use integer primary keys with auto-increment sequences
- Timestamps use `timestamp with time zone` for proper timezone handling
- JSON columns are used for flexible structured data (mood, drives, personality, etc.)
- Foreign key relationships enforce referential integrity
- Indexes are in place on primary keys and foreign keys for performance
- Most tables are currently empty (fresh database)
- Active data exists in: `worlds` (47 rows), `events` (22 rows), `users` (1 row), `pfee_logs` (3 rows)

---

## Relationships Diagram

```
worlds
  ├── locations
  │     ├── agents
  │     └── objects
  ├── agents
  │     ├── relationships (source_agent_id)
  │     ├── relationships (target_agent_id)
  │     ├── memories
  │     ├── arcs
  │     ├── intentions
  │     ├── calendars
  │     └── pfee_influence_fields
  ├── events
  └── users
        └── relationships (target_user_id)
```

---

*Schema generated from PostgreSQL database on Railway*
