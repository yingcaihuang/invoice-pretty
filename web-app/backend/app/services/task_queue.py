"""
Task queue manager for handling asynchronous PDF processing.

This module provides a high-level interface for managing Celery tasks,
including task enqueueing, status monitoring, and queue management.
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from celery.result import AsyncResult
from celery.exceptions import WorkerLostError, Retry

from ..core.celery import celery_app
from ..models.data_models import Task, TaskStatus
from .task_storage import TaskStorageInterface
from .tasks import process_pdf_files_task, cleanup_expired_tasks_task, health_check_task

logger = logging.getLogger(__name__)


class TaskQueueManager:
    """
    High-level interface for managing the task queue system.
    
    Provides methods for enqueueing tasks, monitoring progress,
    and managing queue operations with proper error handling.
    """
    
    def __init__(self, redis_url: str, storage_path: str):
        """
        Initialize the task queue manager.
        
        Args:
            redis_url: Redis connection URL
            storage_path: Base storage path for files
        """
        self.redis_url = redis_url
        self.storage_path = storage_path
        self.task_storage = TaskStorageInterface(redis_url=redis_url, db=0)
    
    def enqueue_task(self, task_id: str, session_id: str) -> bool:
        """
        Enqueue a task for asynchronous processing.
        
        Args:
            task_id: Unique task identifier
            session_id: Session that owns the task
            
        Returns:
            True if task was enqueued successfully, False otherwise
        """
        try:
            # Verify task exists and is in correct state
            task = self.task_storage.get_task(task_id)
            if not task:
                logger.error(f"Cannot enqueue non-existent task {task_id}")
                return False
            
            if task.status != TaskStatus.QUEUED:
                logger.error(f"Cannot enqueue task {task_id} in state {task.status}")
                return False
            
            if task.session_id != session_id:
                logger.error(f"Task {task_id} belongs to different session")
                return False
            
            # Enqueue the Celery task
            celery_result = process_pdf_files_task.delay(
                task_id=task_id,
                session_id=session_id,
                redis_url=self.redis_url,
                storage_path=self.storage_path
            )
            
            # Store Celery task ID for monitoring
            task.celery_task_id = celery_result.id
            task.updated_at = datetime.utcnow()
            
            if not self.task_storage.update_task(task):
                logger.error(f"Failed to update task {task_id} with Celery task ID")
                # Try to revoke the Celery task
                celery_result.revoke(terminate=True)
                return False
            
            logger.info(f"Enqueued task {task_id} with Celery ID {celery_result.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to enqueue task {task_id}: {e}")
            return False
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive task status including Celery state.
        
        Args:
            task_id: Unique task identifier
            
        Returns:
            Dictionary with task status information, None if task not found
        """
        try:
            # Get task from storage
            task = self.task_storage.get_task(task_id)
            if not task:
                return None
            
            status_info = {
                "taskId": task_id,  # Frontend expects camelCase
                "status": task.status.value,
                "progress": task.progress,
                "createdAt": task.created_at.isoformat(),  # Frontend expects camelCase
                "updatedAt": task.updated_at.isoformat(),  # Frontend expects camelCase
                "sessionId": task.session_id,
                "inputFiles": task.input_files,
                "outputFiles": task.output_files
            }
            
            # Add completion time if available
            if task.completed_at:
                status_info["completedAt"] = task.completed_at.isoformat()  # Frontend expects camelCase
            
            # Add error message for failed tasks
            if task.error_message:
                status_info["message"] = task.error_message  # Frontend expects 'message' field
            
            # Get Celery task status if available
            if hasattr(task, 'celery_task_id') and task.celery_task_id:
                try:
                    celery_result = AsyncResult(task.celery_task_id, app=celery_app)
                    status_info["celery_state"] = celery_result.state
                    
                    if celery_result.info:
                        if isinstance(celery_result.info, dict):
                            status_info["celery_info"] = celery_result.info
                        else:
                            status_info["celery_info"] = {"message": str(celery_result.info)}
                    
                except Exception as celery_error:
                    logger.debug(f"Could not get Celery status for task {task_id}: {celery_error}")
                    status_info["celery_state"] = "UNKNOWN"
            
            return status_info
            
        except Exception as e:
            logger.error(f"Failed to get task status {task_id}: {e}")
            return None
    
    def cancel_task(self, task_id: str, session_id: str) -> bool:
        """
        Cancel a running or queued task.
        
        Args:
            task_id: Unique task identifier
            session_id: Session that owns the task
            
        Returns:
            True if task was cancelled successfully, False otherwise
        """
        try:
            # Get task from storage
            task = self.task_storage.get_task(task_id)
            if not task:
                logger.error(f"Cannot cancel non-existent task {task_id}")
                return False
            
            # Verify session ownership
            if task.session_id != session_id:
                logger.error(f"Cannot cancel task {task_id}: belongs to different session")
                return False
            
            # Only cancel tasks that are queued or processing
            if task.status not in [TaskStatus.QUEUED, TaskStatus.PROCESSING]:
                logger.warning(f"Cannot cancel task {task_id} in state {task.status}")
                return False
            
            # Revoke Celery task if it exists
            if hasattr(task, 'celery_task_id') and task.celery_task_id:
                try:
                    celery_result = AsyncResult(task.celery_task_id, app=celery_app)
                    celery_result.revoke(terminate=True)
                    logger.info(f"Revoked Celery task {task.celery_task_id} for task {task_id}")
                except Exception as celery_error:
                    logger.warning(f"Failed to revoke Celery task: {celery_error}")
            
            # Update task status to failed with cancellation message
            success = self.task_storage.update_task_status(
                task_id,
                TaskStatus.FAILED,
                error_message="Task cancelled by user"
            )
            
            if success:
                logger.info(f"Cancelled task {task_id}")
                return True
            else:
                logger.error(f"Failed to update cancelled task {task_id}")
                return False
            
        except Exception as e:
            logger.error(f"Failed to cancel task {task_id}: {e}")
            return False
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the task queue.
        
        Returns:
            Dictionary with queue statistics
        """
        try:
            # Get Celery queue statistics
            inspect = celery_app.control.inspect()
            
            stats = {
                "timestamp": datetime.utcnow().isoformat(),
                "queue_healthy": True,
                "active_tasks": 0,
                "scheduled_tasks": 0,
                "workers": []
            }
            
            try:
                # Get active tasks
                active = inspect.active()
                if active:
                    stats["active_tasks"] = sum(len(tasks) for tasks in active.values())
                    stats["workers"] = list(active.keys())
                
                # Get scheduled tasks
                scheduled = inspect.scheduled()
                if scheduled:
                    stats["scheduled_tasks"] = sum(len(tasks) for tasks in scheduled.values())
                
            except Exception as inspect_error:
                logger.warning(f"Could not get detailed queue stats: {inspect_error}")
                stats["queue_healthy"] = False
                stats["error"] = str(inspect_error)
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get queue stats: {e}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "queue_healthy": False,
                "error": str(e)
            }
    
    def schedule_cleanup(self) -> bool:
        """
        Schedule a cleanup task to run.
        
        Returns:
            True if cleanup was scheduled successfully, False otherwise
        """
        try:
            result = cleanup_expired_tasks_task.delay(
                redis_url=self.redis_url,
                storage_path=self.storage_path
            )
            
            logger.info(f"Scheduled cleanup task with ID {result.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to schedule cleanup task: {e}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check of the task queue system.
        
        Returns:
            Dictionary with health check results
        """
        try:
            # Test basic Celery connectivity
            result = health_check_task.delay()
            
            # Wait for result with timeout
            health_result = result.get(timeout=10)
            
            return {
                "healthy": True,
                "timestamp": datetime.utcnow().isoformat(),
                "celery_result": health_result,
                "message": "Task queue is healthy"
            }
            
        except Exception as e:
            logger.error(f"Task queue health check failed: {e}")
            return {
                "healthy": False,
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "message": "Task queue is unhealthy"
            }
    
    def retry_failed_task(self, task_id: str, session_id: str) -> bool:
        """
        Retry a failed task.
        
        Args:
            task_id: Unique task identifier
            session_id: Session that owns the task
            
        Returns:
            True if task was requeued successfully, False otherwise
        """
        try:
            # Get task from storage
            task = self.task_storage.get_task(task_id)
            if not task:
                logger.error(f"Cannot retry non-existent task {task_id}")
                return False
            
            # Verify session ownership
            if task.session_id != session_id:
                logger.error(f"Cannot retry task {task_id}: belongs to different session")
                return False
            
            # Only retry failed tasks
            if task.status != TaskStatus.FAILED:
                logger.warning(f"Cannot retry task {task_id} in state {task.status}")
                return False
            
            # Reset task state
            task.status = TaskStatus.QUEUED
            task.progress = 0
            task.error_message = None
            task.updated_at = datetime.utcnow()
            task.completed_at = None
            
            # Clear old Celery task ID
            if hasattr(task, 'celery_task_id'):
                delattr(task, 'celery_task_id')
            
            # Update task in storage
            if not self.task_storage.update_task(task):
                logger.error(f"Failed to reset task {task_id} for retry")
                return False
            
            # Enqueue the task again
            return self.enqueue_task(task_id, session_id)
            
        except Exception as e:
            logger.error(f"Failed to retry task {task_id}: {e}")
            return False