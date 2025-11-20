import httpx
from fastapi import FastAPI, HTTPException
from backend.config.settings import settings
from backend.persistence.database import Base
from backend.persistence.models import *  # noqa
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

app = FastAPI(title=settings.app_name)

# Lazy-load database engine
_db_engine = None

async def get_db_engine():
    global _db_engine
    if _db_engine is None:
        _db_engine = create_async_engine(
            settings.async_database_url,
            echo=False,
            pool_size=5,
            max_overflow=5,
            pool_recycle=3600,  # Recycle connections every hour
            pool_pre_ping=True  # Verify connection before using
        )
    return _db_engine

@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup."""
    try:
        print("Starting up: Initializing database tables...")
        engine = await get_db_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("Database initialization complete.")
    except Exception as e:
        print(f"ERROR during database initialization: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        # Don't fail startup, just warn

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up database connections on shutdown."""
    global _db_engine
    if _db_engine is not None:
        try:
            print("Shutting down: Closing database engine...")
            await _db_engine.dispose()
            _db_engine = None
            print("Database engine closed.")
        except Exception as e:
            print(f"ERROR during shutdown: {type(e).__name__}: {str(e)}")

@app.get("/health")
async def health_check():
    """Basic health check."""
    return {"status": "ok", "environment": settings.environment}

@app.get("/health/full")
async def health_check_full():
    """Full health check including all dependencies."""
    checks = {
        "backend": "ok",
        "database": "unknown",
        "venice_api": "unknown",
        "environment": settings.environment
    }
    
    # Check database
    try:
        engine = await get_db_engine()
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {str(e)}"
        raise HTTPException(status_code=503, detail=f"Database unavailable: {str(e)}")
    
    # Check Venice API
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{settings.venice_base_url}/models",
                headers={"Authorization": f"Bearer {settings.venice_api_key}"},
                timeout=5.0
            )
            if resp.status_code == 200:
                checks["venice_api"] = "ok"
            else:
                checks["venice_api"] = f"error: {resp.status_code}"
    except Exception as e:
        checks["venice_api"] = f"error: {str(e)}"
        raise HTTPException(status_code=503, detail=f"Venice API unavailable: {str(e)}")
    
    return checks

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "app": settings.app_name,
        "environment": settings.environment,
        "status": "running"
    }
