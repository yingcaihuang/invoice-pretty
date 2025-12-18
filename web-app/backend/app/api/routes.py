"""
API routes for the Web Invoice Processor.

This module defines the API endpoints for file upload, task management,
and file download operations.
"""

from fastapi import APIRouter

# Create API router
api_router = APIRouter(prefix="/api", tags=["api"])

# Import route modules
from .upload import upload_router
from .tasks import tasks_router
from .download import download_router
from .cleanup import cleanup_router

# Add route modules to main router
api_router.include_router(upload_router)
api_router.include_router(tasks_router)
api_router.include_router(download_router)
api_router.include_router(cleanup_router)