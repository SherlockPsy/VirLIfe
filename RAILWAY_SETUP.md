# RAILWAY PRODUCTION SETUP GUIDE

This document defines the **complete production architecture** for the Virtual World Backend on Railway.
It covers the full system topology including the core backend, authoritative persistence (Postgres), optimization caching (Redis), and vector memory (Qdrant).

**Target State:** Phase 9 (Full Production)

---

## 1. ARCHITECTURE OVERVIEW

The production system consists of four distinct services within a single Railway Project:

| Service Name | Type | Role | Visibility |
| :--- | :--- | :--- | :--- |
| `virlife-backend` | GitHub Repo | Core Logic, API, World Engine | **Public** (HTTP/HTTPS) |
| `virlife-db` | PostgreSQL | **Authoritative** State Store | Private (Internal Network) |
| `virlife-redis` | Redis | Non-Authoritative Cache | Private (Internal Network) |
| `virlife-qdrant` | Docker Image | Vector Memory Retrieval | Private (Internal Network) |

---

## 2. SERVICE CONFIGURATION

### 2.1 Database Service (`virlife-db`)
*   **Type:** PostgreSQL
*   **Image:** Standard Railway Postgres
*   **Resources:** Production tier recommended (for persistence guarantees).
*   **Networking:** Expose to other services in the project.

### 2.2 Backend Service (`virlife-backend`)
*   **Source:** GitHub Repository (`SherlockPsy/VirLIfe`)
*   **Build Command:** `pip install -r requirements.txt` (Auto-detected)
*   **Start Command:** `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
*   **Health Check Path:** `/health`
*   **Networking:** Public Domain enabled.

### 2.3 Redis Service (`virlife-redis`)
*   **Type:** Redis
*   **Role:** Caching for renderer context, cognition cooldowns, and short-term optimization.
*   **Persistence:** Not required (Ephemeral).
*   **Networking:** Private only.

### 2.4 Qdrant Service (`virlife-qdrant`)
*   **Type:** Docker Image
*   **Image Source:** `qdrant/qdrant:latest`
*   **Role:** Vector storage for episodic and biographical memory embeddings.
*   **Storage:** Mount a volume to `/qdrant/storage` to persist vectors across restarts.
*   **Networking:** Private only. Port `6333` (HTTP) and `6334` (GRPC).

---

## 3. ENVIRONMENT VARIABLES

These variables must be configured in the `virlife-backend` service.

### 3.1 Core System
| Variable | Value / Description | Required |
| :--- | :--- | :--- |
| `ENVIRONMENT` | `production` | **YES** |
| `APP_NAME` | `VirLife Backend` | No |
| `PORT` | (Provided by Railway) | **YES** |

### 3.2 Persistence (Postgres)
| Variable | Value / Description | Required |
| :--- | :--- | :--- |
| `DATABASE_URL` | `postgresql+asyncpg://...` (Link to `virlife-db`) | **YES** |

### 3.3 Optimization (Redis)
| Variable | Value / Description | Required |
| :--- | :--- | :--- |
| `REDIS_URL` | `redis://...` (Link to `virlife-redis`) | Phase 9+ |

### 3.4 Vector Memory (Qdrant)
| Variable | Value / Description | Required |
| :--- | :--- | :--- |
| `QDRANT_URL` | `http://virlife-qdrant:6333` (Internal URL) | Phase 9+ |
| `QDRANT_API_KEY` | (If configured in Qdrant) | Phase 9+ |

### 3.5 LLM Integration (Venice.ai)
| Variable | Value / Description | Required |
| :--- | :--- | :--- |
| `VENICE_API_KEY` | `sk-...` (Your Venice API Key) | **YES** |
| `VENICE_BASE_URL` | `https://api.venice.ai/api/v1` | **YES** |
| `COGNITION_MODEL_ID` | `llama-3.1-405b` (Reasoning/Logic) | **YES** |
| `RENDERER_MODEL_ID` | `llama-3.3-70b` (Perception/Roleplay) | **YES** |

---

## 4. DEPLOYMENT CHECKLIST

1.  **Create Project:** Create a new project on Railway.
2.  **Provision Database:** Add a PostgreSQL service (`virlife-db`).
3.  **Provision Backend:**
    *   Connect GitHub repo.
    *   Set `DATABASE_URL` (Railway often does this automatically when adding Postgres).
    *   Set `ENVIRONMENT=production`.
    *   Set LLM Keys (`VENICE_API_KEY`, etc.).
4.  **Provision Redis (Phase 9):** Add Redis service. Add `REDIS_URL` to Backend variables.
5.  **Provision Qdrant (Phase 9):**
    *   Add new service -> Docker Image -> `qdrant/qdrant`.
    *   Mount Volume: `/qdrant/storage`.
    *   Add `QDRANT_URL` to Backend variables.
6.  **Verify:**
    *   Check Build Logs.
    *   Visit Public URL `/health` -> Should return `{"status": "ok", "environment": "production"}`.

## 5. CRITICAL PRODUCTION RULES

1.  **Postgres is King:** If Redis or Qdrant fail, the system MUST fall back to Postgres-only operation. The backend must handle connection errors to these services gracefully.
2.  **No Public Access to DB/Cache:** Ensure `virlife-db`, `virlife-redis`, and `virlife-qdrant` are NOT exposed to the public internet. Only `virlife-backend` should be public.
3.  **Migrations:** Database schema changes (Alembic) should run as part of the build process or a separate init command, ensuring the DB is always in sync with the code.
