import httpx
import json
import asyncio
from typing import Set
from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from backend.config.settings import settings
from backend.persistence.database import Base, AsyncSessionLocal
from backend.persistence.models import *  # noqa
from backend.gateway.handlers import GatewayAPI
from backend.gateway.routes import router as gateway_router
from backend.gateway.models import (
    UserActionRequest, UserActionResponse,
    WorldAdvanceRequest, WorldAdvanceResponse,
    RenderRequest, RenderResponse, StatusResponse
)
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Phase 9: Import caching and memory services for health checks
try:
    from backend.caching import get_redis_service
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

try:
    from backend.memory import get_qdrant_service
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

app = FastAPI(title=settings.app_name)

# CORS Configuration - Allow frontend to access backend
# Per Plan.md Phase 10.9: Frontend needs to make cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://virlife-frontend-production.up.railway.app",
        "http://localhost:3000",
        "http://localhost:5173",  # Vite dev server
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include gateway router with /api/v1 prefix
app.include_router(gateway_router)

# WebSocket connection manager
class ConnectionManager:
    """Manages WebSocket connections for real-time timeline events."""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.add(websocket)
        print(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        self.active_connections.discard(websocket)
        print(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific WebSocket connection."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            print(f"Error sending WebSocket message: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: dict):
        """Broadcast a message to all connected WebSocket clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error broadcasting to WebSocket: {e}")
                disconnected.append(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)

manager = ConnectionManager()

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
        "redis": "not_configured",
        "qdrant": "not_configured",
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
    
    # Check Redis (Phase 9)
    if REDIS_AVAILABLE and settings.redis_url:
        try:
            redis_service = await get_redis_service()
            if redis_service and await redis_service.is_available():
                checks["redis"] = "ok"
            else:
                checks["redis"] = "unavailable"
        except Exception as e:
            checks["redis"] = f"error: {str(e)}"
    
    # Check Qdrant (Phase 9)
    if QDRANT_AVAILABLE and settings.qdrant_url:
        try:
            qdrant_service = await get_qdrant_service()
            if qdrant_service and await qdrant_service.is_available():
                checks["qdrant"] = "ok"
            else:
                checks["qdrant"] = "unavailable"
        except Exception as e:
            checks["qdrant"] = f"error: {str(e)}"
    
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

# ============================================================================
# WEBSOCKET ENDPOINT (PHASE 10)
# ============================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, user_id: int = None):
    """
    WebSocket endpoint for real-time timeline events.
    
    Per Plan.md Phase 10.3:
    - Streams timeline events to connected clients
    - Handles reconnection logic
    - Broadcasts renderer output as events occur
    
    Query parameters:
    - user_id: User ID for filtering events (optional)
    """
    # Check origin for WebSocket (CORS middleware doesn't apply to WebSockets)
    # Railway proxy may not send origin header, so we're lenient here
    origin = websocket.headers.get("origin")
    allowed_origins = [
        "https://virlife-frontend-production.up.railway.app",
        "http://localhost:3000",
        "http://localhost:5173",
    ]
    
    # Allow connection if:
    # 1. Origin is in allowed list
    # 2. Origin is not set (Railway proxy or direct connection)
    # 3. Origin contains "railway" or "localhost" (development)
    if origin:
        if origin not in allowed_origins:
            # Still allow if it's a Railway or localhost origin (for development/proxy)
            if not any(allowed in origin.lower() for allowed in ["railway", "localhost", "127.0.0.1"]):
                # Reject only if origin is explicitly set and doesn't match any allowed pattern
                print(f"WebSocket connection rejected: origin={origin}")
                await websocket.close(code=1008, reason="Origin not allowed")
                return
    
    # Accept WebSocket connection
    await manager.connect(websocket)
    
    try:
        # Send initial connection confirmation
        await manager.send_personal_message({
            "type": "connected",
            "timestamp": int(asyncio.get_event_loop().time() * 1000),
            "message": "WebSocket connected"
        }, websocket)
        
        # Keep connection alive and handle incoming messages
        while True:
            # Wait for messages from client (heartbeat, etc.)
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                # Handle client messages if needed
                # For now, just keep connection alive
            except asyncio.TimeoutError:
                # Send heartbeat to keep connection alive
                await manager.send_personal_message({
                    "type": "heartbeat",
                    "timestamp": int(asyncio.get_event_loop().time() * 1000)
                }, websocket)
            except WebSocketDisconnect:
                break
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)
