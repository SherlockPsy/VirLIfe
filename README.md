# README.md  
**VIRTUAL WORLD BACKEND**  
**ARCHITECTURE • LOGIC • INTERPRETATION RULES**

This README provides a clear, builder-ready introduction to the full system.  
It summarizes nothing — it references the authoritative MASTER_SPEC.md and explains how the builder LLM MUST interpret it.

======================================================================
# 1. PURPOSE OF THIS REPOSITORY
======================================================================

This repository defines the entire architecture, logic, worldview, and rules for building a persistent, deterministic social world simulation in which:

- all simulated humans have autonomous internal lives  
- the world continues even when the user is offline  
- YOU (the user) are a real person, **not** a simulated mind  
- the system never infers your inner life  
- the system uses deterministic psychology + occasional LLM cognition  
- the renderer outputs perception only  
- examples are NEVER treated as rules  

The **MASTER_SPEC.md** file is the single source of truth.

This README explains how to use it safely.

======================================================================
# 2. ABSOLUTE INTERPRETATION RULES FOR BUILDER LLMS
======================================================================

You MUST obey these rules exactly when consuming MASTER_SPEC.md.  
These exist to prevent hallucination, misinterpretation, or unintended “rule creation.”

### 2.1 Normative vs Non-Normative
- **Normative text** contains MUST / MUST NOT / SHALL / SHALL NOT and defines requirements.  
- **Non-normative examples** are clearly labelled "**Example — NON-NORMATIVE**" or "**Examples — NON-NORMATIVE**".  
- Examples illustrate patterns; they are NEVER rules.

### 2.2 Requirements Always Win
If an example *appears* to contradict a requirement:
- the requirement wins  
- the example MUST be ignored as a rule  

### 2.3 No Implicit Inference  
You MUST NOT infer rules from:
- patterns in examples  
- narrative phrasing  
- human-readable explanations  
- context that is not explicit  

### 2.4 No Summarisation  
You MUST NOT compress, reinterpret, or “improve” normative text.  
The implementation MUST reflect the specification exactly.

### 2.5 Numeric vs Semantic  
- Internal agent psychology MUST be numeric and deterministic.  
- LLMs MUST see semantic summaries only.  
- LLMs MUST NOT manipulate numbers.  
- LLM outputs MUST be converted to numeric updates deterministically.

### 2.6 User MUST NOT be Simulated  
The user (George) MUST NOT have:  
- drives  
- mood  
- arcs  
- intentions  
- energy  
- personality vector  
- outgoing relationship edges  
- simulated cognition  

Agents MAY store memories and facts *about* the user based on observable behaviour and explicit statements.

### 2.7 Single Source of Truth  
MASTER_SPEC.md overrides:
- examples  
- assumptions  
- any other files  
- latent LLM “common sense”  
- any external model bias  

======================================================================
# 3. SYSTEM OVERVIEW (FOR BUILDERS)
======================================================================

The system is composed of:

1. **World Engine** — deterministic world physics and time.  
2. **Autonomy Engine** — deterministic low-level behaviour, mood, drives, arcs.  
3. **Cognition Service (LLM)** — high-value, meaningful decisions ONLY.  
4. **Renderer Service (LLM)** — pure perceptual output, no omniscience.  
5. **Gateway** — interface between user and world.  
6. **Persistence Layer** — long-term storage.  

See MASTER_SPEC.md for full requirements.

======================================================================
# 4. CORE PRINCIPLES
======================================================================

These principles MUST be upheld across all code:

### 4.1 Deterministic Substrate  
All psychology, behaviour, and world updates MUST be deterministic.

### 4.2 Minimal Numeric State  
Agents MUST use a minimal, universal set of variables:
- mood  
- drives  
- personality  
- relationships  
- arcs  
- intentions  
- energy  
- episodic memory  
- **biographical memory**  

### 4.3 Biographical Memory Is Essential  
Agents MUST maintain persistent long-term facts about others.  
These MUST:
- grow naturally over time  
- shape interpretation of events  
- NEVER include user internal states  

### 4.4 LLM Use is Sparse and Controlled  
LLM cognition MUST be triggered ONLY for meaningful, high-stakes events.  
LLM rendering MUST reflect perception only.

### 4.5 No User Internal State  
The user is real.  
Only behaviour enters the simulation.

======================================================================
# 5. FILE STRUCTURE (RECOMMENDED)
======================================================================

/
├── MASTER_SPEC.md          # full authoritative specification
├── README.md               # this file
├── docs/                   # future additions
│   ├── diagrams/           # architecture diagrams
│   ├── api/                # gateway interface docs
│   └── logic_notes/        # derived deterministic rules
└── src/
├── world/              # World Engine
├── autonomy/           # Autonomy Engine
├── cognition/          # LLM Cognition wrapper
├── renderer/           # LLM Renderer wrapper
├── state/              # Agent models, memory, arcs
└── gateway/            # user interaction layer

======================================================================
# 6. DEVELOPMENT GUIDELINES FOR BUILDER LLMS
======================================================================

### 6.1 Always validate your output against MASTER_SPEC.md  
Never produce features or behaviour that contradict it.

### 6.2 Never invent psychological variables  
You MUST use the exact variable set defined in the spec.

### 6.3 Never invent new rules  
If something is not explicitly required, you MUST use the general principles described.

### 6.4 Do not optimise away complexity  
If the spec says something MUST persist, drift, decay, or bias behaviour, it must.

### 6.5 Never simulate the user  
This is the most critical rule.  
Violating it breaks the entire system.

======================================================================
# 7. FREQUENT BUILDER ERRORS (AND THEIR FIXES)
======================================================================

### 7.1 Treating Examples as Rules  
Fix: Only normative text defines requirements.

### 7.2 Inventing Additional Internal States  
Fix: Use the minimal variable set only.

### 7.3 Inferring User Feelings  
Fix: Use observable actions only.

### 7.4 Using LLM for Trivial Behaviour  
Fix: Use deterministic tendencies instead.

### 7.5 Storing User Psychology  
Fix: Allowed memories must be episodic or biographical FROM THE AGENT POV ONLY.

======================================================================
# 8. STARTING THE BUILD
======================================================================

The recommended build order is:

1. World Engine  
2. Agent Model  
3. Autonomy Engine  
4. Memory systems (episodic + biographical)  
5. Cognition Service (LLM wrapper)  
6. Numeric→Semantic summary generator  
7. Renderer Service  
8. Gateway  
9. Persistence integration  

Each subsystem MUST be tested against MASTER_SPEC.md.

======================================================================
# 9. DEPLOYMENT AND INFRASTRUCTURE
======================================================================

**This application is designed to run exclusively on Railway with managed services.**

### 9.1 Required Services

All services are managed by Railway:
- **PostgreSQL** - Authoritative database (required, no SQLite support)
- **Redis** - Non-authoritative caching layer (optional, Phase 9+)
- **Qdrant** - Vector memory for semantic search (optional, Phase 9+)

### 9.2 Environment Variables

Required environment variables from Railway:
- `DATABASE_URL` - PostgreSQL connection string (Railway provides automatically)
- `VENICE_API_KEY` - Venice.ai API key for LLM services
- `VENICE_BASE_URL` - Venice API endpoint
- `COGNITION_MODEL_ID` - Model ID for cognition processing
- `RENDERER_MODEL_ID` - Model ID for perception rendering

Optional (Phase 9+):
- `REDIS_URL` - Redis connection string (Railway provides)
- `QDRANT_URL` - Qdrant service URL (Railway provides)
- `QDRANT_API_KEY` - Qdrant authentication key (if enabled)

### 9.3 Local Development

**Local development must connect to Railway services.**

This application does NOT support local SQLite or local-only databases.
To develop locally:
1. Link to Railway project: `railway link`
2. Use Railway environment variables: `railway run <command>`
3. Or export Railway's `DATABASE_URL` to your local environment

See `RAILWAY_SETUP.md` for complete deployment instructions.

======================================================================
# 10. FINAL NOTE
======================================================================

MASTER_SPEC.md is not a suggestion.  
It is the **law of the world**.  
You MUST follow it exactly as written.

For any unclear case:
- Prefer the general rules.  
- Never infer from examples.  
- Never simulate the user.  
- Never violate determinism.  

Failure to follow these rules creates an invalid build.

# END OF README.md
