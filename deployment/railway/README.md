# Railway Deployment Guide

Per CompleteWork.md Phase 8 and Architecture.md.

This guide covers deploying the VirLIfe backend to Railway as a fully operational service using Postgres as the ONLY data store.

## Prerequisites

- Railway account (https://railway.app)
- GitHub repository with VirLIfe code
- Railway CLI (optional, for local testing)

## Deployment Steps

### 1. Create Railway Project

1. Log in to Railway dashboard
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your VirLIfe repository

### 2. Add Postgres Service

1. In your Railway project, click "New"
2. Select "Database" → "PostgreSQL"
3. Railway will automatically create:
   - `PGHOST`
   - `PGPORT`
   - `PGUSER`
   - `PGPASSWORD`
   - `PGDATABASE`
   - `DATABASE_URL`

### 3. Configure Environment Variables

Add the following environment variables in Railway:

**Required:**
- `VENICE_API_KEY` - Your Venice.ai API key
- `VENICE_BASE_URL` - Venice API base URL (default: https://api.venice.ai/api/v1)
- `COGNITION_MODEL_ID` - Model ID for cognition (e.g., "qwen3-4b")
- `RENDERER_MODEL_ID` - Model ID for renderer (e.g., "qwen3-4b" or "venice-uncensored")

**Optional:**
- `ENVIRONMENT` - Environment name (default: "production")
- `LOG_LEVEL` - Logging level (default: "INFO")

**Database variables are automatically set by Railway Postgres service.**

### 4. Configure Service Settings

1. Set build command (if needed):
   ```bash
   pip install -r requirements.txt
   ```

2. Set start command:
   ```bash
   uvicorn backend.main:app --host 0.0.0.0 --port $PORT
   ```

3. Railway will automatically detect the `Procfile` if present.

### 5. Deploy

1. Railway will automatically deploy on every push to main branch
2. Or trigger manual deployment from dashboard
3. Check deployment logs for any errors

### 6. Verify Deployment

1. Check health endpoint:
   ```bash
   curl https://your-app.railway.app/health
   ```

2. Check full health endpoint:
   ```bash
   curl https://your-app.railway.app/health/full
   ```

## Service Architecture

Per Architecture.md:

- **virlife-backend** (Python backend service)
  - Runs HTTP API (Gateway)
  - Hosts all backend subsystems
  - Uses Postgres for authoritative state

- **virlife-db** (Postgres service)
  - Railway-managed Postgres instance
  - Single source of truth for all state

## Phase 8 Constraints

**IMPORTANT:** Per Plan.md Phase 8:

- **NO Redis** - Must not be used before Phase 9
- **NO Qdrant** - Must not be used before Phase 9
- **Postgres ONLY** - Single authoritative data store

## Health Checks

Railway uses the `/health` endpoint to determine container health.

The endpoint checks:
- Database connectivity
- Basic service status

## Troubleshooting

### Database Connection Issues

1. Verify `DATABASE_URL` is set correctly
2. Check Postgres service is running
3. Verify network connectivity

### LLM API Issues

1. Verify `VENICE_API_KEY` is set
2. Check `VENICE_BASE_URL` is correct
3. Verify API key has proper permissions

### Deployment Failures

1. Check build logs in Railway dashboard
2. Verify `requirements.txt` is up to date
3. Check Python version in `runtime.txt`

## Migration and Data Management

Railway Postgres is the authoritative and only supported database.

**Important:** This application does NOT support SQLite or local file-based databases. All development and production environments must use PostgreSQL (via Railway or a compatible Postgres service).

For fresh deployments:
1. Railway creates a new Postgres database automatically
2. The application creates schema tables on first startup (via SQLAlchemy)
3. Use migration scripts if you have existing data to import

## Next Steps

After Phase 8 is complete and tested:
- Phase 9: Add Redis and Qdrant as optimization layers
- Phase 10: Build UI (locked until backend is complete)

## References

- [Railway Documentation](https://docs.railway.app)
- Architecture.md - System topology
- Plan.md - Phase-by-phase implementation
- MASTER_SPEC.md - Core system specification

