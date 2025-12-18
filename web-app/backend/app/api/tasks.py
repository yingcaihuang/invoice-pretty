"""
Task management API endpoints.

This module handles task status queries, progress tracking,
and task management operations with session-based access control.
"""

import logging
import os
from typing import List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Request, HTTPException, Path
from fastapi.responses import JSONResponse

from ..models.data_models import Task, TaskStatus
from ..services.pdf_processor import WebPDFProcessor
from ..services.file_handler import WebFileHandler
from ..services.task_queue import TaskQueueManager
from ..utils.timezone import beijing_now

logger = logging.getLogger(__name__)

tasks_router = APIRouter(prefix="/task", tags=["tasks"])


@tasks_router.get("/{task_id}/status")
async def get_task_status(
    request: Request,
    task_id: str = Path(..., description="Unique task identifier")
):
    """
    Get the current status and progress of a task.
    
    Args:
        request: FastAPI request object (contains session info)
        task_id: Unique task identifier
        
    Returns:
        JSON response with task status and details
    """
    try:
        # Get services from app state
        task_storage = request.app.state.task_storage
        file_storage = request.app.state.file_storage
        
        # Get session ID from middleware
        session_id = request.state.session_id
        
        # Retrieve task
        task = task_storage.get_task(task_id)
        if task is None:
            raise HTTPException(
                status_code=404, 
                detail=f"Task {task_id} not found"
            )
        
        # Verify session ownership
        if task.session_id != session_id:
            raise HTTPException(
                status_code=403,
                detail="Access denied: Task belongs to different session"
            )
        
        # Get enhanced status from task queue if available
        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            storage_path = os.getenv("STORAGE_PATH", "./storage")
            task_queue = TaskQueueManager(redis_url=redis_url, storage_path=storage_path)
            
            enhanced_status = task_queue.get_task_status(task_id)
            if enhanced_status:
                response_data = enhanced_status
            else:
                # Fallback to basic task data
                response_data = {
                    "task_id": task.task_id,
                    "status": task.status.value,
                    "progress": task.progress,
                    "created_at": task.created_at.isoformat(),
                    "updated_at": task.updated_at.isoformat(),
                    "file_count": len(task.input_files)
                }
        except Exception as queue_error:
            logger.warning(f"Could not get enhanced status from queue: {queue_error}")
            # Fallback to basic task data
            response_data = {
                "taskId": task.task_id,  # Frontend expects camelCase
                "status": task.status.value,
                "progress": task.progress,
                "createdAt": task.created_at.isoformat(),  # Frontend expects camelCase
                "updatedAt": task.updated_at.isoformat(),
                "fileCount": len(task.input_files)
            }
        
        # Add completion timestamp if available (only if not already in response_data)
        if task.completed_at and "completedAt" not in response_data:
            response_data["completedAt"] = task.completed_at.isoformat()
        
        # Add error message for failed tasks (only if not already in response_data)
        if task.status == TaskStatus.FAILED and task.error_message and "message" not in response_data:
            response_data["message"] = task.error_message
        
        # Add download URLs for completed tasks
        if task.status == TaskStatus.COMPLETED and task.output_files:
            download_urls = []
            for output_file in task.output_files:
                # Extract filename from path
                filename = output_file.split("/")[-1]
                # Remove task_id prefix from filename
                if filename.startswith(f"{task_id}_"):
                    display_filename = filename[len(f"{task_id}_"):]
                else:
                    display_filename = filename
                
                # Verify file still exists
                logger.info(f"Verifying file access - Task: {task_id}, Original: {filename}, Display: {display_filename}")
                if file_storage.verify_file_access(session_id, task_id, display_filename, "output"):
                    # URL encode the filename to handle special characters
                    from urllib.parse import quote
                    encoded_filename = quote(display_filename)
                    download_url = f"/api/download/{task_id}/{encoded_filename}"
                    logger.info(f"Generated download URL: {download_url}")
                    download_urls.append({
                        "filename": display_filename,
                        "url": download_url
                    })
                else:
                    logger.warning(f"File access verification failed - Task: {task_id}, Display: {display_filename}")
            
            response_data["downloadUrls"] = [url["url"] for url in download_urls]  # Frontend expects array of URLs
        
        logger.debug(f"Retrieved status for task {task_id}: {task.status.value}")
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task status {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve task status")


@tasks_router.get("/")
async def get_session_tasks(
    request: Request,
    status: Optional[str] = None
):
    """
    Get all tasks for the current session.
    
    Args:
        request: FastAPI request object (contains session info)
        status: Optional status filter
        
    Returns:
        JSON response with list of tasks
    """
    try:
        # Get services from app state
        task_storage = request.app.state.task_storage
        
        # Get session ID from middleware
        session_id = request.state.session_id
        
        # Retrieve all tasks for session
        tasks = task_storage.get_session_tasks(session_id)
        
        # Filter by status if provided
        if status:
            try:
                status_filter = TaskStatus(status.lower())
                tasks = [task for task in tasks if task.status == status_filter]
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid status filter: {status}"
                )
        
        # Prepare response data
        task_list = []
        for task in tasks:
            task_data = {
                "task_id": task.task_id,
                "status": task.status.value,
                "progress": task.progress,
                "created_at": task.created_at.isoformat(),
                "updated_at": task.updated_at.isoformat(),
                "file_count": len(task.input_files)
            }
            
            if task.completed_at:
                task_data["completed_at"] = task.completed_at.isoformat()
            
            if task.status == TaskStatus.FAILED and task.error_message:
                task_data["error_message"] = task.error_message
            
            task_list.append(task_data)
        
        # Sort by creation time (newest first)
        task_list.sort(key=lambda x: x["created_at"], reverse=True)
        
        logger.debug(f"Retrieved {len(task_list)} tasks for session {session_id}")
        return {
            "tasks": task_list,
            "total_count": len(task_list),
            "session_id": session_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session tasks: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve tasks")


@tasks_router.delete("/{task_id}")
async def delete_task(
    request: Request,
    task_id: str = Path(..., description="Unique task identifier")
):
    """
    Delete a task and its associated files.
    
    Args:
        request: FastAPI request object (contains session info)
        task_id: Unique task identifier
        
    Returns:
        JSON response confirming deletion
    """
    try:
        # Get services from app state
        task_storage = request.app.state.task_storage
        file_storage = request.app.state.file_storage
        
        # Get session ID from middleware
        session_id = request.state.session_id
        
        # Retrieve task to verify ownership
        task = task_storage.get_task(task_id)
        if task is None:
            raise HTTPException(
                status_code=404,
                detail=f"Task {task_id} not found"
            )
        
        # Verify session ownership
        if task.session_id != session_id:
            raise HTTPException(
                status_code=403,
                detail="Access denied: Task belongs to different session"
            )
        
        # Clean up files
        file_cleanup_success = file_storage.cleanup_task_files(session_id, task_id)
        if not file_cleanup_success:
            logger.warning(f"File cleanup failed for task {task_id}")
        
        # Delete task from storage
        task_deleted = task_storage.delete_task(task_id, session_id)
        if not task_deleted:
            raise HTTPException(
                status_code=500,
                detail="Failed to delete task"
            )
        
        logger.info(f"Deleted task {task_id} for session {session_id}")
        return {
            "message": f"Task {task_id} deleted successfully",
            "task_id": task_id,
            "files_cleaned": file_cleanup_success
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete task {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete task")


@tasks_router.post("/{task_id}/process")
async def process_task_sync(
    request: Request,
    task_id: str = Path(..., description="Unique task identifier")
):
    """
    Process a task synchronously (temporary endpoint for testing).
    
    This endpoint processes PDF files immediately and returns results.
    It's intended for testing and will be replaced by async processing.
    
    Args:
        request: FastAPI request object (contains session info)
        task_id: Unique task identifier
        
    Returns:
        JSON response with processing results
    """
    try:
        # Get services from app state
        task_storage = request.app.state.task_storage
        file_storage = request.app.state.file_storage
        
        # Get session ID from middleware
        session_id = request.state.session_id
        
        # Retrieve task
        task = task_storage.get_task(task_id)
        if task is None:
            raise HTTPException(
                status_code=404,
                detail=f"Task {task_id} not found"
            )
        
        # Verify session ownership
        if task.session_id != session_id:
            raise HTTPException(
                status_code=403,
                detail="Access denied: Task belongs to different session"
            )
        
        # Check if task is in correct state for processing
        if task.status != TaskStatus.QUEUED:
            raise HTTPException(
                status_code=400,
                detail=f"Task cannot be processed in current state: {task.status.value}"
            )
        
        # Update task status to processing
        task.status = TaskStatus.PROCESSING
        task.progress = 0
        task.updated_at = beijing_now()
        task_storage.update_task(task)
        
        logger.info(f"Starting synchronous processing for task {task_id}")
        
        # Initialize processors
        pdf_processor = WebPDFProcessor(file_storage)
        file_handler = WebFileHandler(file_storage)
        
        # Progress callback to update task status
        def progress_callback(progress: int, message: str):
            task.progress = progress
            task.updated_at = beijing_now()
            task_storage.update_task(task)
            logger.debug(f"Task {task_id} progress: {progress}% - {message}")
        
        try:
            # Get PDF files from uploaded files (including ZIP extraction)
            uploaded_filenames = [f.split("/")[-1].replace(f"{task_id}_", "") for f in task.input_files]
            pdf_files = file_handler.get_pdf_files_from_uploads(session_id, task_id, uploaded_filenames)
            
            if not pdf_files:
                raise Exception("No valid PDF files found for processing")
            
            logger.info(f"Found {len(pdf_files)} PDF files for processing")
            
            # Process invoices
            result = pdf_processor.process_invoices_async(
                task_id=task_id,
                session_id=session_id,
                input_file_paths=pdf_files,
                progress_callback=progress_callback
            )
            
            if result.success:
                # Update task as completed
                task.status = TaskStatus.COMPLETED
                task.progress = 100
                task.completed_at = beijing_now()
                task.updated_at = beijing_now()
                task.output_files = [result.output_file]
                
                # Generate download URL
                output_filename = result.output_file.split("/")[-1]
                if output_filename.startswith(f"{task_id}_"):
                    display_filename = output_filename[len(f"{task_id}_"):]
                else:
                    display_filename = output_filename
                
                # URL encode the filename to handle special characters
                from urllib.parse import quote
                encoded_filename = quote(display_filename)
                download_url = f"/api/download/{task_id}/{encoded_filename}"
                
                response_data = {
                    "task_id": task_id,
                    "status": "completed",
                    "progress": 100,
                    "processed_count": result.processed_count,
                    "total_pages": result.total_pages,
                    "download_urls": [{
                        "filename": display_filename,
                        "url": download_url
                    }],
                    "completed_at": task.completed_at.isoformat(),
                    "processing_time_seconds": (task.completed_at - task.created_at).total_seconds()
                }
                
                logger.info(f"Task {task_id} completed successfully")
                
            else:
                # Update task as failed
                error_message = "; ".join(result.errors) if result.errors else "Processing failed"
                task.status = TaskStatus.FAILED
                task.error_message = error_message
                task.updated_at = beijing_now()
                
                response_data = {
                    "task_id": task_id,
                    "status": "failed",
                    "progress": task.progress,
                    "error_message": error_message,
                    "errors": result.errors,
                    "skipped_files": result.skipped_files
                }
                
                logger.error(f"Task {task_id} failed: {error_message}")
            
            # Update task in storage
            task_storage.update_task(task)
            
            # Clean up temporary files
            file_handler.cleanup_temp_dirs()
            
            return response_data
            
        except Exception as processing_error:
            # Update task as failed
            error_message = f"Processing error: {str(processing_error)}"
            task.status = TaskStatus.FAILED
            task.error_message = error_message
            task.updated_at = beijing_now()
            task_storage.update_task(task)
            
            # Clean up temporary files
            file_handler.cleanup_temp_dirs()
            
            logger.error(f"Task {task_id} processing failed: {error_message}")
            raise HTTPException(status_code=500, detail=error_message)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process task {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to process task")


@tasks_router.get("/statistics")
async def get_task_statistics(request: Request):
    """
    Get task statistics for the current session.
    
    Args:
        request: FastAPI request object (contains session info)
        
    Returns:
        JSON response with task statistics
    """
    try:
        # Get services from app state
        task_storage = request.app.state.task_storage
        
        # Get session ID from middleware
        session_id = request.state.session_id
        
        # Retrieve all tasks for session
        tasks = task_storage.get_session_tasks(session_id)
        
        # Calculate statistics
        total_tasks = len(tasks)
        status_counts = {}
        for status in TaskStatus:
            status_counts[status.value] = len([t for t in tasks if t.status == status])
        
        # Calculate average processing time for completed tasks
        completed_tasks = [t for t in tasks if t.status == TaskStatus.COMPLETED and t.completed_at]
        avg_processing_time = 0
        if completed_tasks:
            total_time = sum(
                (t.completed_at - t.created_at).total_seconds() 
                for t in completed_tasks
            )
            avg_processing_time = total_time / len(completed_tasks)
        
        statistics = {
            "total_tasks": total_tasks,
            "status_counts": status_counts,
            "avg_processing_time_seconds": avg_processing_time,
            "session_id": session_id
        }
        
        logger.debug(f"Generated task statistics for session {session_id}")
        return statistics
        
    except Exception as e:
        logger.error(f"Failed to get task statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve task statistics")


@tasks_router.post("/{task_id}/start")
async def start_async_processing(
    request: Request,
    task_id: str = Path(..., description="Unique task identifier")
):
    """
    Start asynchronous processing for a queued task.
    
    Args:
        request: FastAPI request object (contains session info)
        task_id: Unique task identifier
        
    Returns:
        JSON response confirming task was queued for processing
    """
    try:
        # Get services from app state
        task_storage = request.app.state.task_storage
        
        # Get session ID from middleware
        session_id = request.state.session_id
        
        # Retrieve task to verify ownership and state
        task = task_storage.get_task(task_id)
        if task is None:
            raise HTTPException(
                status_code=404,
                detail=f"Task {task_id} not found"
            )
        
        # Verify session ownership
        if task.session_id != session_id:
            raise HTTPException(
                status_code=403,
                detail="Access denied: Task belongs to different session"
            )
        
        # Check if task can be processed
        if task.status != TaskStatus.QUEUED:
            raise HTTPException(
                status_code=400,
                detail=f"Task cannot be started in current state: {task.status.value}"
            )
        
        # Initialize task queue manager
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        storage_path = os.getenv("STORAGE_PATH", "./storage")
        task_queue = TaskQueueManager(redis_url=redis_url, storage_path=storage_path)
        
        # Enqueue task for processing
        if task_queue.enqueue_task(task_id, session_id):
            logger.info(f"Started async processing for task {task_id}")
            return {
                "task_id": task_id,
                "status": "processing",
                "message": "Task queued for asynchronous processing",
                "started_at": beijing_now().isoformat()
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to queue task for processing"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start async processing for task {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to start task processing")


@tasks_router.post("/{task_id}/cancel")
async def cancel_task(
    request: Request,
    task_id: str = Path(..., description="Unique task identifier")
):
    """
    Cancel a running or queued task.
    
    Args:
        request: FastAPI request object (contains session info)
        task_id: Unique task identifier
        
    Returns:
        JSON response confirming task cancellation
    """
    try:
        # Get session ID from middleware
        session_id = request.state.session_id
        
        # Initialize task queue manager
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        storage_path = os.getenv("STORAGE_PATH", "./storage")
        task_queue = TaskQueueManager(redis_url=redis_url, storage_path=storage_path)
        
        # Cancel the task
        if task_queue.cancel_task(task_id, session_id):
            logger.info(f"Cancelled task {task_id} for session {session_id}")
            return {
                "task_id": task_id,
                "status": "cancelled",
                "message": "Task cancelled successfully",
                "cancelled_at": beijing_now().isoformat()
            }
        else:
            raise HTTPException(
                status_code=400,
                detail="Failed to cancel task"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel task {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel task")


@tasks_router.post("/{task_id}/retry")
async def retry_failed_task(
    request: Request,
    task_id: str = Path(..., description="Unique task identifier")
):
    """
    Retry a failed task.
    
    Args:
        request: FastAPI request object (contains session info)
        task_id: Unique task identifier
        
    Returns:
        JSON response confirming task retry
    """
    try:
        # Get session ID from middleware
        session_id = request.state.session_id
        
        # Initialize task queue manager
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        storage_path = os.getenv("STORAGE_PATH", "./storage")
        task_queue = TaskQueueManager(redis_url=redis_url, storage_path=storage_path)
        
        # Retry the task
        if task_queue.retry_failed_task(task_id, session_id):
            logger.info(f"Retrying task {task_id} for session {session_id}")
            return {
                "task_id": task_id,
                "status": "queued",
                "message": "Task queued for retry",
                "retried_at": beijing_now().isoformat()
            }
        else:
            raise HTTPException(
                status_code=400,
                detail="Failed to retry task"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retry task {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retry task")


@tasks_router.get("/{task_id}/debug")
async def debug_task_files(
    request: Request,
    task_id: str = Path(..., description="Unique task identifier")
):
    """
    Debug endpoint to check task files and paths.
    
    Args:
        request: FastAPI request object (contains session info)
        task_id: Unique task identifier
        
    Returns:
        JSON response with debug information
    """
    try:
        # Get services from app state
        task_storage = request.app.state.task_storage
        file_storage = request.app.state.file_storage
        
        # Get session ID from middleware
        session_id = request.state.session_id
        
        # Retrieve task
        task = task_storage.get_task(task_id)
        if task is None:
            raise HTTPException(
                status_code=404,
                detail=f"Task {task_id} not found"
            )
        
        # Verify session ownership
        if task.session_id != session_id:
            raise HTTPException(
                status_code=403,
                detail="Access denied: Task belongs to different session"
            )
        
        debug_info = {
            "task_id": task_id,
            "session_id": session_id,
            "task_status": task.status.value,
            "output_files": task.output_files,
            "file_checks": []
        }
        
        # Check each output file
        for output_file in task.output_files:
            filename = output_file.split("/")[-1]
            display_filename = filename[len(f"{task_id}_"):] if filename.startswith(f"{task_id}_") else filename
            
            # Check file access
            file_access = file_storage.verify_file_access(session_id, task_id, display_filename, "output")
            file_path = file_storage.get_output_path(session_id, task_id, display_filename)
            
            file_check = {
                "original_filename": filename,
                "display_filename": display_filename,
                "file_access": file_access,
                "file_path": str(file_path) if file_path else None,
                "file_exists": file_path.exists() if file_path else False
            }
            
            debug_info["file_checks"].append(file_check)
        
        return debug_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to debug task {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to debug task")


@tasks_router.get("/queue/stats")
async def get_queue_statistics(request: Request):
    """
    Get task queue statistics.
    
    Args:
        request: FastAPI request object (contains session info)
        
    Returns:
        JSON response with queue statistics
    """
    try:
        # Initialize task queue manager
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        storage_path = os.getenv("STORAGE_PATH", "./storage")
        task_queue = TaskQueueManager(redis_url=redis_url, storage_path=storage_path)
        
        # Get queue statistics
        stats = task_queue.get_queue_stats()
        
        logger.debug("Retrieved queue statistics")
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get queue statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve queue statistics")


@tasks_router.post("/queue/health")
async def check_queue_health(request: Request):
    """
    Perform a health check of the task queue system.
    
    Args:
        request: FastAPI request object
        
    Returns:
        JSON response with health check results
    """
    try:
        # Initialize task queue manager
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        storage_path = os.getenv("STORAGE_PATH", "./storage")
        task_queue = TaskQueueManager(redis_url=redis_url, storage_path=storage_path)
        
        # Perform health check
        health_result = task_queue.health_check()
        
        status_code = 200 if health_result.get("healthy", False) else 503
        
        logger.debug(f"Queue health check: {'healthy' if health_result.get('healthy') else 'unhealthy'}")
        return JSONResponse(status_code=status_code, content=health_result)
        
    except Exception as e:
        logger.error(f"Queue health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "healthy": False,
                "error": str(e),
                "timestamp": beijing_now().isoformat()
            }
        )


@tasks_router.get("/{task_id}/progress")
async def get_task_progress(
    request: Request,
    task_id: str = Path(..., description="Unique task identifier")
):
    """
    Get real-time progress updates for a task.
    
    This endpoint provides detailed progress information including
    current percentage, processing stage, and estimated completion time.
    
    Args:
        request: FastAPI request object (contains session info)
        task_id: Unique task identifier
        
    Returns:
        JSON response with detailed progress information
    """
    try:
        # Get services from app state
        task_storage = request.app.state.task_storage
        
        # Get session ID from middleware
        session_id = request.state.session_id
        
        # Retrieve task
        task = task_storage.get_task(task_id)
        if task is None:
            raise HTTPException(
                status_code=404,
                detail=f"Task {task_id} not found"
            )
        
        # Verify session ownership
        if task.session_id != session_id:
            raise HTTPException(
                status_code=403,
                detail="Access denied: Task belongs to different session"
            )
        
        # Get enhanced progress from task queue
        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            storage_path = os.getenv("STORAGE_PATH", "./storage")
            task_queue = TaskQueueManager(redis_url=redis_url, storage_path=storage_path)
            
            enhanced_status = task_queue.get_task_status(task_id)
            if enhanced_status:
                progress_data = {
                    "task_id": task_id,
                    "progress": enhanced_status.get("progress", task.progress),
                    "status": enhanced_status.get("status", task.status.value),
                    "updated_at": enhanced_status.get("updated_at", task.updated_at.isoformat()),
                    "celery_state": enhanced_status.get("celery_state", "UNKNOWN")
                }
                
                # Add Celery progress info if available
                if "celery_info" in enhanced_status:
                    celery_info = enhanced_status["celery_info"]
                    if isinstance(celery_info, dict):
                        progress_data["stage"] = celery_info.get("message", "Processing")
                        progress_data["celery_progress"] = celery_info.get("progress", task.progress)
                        progress_data["timestamp"] = celery_info.get("timestamp")
                
            else:
                # Fallback to basic progress data
                progress_data = {
                    "task_id": task_id,
                    "progress": task.progress,
                    "status": task.status.value,
                    "updated_at": task.updated_at.isoformat(),
                    "celery_state": "UNKNOWN"
                }
                
        except Exception as queue_error:
            logger.warning(f"Could not get enhanced progress from queue: {queue_error}")
            # Fallback to basic progress data
            progress_data = {
                "task_id": task_id,
                "progress": task.progress,
                "status": task.status.value,
                "updated_at": task.updated_at.isoformat(),
                "celery_state": "UNKNOWN"
            }
        
        # Calculate estimated completion time for processing tasks
        if task.status == TaskStatus.PROCESSING and task.progress > 0:
            elapsed_time = (beijing_now() - task.created_at).total_seconds()
            estimated_total_time = elapsed_time * (100 / task.progress)
            estimated_remaining_time = estimated_total_time - elapsed_time
            
            progress_data["estimated_remaining_seconds"] = max(0, int(estimated_remaining_time))
            progress_data["estimated_completion_at"] = (
                beijing_now() + timedelta(seconds=estimated_remaining_time)
            ).isoformat()
        
        # Add processing rate information
        if task.status == TaskStatus.PROCESSING:
            elapsed_time = (beijing_now() - task.created_at).total_seconds()
            if elapsed_time > 0:
                progress_data["progress_rate_per_minute"] = (task.progress / elapsed_time) * 60
        
        logger.debug(f"Retrieved progress for task {task_id}: {task.progress}%")
        return progress_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task progress {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve task progress")