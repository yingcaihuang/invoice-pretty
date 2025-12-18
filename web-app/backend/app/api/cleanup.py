"""
Cleanup management API endpoints.

This module provides endpoints for managing file cleanup and maintenance operations,
including manual cleanup triggers and storage monitoring.
"""

import logging
from typing import Dict, Any

from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from ..services.tasks import cleanup_old_files_task, monitor_storage_usage_task, update_expired_task_status_task

logger = logging.getLogger(__name__)

cleanup_router = APIRouter(prefix="/cleanup", tags=["cleanup"])


@cleanup_router.post("/files")
async def trigger_file_cleanup(
    request: Request,
    background_tasks: BackgroundTasks,
    max_age_hours: int = 24
):
    """
    Manually trigger file cleanup operation.
    
    Args:
        request: FastAPI request object
        background_tasks: FastAPI background tasks
        max_age_hours: Maximum age in hours before files are deleted
        
    Returns:
        JSON response with cleanup task information
    """
    try:
        # Get file storage from app state
        file_storage = request.app.state.file_storage
        
        if not file_storage:
            raise HTTPException(
                status_code=503,
                detail="File storage service unavailable"
            )
        
        # Add cleanup task to background tasks
        background_tasks.add_task(
            cleanup_old_files_task,
            file_storage.base_path,
            max_age_hours
        )
        
        logger.info(f"Manual file cleanup triggered for files older than {max_age_hours} hours")
        
        return {
            "success": True,
            "message": f"File cleanup task started for files older than {max_age_hours} hours",
            "max_age_hours": max_age_hours
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger file cleanup: {e}")
        raise HTTPException(status_code=500, detail="Failed to trigger file cleanup")


@cleanup_router.post("/tasks")
async def trigger_task_cleanup(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Manually trigger expired task cleanup operation.
    
    Args:
        request: FastAPI request object
        background_tasks: FastAPI background tasks
        
    Returns:
        JSON response with cleanup task information
    """
    try:
        # Get services from app state
        task_storage = request.app.state.task_storage
        file_storage = request.app.state.file_storage
        
        if not task_storage or not file_storage:
            raise HTTPException(
                status_code=503,
                detail="Storage services unavailable"
            )
        
        # Add task status update to background tasks
        background_tasks.add_task(
            update_expired_task_status_task,
            task_storage.redis_url,
            str(file_storage.base_path)
        )
        
        logger.info("Manual expired task status update triggered")
        
        return {
            "success": True,
            "message": "Expired task status update started"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger task cleanup: {e}")
        raise HTTPException(status_code=500, detail="Failed to trigger task cleanup")


@cleanup_router.get("/storage/usage")
async def get_storage_usage(request: Request):
    """
    Get current storage usage statistics.
    
    Args:
        request: FastAPI request object
        
    Returns:
        JSON response with storage usage information
    """
    try:
        # Get file storage from app state
        file_storage = request.app.state.file_storage
        
        if not file_storage:
            raise HTTPException(
                status_code=503,
                detail="File storage service unavailable"
            )
        
        # Get storage usage statistics
        usage_stats = file_storage.get_storage_usage()
        
        # Convert bytes to human-readable format
        def format_bytes(bytes_value: int) -> Dict[str, Any]:
            """Convert bytes to human-readable format."""
            for unit in ['B', 'KB', 'MB', 'GB']:
                if bytes_value < 1024.0:
                    return {
                        "bytes": bytes_value,
                        "formatted": f"{bytes_value:.1f} {unit}"
                    }
                bytes_value /= 1024.0
            return {
                "bytes": bytes_value * 1024,
                "formatted": f"{bytes_value:.1f} TB"
            }
        
        formatted_usage = {
            key: format_bytes(value) 
            for key, value in usage_stats.items()
        }
        
        logger.debug(f"Storage usage retrieved: {usage_stats}")
        
        return {
            "success": True,
            "usage_stats": usage_stats,
            "formatted_usage": formatted_usage
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get storage usage: {e}")
        raise HTTPException(status_code=500, detail="Failed to get storage usage")


@cleanup_router.post("/storage/monitor")
async def trigger_storage_monitoring(
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Manually trigger storage usage monitoring.
    
    Args:
        request: FastAPI request object
        background_tasks: FastAPI background tasks
        
    Returns:
        JSON response with monitoring task information
    """
    try:
        # Get file storage from app state
        file_storage = request.app.state.file_storage
        
        if not file_storage:
            raise HTTPException(
                status_code=503,
                detail="File storage service unavailable"
            )
        
        # Add monitoring task to background tasks
        background_tasks.add_task(
            monitor_storage_usage_task,
            str(file_storage.base_path)
        )
        
        logger.info("Manual storage monitoring triggered")
        
        return {
            "success": True,
            "message": "Storage monitoring task started"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger storage monitoring: {e}")
        raise HTTPException(status_code=500, detail="Failed to trigger storage monitoring")


@cleanup_router.get("/status")
async def get_cleanup_status(request: Request):
    """
    Get status of cleanup and maintenance operations.
    
    Args:
        request: FastAPI request object
        
    Returns:
        JSON response with cleanup status information
    """
    try:
        # Get services from app state
        task_storage = request.app.state.task_storage
        file_storage = request.app.state.file_storage
        
        if not task_storage or not file_storage:
            raise HTTPException(
                status_code=503,
                detail="Storage services unavailable"
            )
        
        # Get basic statistics
        usage_stats = file_storage.get_storage_usage()
        
        # Check service health
        redis_healthy = task_storage.health_check()
        
        status_info = {
            "services": {
                "redis": "healthy" if redis_healthy else "unhealthy",
                "file_storage": "healthy"
            },
            "storage": {
                "total_size_mb": round(usage_stats["total_size"] / (1024 * 1024), 2),
                "uploads_size_mb": round(usage_stats["uploads_size"] / (1024 * 1024), 2),
                "outputs_size_mb": round(usage_stats["outputs_size"] / (1024 * 1024), 2),
                "temp_size_mb": round(usage_stats["temp_size"] / (1024 * 1024), 2)
            },
            "cleanup": {
                "automatic_cleanup_enabled": True,
                "cleanup_interval_hours": 6,
                "file_retention_hours": 24
            }
        }
        
        logger.debug(f"Cleanup status retrieved: {status_info}")
        
        return {
            "success": True,
            "status": status_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get cleanup status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get cleanup status")