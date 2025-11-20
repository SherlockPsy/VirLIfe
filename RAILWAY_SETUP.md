# RAILWAY SETUP GUIDE

This document defines the required Railway services and environment variables for the Virtual World Backend.

## PHASE 1–8 (CURRENT REQUIREMENTS)

For the initial build and deployment (up to Phase 8), you need:

### 1. Services

*   **PostgreSQL Database**
    *   Service Name: `virlife-db` (or similar)
    *   Image: Standard Postgres image
    *   Resources: Default is sufficient for dev.

*   **Backend Service**
    *   Service Name: `virlife-backend`
    *   Source: This GitHub repository
    *   Build Command: `pip install -r requirements.txt` (Railway detects this automatically)
    *   Start Command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT` (Defined in `Procfile`)

### 2. Environment Variables (Backend Service)

These variables must be set in the `virlife-backend` service settings on Railway.

| Variable | Description | Required? | Example Value |
| :--- | :--- | :--- | :--- |
| `DATABASE_URL` | Connection string for the Postgres DB. | **YES** | `postgresql+asyncpg://user:pass@host:port/dbname` |
| `ENVIRONMENT` | Execution environment. | **YES** | `production` |
| `APP_NAME` | Name of the application. | No | `VirLife Backend` |
| `PORT` | Provided automatically by Railway. | **YES** | `8080` |

**Note on `DATABASE_URL`:**
Railway often provides `DATABASE_URL` automatically if you link the Postgres service to the Backend service. Ensure it uses the `postgresql+asyncpg://` scheme. If Railway provides `postgres://`, you may need to manually override it or handle the string replacement in `settings.py` (we will handle this in code to be safe).

---

## PHASE 9 (FUTURE REQUIREMENTS)

**DO NOT PROVISION THESE YET.**
These are strictly for Phase 9 (Optimization & Memory).

### 1. Services

*   **Redis**
    *   Role: Non-authoritative cache.
    *   Service Name: `virlife-redis`

*   **Qdrant**
    *   Role: Vector database for memory retrieval.
    *   Service Name: `virlife-qdrant`
    *   Image: `qdrant/qdrant`

### 2. Environment Variables

| Variable | Description |
| :--- | :--- |
| `REDIS_URL` | Connection string for Redis. |
| `QDRANT_URL` | URL for Qdrant API. |
| `QDRANT_API_KEY` | API Key for Qdrant (if auth enabled). |
| `VENICE_API_KEY` | API Key for LLM Provider (Venice). |
| `COGNITION_MODEL_ID` | Model ID for cognition (e.g., `llama-3.1-405b`). |
| `RENDERER_MODEL_ID` | Model ID for rendering. |

---

## DEPLOYMENT INSTRUCTIONS

1.  **Push** this repository to GitHub.
2.  **Create New Project** on Railway.
3.  **Add Database:** Select PostgreSQL.
4.  **Add Service:** Select "GitHub Repo" and choose `VirLIfe`.
5.  **Variables:** Go to the Backend service -> Variables.
    *   Railway usually adds `DATABASE_URL` automatically when you add Postgres.
    *   Add `ENVIRONMENT=production`.
6.  **Deploy:** Railway will build and deploy automatically.
