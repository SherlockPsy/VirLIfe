import httpx
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from backend.config.settings import settings
from backend.persistence.database import Base, AsyncSessionLocal
from backend.persistence.models import *  # noqa
from backend.gateway.handlers import GatewayAPI
from backend.gateway.models import (
    UserActionRequest, UserActionResponse,
    WorldAdvanceRequest, WorldAdvanceResponse,
    RenderRequest, RenderResponse, StatusResponse
)
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

async def get_db():
    """Get database session for dependency injection."""
    async with AsyncSessionLocal() as session:
        yield session

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
    """Health check endpoint - Railway uses this to determine if container is healthy."""
    checks = {
        "status": "ok",
        "environment": settings.environment
    }
    
    # Check database connectivity (Railway requires this)
    try:
        engine = await get_db_engine()
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {str(e)}"
        raise HTTPException(status_code=503, detail=f"Database unavailable: {str(e)}")
    
    return checks

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

# ============================================================================
# GATEWAY API ENDPOINTS (PHASE 7)
# ============================================================================

gateway_api = GatewayAPI()

@app.post("/user/action", response_model=UserActionResponse)
async def user_action(
    request: UserActionRequest,
    db: AsyncSession = Depends(get_db)
):
    """User performs an action in the world."""
    return await gateway_api.user_action(request, db)

@app.post("/world/advance", response_model=WorldAdvanceResponse)
async def world_advance(
    request: WorldAdvanceRequest,
    db: AsyncSession = Depends(get_db)
):
    """Advance world time by N ticks."""
    return await gateway_api.world_advance(request, db)

@app.get("/render", response_model=RenderResponse)
async def render(
    user_id: int,
    pov: str = "second_person",
    db: AsyncSession = Depends(get_db)
):
    """Render perceptual experience for user."""
    request = RenderRequest(user_id=user_id, pov=pov)
    return await gateway_api.render(request, db)

@app.get("/status", response_model=StatusResponse)
async def status(db: AsyncSession = Depends(get_db)):
    """Get system status."""
    return await gateway_api.status(db)
