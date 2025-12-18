"""
Redis-based task storage interface for the Web Invoice Processor.

This module provides a Redis-backed storage interface for managing task data,
including task creation, status updates, and retrieval operations.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import redis
from redis.exceptions import ConnectionError, RedisError

from ..models.data_models import Task, TaskStatus


logger = logging.getLogger(__name__)


class TaskStorageInterface:
    """
    Redis-based storage interface for managing task data.
    
    Provides methods for storing, retrieving, and updating task information
    with session-based isolation and automatic expiration.
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379", db: int = 0):
        """
        Initialize the task storage interface.
        
        Args:
            redis_url: Redis connection URL
            db: Redis database number to use
        """
        self.redis_url = redis_url
        self.db = db
        self._redis_client = None
        self._connect()
    
    def _connect(self) -> None:
        """Establish connection to Redis server."""
        try:
            self._redis_client = redis.from_url(
                self.redis_url,
                db=self.db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            self._redis_client.ping()
            logger.info(f"Connected to Redis at {self.redis_url}")
        except ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    def _get_task_key(self, task_id: str) -> str:
        """Generate Redis key for task data."""
        return f"task:{task_id}"
    
    def _get_session_tasks_key(self, session_id: str) -> str:
        """Generate Redis key for session task list."""
        return f"session:{session_id}:tasks"
    
    def _serialize_task(self, task: Task) -> str:
        """Serialize task object to JSON string."""
        return task.json()
    
    def _deserialize_task(self, task_data: str) -> Task:
        """Deserialize JSON string to task object."""
        return Task.parse_raw(task_data)
    
    def store_task(self, task: Task, expire_hours: int = 48) -> bool:
        """
        Store a task in Redis with automatic expiration.
        
        Args:
            task: Task object to store
            expire_hours: Hours until task expires (default: 48)
            
        Returns:
            True if task was stored successfully, False otherwise
        """
        try:
            task_key = self._get_task_key(task.task_id)
            session_tasks_key = self._get_session_tasks_key(task.session_id)
            
            # Store task data with expiration
            task_data = self._serialize_task(task)
            expire_seconds = expire_hours * 3600
            
            # Use pipeline for atomic operations
            pipe = self._redis_client.pipeline()
            pipe.setex(task_key, expire_seconds, task_data)
            pipe.sadd(session_tasks_key, task.task_id)
            pipe.expire(session_tasks_key, expire_seconds)
            pipe.execute()
            
            logger.debug(f"Stored task {task.task_id} for session {task.session_id}")
            return True
            
        except RedisError as e:
            logger.error(f"Failed to store task {task.task_id}: {e}")
            return False
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """
        Retrieve a task by ID.
        
        Args:
            task_id: Unique task identifier
            
        Returns:
            Task object if found, None otherwise
        """
        try:
            task_key = self._get_task_key(task_id)
            task_data = self._redis_client.get(task_key)
            
            if task_data is None:
                logger.debug(f"Task {task_id} not found")
                return None
            
            task = self._deserialize_task(task_data)
            logger.debug(f"Retrieved task {task_id}")
            return task
            
        except RedisError as e:
            logger.error(f"Failed to retrieve task {task_id}: {e}")
            return None
    
    def update_task(self, task: Task) -> bool:
        """
        Update an existing task in Redis.
        
        Args:
            task: Updated task object
            
        Returns:
            True if task was updated successfully, False otherwise
        """
        try:
            task_key = self._get_task_key(task.task_id)
            
            # Check if task exists
            if not self._redis_client.exists(task_key):
                logger.warning(f"Cannot update non-existent task {task.task_id}")
                return False
            
            # Update task data while preserving TTL
            task_data = self._serialize_task(task)
            ttl = self._redis_client.ttl(task_key)
            
            if ttl > 0:
                self._redis_client.setex(task_key, ttl, task_data)
            else:
                self._redis_client.set(task_key, task_data)
            
            logger.debug(f"Updated task {task.task_id}")
            return True
            
        except RedisError as e:
            logger.error(f"Failed to update task {task.task_id}: {e}")
            return False
    
    def get_session_tasks(self, session_id: str) -> List[Task]:
        """
        Retrieve all tasks for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of Task objects for the session
        """
        try:
            session_tasks_key = self._get_session_tasks_key(session_id)
            task_ids = self._redis_client.smembers(session_tasks_key)
            
            tasks = []
            for task_id in task_ids:
                task = self.get_task(task_id)
                if task is not None:
                    tasks.append(task)
                else:
                    # Clean up stale task ID from session set
                    self._redis_client.srem(session_tasks_key, task_id)
            
            logger.debug(f"Retrieved {len(tasks)} tasks for session {session_id}")
            return tasks
            
        except RedisError as e:
            logger.error(f"Failed to retrieve tasks for session {session_id}: {e}")
            return []
    
    def delete_task(self, task_id: str, session_id: str) -> bool:
        """
        Delete a task from Redis.
        
        Args:
            task_id: Task identifier to delete
            session_id: Session that owns the task
            
        Returns:
            True if task was deleted successfully, False otherwise
        """
        try:
            task_key = self._get_task_key(task_id)
            session_tasks_key = self._get_session_tasks_key(session_id)
            
            # Use pipeline for atomic operations
            pipe = self._redis_client.pipeline()
            pipe.delete(task_key)
            pipe.srem(session_tasks_key, task_id)
            result = pipe.execute()
            
            deleted = result[0] > 0  # Number of keys deleted
            logger.debug(f"Deleted task {task_id}: {deleted}")
            return deleted
            
        except RedisError as e:
            logger.error(f"Failed to delete task {task_id}: {e}")
            return False
    
    def update_task_status(self, task_id: str, status: TaskStatus, 
                          progress: Optional[int] = None, 
                          error_message: Optional[str] = None) -> bool:
        """
        Update task status and related fields with monotonic progress guarantees.
        
        Args:
            task_id: Task identifier
            status: New task status
            progress: Optional progress percentage (must be >= current progress)
            error_message: Optional error message for failed tasks
            
        Returns:
            True if status was updated successfully, False otherwise
        """
        try:
            task = self.get_task(task_id)
            if task is None:
                logger.warning(f"Cannot update status for non-existent task {task_id}")
                return False
            
            # Update task fields
            task.status = status
            task.updated_at = datetime.utcnow()
            
            # Ensure progress is monotonic
            if progress is not None:
                # Ensure progress doesn't decrease (monotonic property)
                progress = max(task.progress, min(100, max(0, progress)))
                try:
                    task.update_progress(progress)
                except ValueError as ve:
                    logger.warning(f"Progress update validation failed for task {task_id}: {ve}")
                    # Continue with other updates even if progress update fails
            
            if error_message is not None:
                task.error_message = error_message
            
            if status == TaskStatus.COMPLETED:
                task.completed_at = datetime.utcnow()
                task.progress = 100
            
            return self.update_task(task)
            
        except Exception as e:
            logger.error(f"Failed to update task status {task_id}: {e}")
            return False
    
    def update_task_progress_only(self, task_id: str, progress: int, message: str = "") -> bool:
        """
        Update only the progress of a task with monotonic guarantees.
        
        This method is optimized for frequent progress updates during processing.
        
        Args:
            task_id: Task identifier
            progress: Progress percentage (0-100)
            message: Optional progress message
            
        Returns:
            True if progress was updated successfully, False otherwise
        """
        try:
            task = self.get_task(task_id)
            if task is None:
                logger.warning(f"Cannot update progress for non-existent task {task_id}")
                return False
            
            # Ensure progress is monotonic and within bounds
            progress = max(task.progress, min(100, max(0, progress)))
            
            # Only update if progress actually changed
            if progress == task.progress:
                return True
            
            # Update progress using the model's validation
            try:
                task.update_progress(progress)
            except ValueError as ve:
                logger.warning(f"Progress validation failed for task {task_id}: {ve}")
                return False
            
            return self.update_task(task)
            
        except Exception as e:
            logger.error(f"Failed to update task progress {task_id}: {e}")
            return False
    
    def cleanup_expired_tasks(self) -> int:
        """
        Clean up expired tasks and session references.
        
        Returns:
            Number of tasks cleaned up
        """
        try:
            # This is a basic cleanup - Redis handles expiration automatically
            # but we can clean up session task sets that may have stale references
            cleaned_count = 0
            
            # Get all session keys
            session_keys = self._redis_client.keys("session:*:tasks")
            
            for session_key in session_keys:
                task_ids = self._redis_client.smembers(session_key)
                stale_task_ids = []
                
                for task_id in task_ids:
                    task_key = self._get_task_key(task_id)
                    if not self._redis_client.exists(task_key):
                        stale_task_ids.append(task_id)
                
                if stale_task_ids:
                    self._redis_client.srem(session_key, *stale_task_ids)
                    cleaned_count += len(stale_task_ids)
            
            logger.info(f"Cleaned up {cleaned_count} expired task references")
            return cleaned_count
            
        except RedisError as e:
            logger.error(f"Failed to cleanup expired tasks: {e}")
            return 0
    
    def health_check(self) -> bool:
        """
        Check if Redis connection is healthy.
        
        Returns:
            True if connection is healthy, False otherwise
        """
        try:
            self._redis_client.ping()
            return True
        except RedisError:
            return False
    
    async def close(self) -> None:
        """
        Close Redis connection gracefully.
        """
        try:
            if self._redis_client:
                await self._redis_client.aclose()
                logger.info("Task storage Redis connection closed")
        except Exception as e:
            logger.error(f"Error closing task storage Redis connection: {e}")