"""
FastAPI main application entry point
"""
import logging
import os
import time
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .services.session_manager import SessionManager
from .services.task_storage import TaskStorageInterface
from .services.file_storage import FileStorageManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize services with error handling
try:
    session_manager = SessionManager(
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
        db=1
    )
    task_storage = TaskStorageInterface(
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
        db=0
    )
    logger.info("Redis services initialized successfully")
except Exception as e:
    logger.warning(f"Redis services initialization failed: {e}")
    logger.warning("Application will start but Redis-dependent features will be unavailable")
    session_manager = None
    task_storage = None

file_storage = FileStorageManager(
    base_storage_path=os.getenv("STORAGE_PATH", "./storage")
)

app = FastAPI(
    title="Web Invoice Processor",
    description="Web-based PDF invoice layout processor",
    version="1.0.0"
)


class SessionMiddleware(BaseHTTPMiddleware):
    """Middleware for handling session management."""
    
    async def dispatch(self, request: Request, call_next):
        # Extract session ID from headers
        session_id = request.headers.get("X-Session-ID")
        
        # Add session info to request state
        request.state.session_id = session_id
        request.state.session_manager = session_manager
        
        # Skip session validation for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            response = await call_next(request)
            return response
        
        # Validate session for protected endpoints (only if Redis is available)
        if session_manager and request.url.path.startswith("/api/") and request.url.path not in ["/api/health", "/api/", "/api/session"]:
            # Special handling for download endpoints - they can use query parameter for session
            if request.url.path.startswith("/api/download/"):
                # Check if session is provided as query parameter (for iframe access)
                query_session = request.query_params.get("session")
                if query_session:
                    # Use query parameter session and add it to request state
                    request.state.session_id = query_session
                    session_id = query_session
                elif not session_id:
                    return JSONResponse(
                        status_code=400,
                        content={"error": True, "code": "MISSING_SESSION_ID", "message": "Session ID is required"}
                    )
            elif not session_id:
                return JSONResponse(
                    status_code=400,
                    content={"error": True, "code": "MISSING_SESSION_ID", "message": "Session ID is required"}
                )
            
            # Validate session exists and update activity
            if not session_manager.validate_session(session_id):
                # If session doesn't exist, try to create it automatically for development
                try:
                    from .models.data_models import Session
                    new_session = Session(session_id=session_id)
                    if session_manager.store_session(new_session):
                        logger.info(f"Auto-created session for development: {session_id}")
                    else:
                        return JSONResponse(
                            status_code=401,
                            content={"error": True, "code": "INVALID_SESSION", "message": "Invalid or expired session"}
                        )
                except Exception as e:
                    logger.error(f"Failed to auto-create session: {e}")
                    return JSONResponse(
                        status_code=401,
                        content={"error": True, "code": "INVALID_SESSION", "message": "Invalid or expired session"}
                    )
        
        response = await call_next(request)
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging."""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log request
        logger.info(f"Request: {request.method} {request.url.path} - Session: {request.headers.get('X-Session-ID', 'None')}")
        
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        logger.info(f"Response: {response.status_code} - Time: {process_time:.3f}s")
        
        return response


# Add custom middleware first (they execute in reverse order)
app.add_middleware(SessionMiddleware)
app.add_middleware(LoggingMiddleware)

# Configure CORS (should be last middleware added, executes first)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server
        "http://localhost:8080",  # Alternative dev port
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
        "*"  # Allow all origins for development
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler."""
    logger.warning(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "code": f"HTTP_{exc.status_code}",
            "message": exc.detail
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {type(exc).__name__}: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "code": "INTERNAL_SERVER_ERROR",
            "message": "An internal server error occurred"
        }
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Web Invoice Processor API", "version": "1.0.0"}


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check service health
        redis_healthy = False
        if task_storage and session_manager:
            redis_healthy = task_storage.health_check() and session_manager.health_check()
        
        health_status = {
            "status": "healthy" if redis_healthy else "degraded",
            "services": {
                "redis": "healthy" if redis_healthy else "unavailable",
                "file_storage": "healthy"  # File storage is always available if directories exist
            },
            "timestamp": time.time()
        }
        
        # Return 200 even if Redis is down (degraded mode)
        status_code = 200
        return JSONResponse(status_code=status_code, content=health_status)
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }
        )


@app.post("/api/session")
async def create_session():
    """Create a new session."""
    try:
        if not session_manager:
            raise HTTPException(status_code=503, detail="Session service unavailable")
            
        session = session_manager.create_session()
        logger.info(f"Created new session: {session.session_id}")
        
        return {
            "session_id": session.session_id,
            "created_at": session.created_at.isoformat(),
            "expires_in_hours": 72
        }
        
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        raise HTTPException(status_code=500, detail="Failed to create session")


# Import and include API routes
from .api.routes import api_router
app.include_router(api_router)

# Graceful shutdown handling
@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("Web Invoice Processor starting up...")
    
    # Validate configuration
    from .core.config import settings
    if not settings.validate_configuration():
        logger.warning("Configuration validation failed - some features may not work correctly")
    
    logger.info("Application startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("Web Invoice Processor shutting down...")
    
    try:
        # Close Redis connections gracefully
        if session_manager:
            await session_manager.close()
            logger.info("Session manager closed")
        
        if task_storage:
            await task_storage.close()
            logger.info("Task storage closed")
            
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
    
    logger.info("Application shutdown complete")


# Make services available to other modules
app.state.session_manager = session_manager
app.state.task_storage = task_storage
app.state.file_storage = file_storage