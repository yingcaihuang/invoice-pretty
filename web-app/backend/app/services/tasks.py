"""
Celery tasks for asynchronous PDF processing.

This module contains Celery tasks that handle PDF processing operations
asynchronously with progress reporting and error handling.
"""

import logging
import os
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from celery import current_task
from celery.exceptions import Retry

from ..core.celery import celery_app
from ..models.data_models import Task, TaskStatus
from .pdf_processor import WebPDFProcessor, ProcessResult
from .file_handler import WebFileHandler
from .file_storage import FileStorageManager
from .task_storage import TaskStorageInterface

logger = logging.getLogger(__name__)


class TaskProgressTracker:
    """Helper class for tracking and reporting task progress with monotonic guarantees."""
    
    def __init__(self, task_id: str, task_storage: TaskStorageInterface):
        self.task_id = task_id
        self.task_storage = task_storage
        self.last_progress = 0
        self.last_update_time = time.time()
        self.min_update_interval = 1.0  # Minimum seconds between updates
        self.progress_history = []  # Track progress history for debugging
        self.current_stage = "Initializing"
    
    def update_progress(self, progress: int, message: str = ""):
        """
        Update task progress with monotonic guarantees and rate limiting.
        
        Args:
            progress: Progress percentage (0-100)
            message: Optional progress message describing current stage
        """
        current_time = time.time()
        
        # Ensure progress is monotonic and within bounds
        progress = max(self.last_progress, min(100, max(0, progress)))
        
        # Update current stage if message provided
        if message:
            self.current_stage = message
        
        # Rate limit updates (except for 0% and 100%)
        should_update = (
            progress in [0, 100] or  # Always update start and completion
            current_time - self.last_update_time >= self.min_update_interval or  # Time-based
            progress - self.last_progress >= 5 or  # Significant progress change
            message != ""  # Stage change
        )
        
        if not should_update:
            return
        
        try:
            # Update task progress in storage
            success = self.task_storage.update_task_status(
                self.task_id, 
                TaskStatus.PROCESSING, 
                progress=progress
            )
            
            if success:
                # Record progress history
                self.progress_history.append({
                    'progress': progress,
                    'message': message,
                    'timestamp': current_time
                })
                
                # Keep only last 10 progress updates
                if len(self.progress_history) > 10:
                    self.progress_history = self.progress_history[-10:]
                
                self.last_progress = progress
                self.last_update_time = current_time
                
                # Update Celery task state for monitoring
                if current_task:
                    current_task.update_state(
                        state='PROGRESS',
                        meta={
                            'progress': progress,
                            'message': message or self.current_stage,
                            'timestamp': datetime.utcnow().isoformat(),
                            'stage': self.current_stage,
                            'history': self.progress_history[-3:]  # Last 3 updates
                        }
                    )
                
                logger.debug(f"Task {self.task_id} progress: {progress}% - {message or self.current_stage}")
            else:
                logger.warning(f"Failed to update progress for task {self.task_id}")
                
        except Exception as e:
            logger.error(f"Error updating progress for task {self.task_id}: {e}")
    
    def get_progress_rate(self) -> float:
        """
        Calculate current progress rate in percentage per minute.
        
        Returns:
            Progress rate as percentage per minute
        """
        if len(self.progress_history) < 2:
            return 0.0
        
        # Calculate rate based on last two updates
        recent = self.progress_history[-1]
        previous = self.progress_history[-2]
        
        time_diff = recent['timestamp'] - previous['timestamp']
        progress_diff = recent['progress'] - previous['progress']
        
        if time_diff <= 0:
            return 0.0
        
        # Convert to percentage per minute
        return (progress_diff / time_diff) * 60
    
    def estimate_completion_time(self) -> Optional[datetime]:
        """
        Estimate task completion time based on current progress rate.
        
        Returns:
            Estimated completion datetime, None if cannot estimate
        """
        if self.last_progress <= 0:
            return None
        
        rate = self.get_progress_rate()
        if rate <= 0:
            return None
        
        remaining_progress = 100 - self.last_progress
        estimated_minutes = remaining_progress / rate
        
        return datetime.utcnow() + timedelta(minutes=estimated_minutes)


@celery_app.task(bind=True, name="process_pdf_files")
def process_pdf_files_task(self, task_id: str, session_id: str, redis_url: str, storage_path: str) -> Dict[str, Any]:
    """
    Celery task for processing PDF files asynchronously.
    
    Args:
        self: Celery task instance (bound)
        task_id: Unique task identifier
        session_id: Session that owns the task
        redis_url: Redis connection URL for task storage
        storage_path: Base storage path for files
        
    Returns:
        Dictionary with processing results
    """
    start_time = time.time()
    logger.info(f"Starting async processing for task {task_id}")
    
    # Initialize services
    task_storage = TaskStorageInterface(redis_url=redis_url, db=0)
    file_storage = FileStorageManager(base_storage_path=storage_path)
    progress_tracker = TaskProgressTracker(task_id, task_storage)
    
    try:
        # Get task from storage
        task = task_storage.get_task(task_id)
        if not task:
            raise Exception(f"Task {task_id} not found in storage")
        
        # Verify task belongs to correct session
        if task.session_id != session_id:
            raise Exception(f"Task {task_id} belongs to different session")
        
        # Check if task is in correct state
        if task.status != TaskStatus.QUEUED:
            raise Exception(f"Task {task_id} is not in queued state: {task.status}")
        
        # Update task status to processing
        progress_tracker.update_progress(0, "Initializing processing")
        task_storage.update_task_status(task_id, TaskStatus.PROCESSING, progress=0)
        
        # Initialize processors
        pdf_processor = WebPDFProcessor(file_storage)
        file_handler = WebFileHandler(file_storage)
        
        # Progress callback for PDF processor
        def progress_callback(progress: int, message: str):
            progress_tracker.update_progress(progress, message)
        
        # Get PDF files from uploaded files (including ZIP extraction)
        progress_tracker.update_progress(10, "Extracting and validating files")
        
        uploaded_filenames = [
            f.split("/")[-1].replace(f"{task_id}_", "") 
            for f in task.input_files
        ]
        
        pdf_files = file_handler.get_pdf_files_from_uploads(
            session_id, task_id, uploaded_filenames
        )
        
        if not pdf_files:
            raise Exception("No valid PDF files found for processing")
        
        logger.info(f"Found {len(pdf_files)} PDF files for processing")
        progress_tracker.update_progress(20, f"Found {len(pdf_files)} PDF files")
        
        # Process invoices
        progress_tracker.update_progress(25, "Starting PDF processing")
        
        result = pdf_processor.process_invoices_async(
            task_id=task_id,
            session_id=session_id,
            input_file_paths=pdf_files,
            progress_callback=progress_callback
        )
        
        # Clean up temporary files
        file_handler.cleanup_temp_dirs()
        
        # Process results
        if result.success:
            # Update task as completed
            progress_tracker.update_progress(100, "Processing completed successfully")
            
            task_storage.update_task_status(
                task_id, 
                TaskStatus.COMPLETED, 
                progress=100
            )
            
            # Update task with output files
            task = task_storage.get_task(task_id)
            if task:
                task.output_files = [result.output_file]
                task.completed_at = datetime.utcnow()
                task_storage.update_task(task)
            
            processing_time = time.time() - start_time
            
            logger.info(f"Task {task_id} completed successfully in {processing_time:.2f}s")
            
            return {
                "success": True,
                "task_id": task_id,
                "processed_count": result.processed_count,
                "total_pages": result.total_pages,
                "output_file": result.output_file,
                "processing_time": processing_time,
                "message": "Processing completed successfully"
            }
            
        else:
            # Handle processing failure
            error_message = "; ".join(result.errors) if result.errors else "Processing failed"
            
            task_storage.update_task_status(
                task_id, 
                TaskStatus.FAILED, 
                error_message=error_message
            )
            
            processing_time = time.time() - start_time
            
            logger.error(f"Task {task_id} failed after {processing_time:.2f}s: {error_message}")
            
            return {
                "success": False,
                "task_id": task_id,
                "error_message": error_message,
                "errors": result.errors,
                "skipped_files": result.skipped_files,
                "processing_time": processing_time
            }
    
    except Exception as e:
        # Handle unexpected errors
        error_message = f"Processing error: {str(e)}"
        
        try:
            task_storage.update_task_status(
                task_id, 
                TaskStatus.FAILED, 
                error_message=error_message
            )
        except Exception as storage_error:
            logger.error(f"Failed to update task status after error: {storage_error}")
        
        # Clean up temporary files on error
        try:
            file_handler = WebFileHandler(file_storage)
            file_handler.cleanup_temp_dirs()
        except Exception as cleanup_error:
            logger.error(f"Failed to cleanup temp files: {cleanup_error}")
        
        processing_time = time.time() - start_time
        
        logger.error(f"Task {task_id} failed with exception after {processing_time:.2f}s: {e}")
        
        # Re-raise for Celery retry mechanism
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying task {task_id} (attempt {self.request.retries + 1})")
            raise self.retry(countdown=60, exc=e)
        
        return {
            "success": False,
            "task_id": task_id,
            "error_message": error_message,
            "processing_time": processing_time,
            "retries_exhausted": True
        }


@celery_app.task(name="cleanup_expired_tasks")
def cleanup_expired_tasks_task(redis_url: str, storage_path: str) -> Dict[str, Any]:
    """
    Celery task for cleaning up expired tasks and files.
    
    Args:
        redis_url: Redis connection URL
        storage_path: Base storage path for files
        
    Returns:
        Dictionary with cleanup results
    """
    logger.info("Starting expired tasks cleanup")
    start_time = time.time()
    
    try:
        # Initialize services
        task_storage = TaskStorageInterface(redis_url=redis_url, db=0)
        file_storage = FileStorageManager(base_storage_path=storage_path)
        
        # Clean up expired task references
        cleaned_tasks = task_storage.cleanup_expired_tasks()
        
        # Clean up old files (older than 24 hours)
        cleaned_files = file_storage.cleanup_old_files(max_age_hours=24)
        
        cleanup_time = time.time() - start_time
        
        logger.info(f"Cleanup completed in {cleanup_time:.2f}s: {cleaned_tasks} tasks, {cleaned_files} files")
        
        return {
            "success": True,
            "cleaned_tasks": cleaned_tasks,
            "cleaned_files": cleaned_files,
            "cleanup_time": cleanup_time
        }
        
    except Exception as e:
        cleanup_time = time.time() - start_time
        error_message = f"Cleanup failed: {str(e)}"
        
        logger.error(f"Cleanup task failed after {cleanup_time:.2f}s: {e}")
        
        return {
            "success": False,
            "error_message": error_message,
            "cleanup_time": cleanup_time
        }


@celery_app.task(name="cleanup_old_files")
def cleanup_old_files_task(storage_path: str, max_age_hours: int = 24) -> Dict[str, Any]:
    """
    Celery task for cleaning up old files and updating task status.
    
    Args:
        storage_path: Base storage path for files
        max_age_hours: Maximum age in hours before files are deleted
        
    Returns:
        Dictionary with cleanup results
    """
    logger.info(f"Starting file cleanup for files older than {max_age_hours} hours")
    start_time = time.time()
    
    try:
        # Initialize services
        file_storage = FileStorageManager(base_storage_path=storage_path)
        
        # Clean up old files
        cleanup_stats = file_storage.cleanup_old_files(max_age_hours=max_age_hours)
        
        cleanup_time = time.time() - start_time
        
        logger.info(f"File cleanup completed in {cleanup_time:.2f}s: {cleanup_stats}")
        
        return {
            "success": True,
            "cleanup_stats": cleanup_stats,
            "cleanup_time": cleanup_time,
            "max_age_hours": max_age_hours,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        cleanup_time = time.time() - start_time
        error_message = f"File cleanup failed: {str(e)}"
        
        logger.error(f"File cleanup task failed after {cleanup_time:.2f}s: {e}")
        
        return {
            "success": False,
            "error_message": error_message,
            "cleanup_time": cleanup_time,
            "timestamp": datetime.utcnow().isoformat()
        }


@celery_app.task(name="monitor_storage_usage")
def monitor_storage_usage_task(storage_path: str) -> Dict[str, Any]:
    """
    Celery task for monitoring storage usage and logging statistics.
    
    Args:
        storage_path: Base storage path to monitor
        
    Returns:
        Dictionary with storage usage statistics
    """
    logger.info("Starting storage usage monitoring")
    start_time = time.time()
    
    try:
        # Initialize file storage manager
        file_storage = FileStorageManager(base_storage_path=storage_path)
        
        # Get storage usage statistics
        usage_stats = file_storage.get_storage_usage()
        
        monitoring_time = time.time() - start_time
        
        # Convert bytes to MB for logging
        usage_mb = {
            key: round(value / (1024 * 1024), 2) 
            for key, value in usage_stats.items()
        }
        
        logger.info(f"Storage usage monitoring completed in {monitoring_time:.3f}s: {usage_mb} MB")
        
        # Log warning if storage usage is high (over 1GB total)
        if usage_stats["total_size"] > 1024 * 1024 * 1024:
            logger.warning(f"High storage usage detected: {usage_mb['total_size']} MB total")
        
        return {
            "success": True,
            "usage_stats": usage_stats,
            "usage_mb": usage_mb,
            "monitoring_time": monitoring_time,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        monitoring_time = time.time() - start_time
        error_message = f"Storage monitoring failed: {str(e)}"
        
        logger.error(f"Storage monitoring task failed after {monitoring_time:.3f}s: {e}")
        
        return {
            "success": False,
            "error_message": error_message,
            "monitoring_time": monitoring_time,
            "timestamp": datetime.utcnow().isoformat()
        }


@celery_app.task(name="update_expired_task_status")
def update_expired_task_status_task(redis_url: str, storage_path: str) -> Dict[str, Any]:
    """
    Celery task for updating status of tasks whose files have been cleaned up.
    
    This task runs after file cleanup to update task status to indicate
    files are no longer available for download.
    
    Args:
        redis_url: Redis connection URL
        storage_path: Base storage path for files
        
    Returns:
        Dictionary with update results
    """
    logger.info("Starting expired task status updates")
    start_time = time.time()
    
    try:
        # Initialize services
        task_storage = TaskStorageInterface(redis_url=redis_url, db=0)
        file_storage = FileStorageManager(base_storage_path=storage_path)
        
        updated_tasks = 0
        errors = 0
        
        # Get all session keys to find tasks
        import redis
        redis_client = redis.from_url(redis_url, db=0, decode_responses=True)
        session_keys = redis_client.keys("session:*:tasks")
        
        for session_key in session_keys:
            session_id = session_key.split(":")[1]
            task_ids = redis_client.smembers(session_key)
            
            for task_id in task_ids:
                try:
                    task = task_storage.get_task(task_id)
                    if not task or task.status != TaskStatus.COMPLETED:
                        continue
                    
                    # Check if output files still exist
                    files_exist = False
                    for output_file in task.output_files:
                        filename = output_file.split("/")[-1].replace(f"{task_id}_", "")
                        if file_storage.verify_file_access(session_id, task_id, filename, "output"):
                            files_exist = True
                            break
                    
                    # Update task status if files no longer exist
                    if not files_exist and task.status == TaskStatus.COMPLETED:
                        success = task_storage.update_task_status(
                            task_id, 
                            TaskStatus.EXPIRED,
                            error_message="Files have been automatically cleaned up after 24 hours"
                        )
                        if success:
                            updated_tasks += 1
                            logger.debug(f"Updated task {task_id} status to EXPIRED")
                        else:
                            errors += 1
                            
                except Exception as e:
                    logger.error(f"Failed to update status for task {task_id}: {e}")
                    errors += 1
        
        update_time = time.time() - start_time
        
        logger.info(f"Task status updates completed in {update_time:.2f}s: {updated_tasks} updated, {errors} errors")
        
        return {
            "success": True,
            "updated_tasks": updated_tasks,
            "errors": errors,
            "update_time": update_time,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        update_time = time.time() - start_time
        error_message = f"Task status update failed: {str(e)}"
        
        logger.error(f"Task status update failed after {update_time:.2f}s: {e}")
        
        return {
            "success": False,
            "error_message": error_message,
            "update_time": update_time,
            "timestamp": datetime.utcnow().isoformat()
        }


@celery_app.task(name="health_check")
def health_check_task() -> Dict[str, Any]:
    """
    Celery task for health checking the task queue system.
    
    Returns:
        Dictionary with health check results
    """
    try:
        return {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "worker_id": current_task.request.hostname if current_task else "unknown",
            "message": "Task queue is healthy"
        }
    except Exception as e:
        return {
            "success": False,
            "error_message": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }