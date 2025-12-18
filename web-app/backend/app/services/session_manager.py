"""
Session management interface for the Web Invoice Processor.

This module provides session management capabilities including session creation,
validation, activity tracking, and cleanup without requiring user authentication.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import uuid4

import redis
from redis.exceptions import ConnectionError, RedisError

from ..models.data_models import Session
from ..utils.timezone import beijing_now


logger = logging.getLogger(__name__)


class SessionManager:
    """
    Session management interface for handling user sessions.
    
    Provides methods for creating, validating, and managing user sessions
    with automatic cleanup and activity tracking.
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379", db: int = 1):
        """
        Initialize the session manager.
        
        Args:
            redis_url: Redis connection URL
            db: Redis database number to use (different from task storage)
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
            logger.info(f"Session manager connected to Redis at {self.redis_url}")
        except ConnectionError as e:
            logger.error(f"Failed to connect to Redis for session management: {e}")
            raise
    
    def _get_session_key(self, session_id: str) -> str:
        """Generate Redis key for session data."""
        return f"session:{session_id}"
    
    def _serialize_session(self, session: Session) -> str:
        """Serialize session object to JSON string."""
        return session.json()
    
    def _deserialize_session(self, session_data: str) -> Session:
        """Deserialize JSON string to session object."""
        return Session.parse_raw(session_data)
    
    def store_session(self, session: Session, expire_hours: int = 72) -> bool:
        """
        Store an existing session object in Redis.
        
        Args:
            session: Session object to store
            expire_hours: Hours until session expires (default: 72)
            
        Returns:
            True if session was stored successfully, False otherwise
        """
        try:
            session_key = self._get_session_key(session.session_id)
            session_data = self._serialize_session(session)
            expire_seconds = expire_hours * 3600
            
            self._redis_client.setex(session_key, expire_seconds, session_data)
            
            logger.info(f"Stored session {session.session_id}")
            return True
            
        except RedisError as e:
            logger.error(f"Failed to store session {session.session_id}: {e}")
            return False

    def create_session(self, expire_hours: int = 72) -> Session:
        """
        Create a new session with unique identifier.
        
        Args:
            expire_hours: Hours until session expires (default: 72)
            
        Returns:
            New Session object
        """
        try:
            session_id = str(uuid4())
            session = Session(
                session_id=session_id,
                created_at=beijing_now(),
                last_activity=beijing_now(),
                task_count=0
            )
            
            # Store session in Redis with expiration
            session_key = self._get_session_key(session_id)
            session_data = self._serialize_session(session)
            expire_seconds = expire_hours * 3600
            
            self._redis_client.setex(session_key, expire_seconds, session_data)
            
            logger.info(f"Created new session {session_id}")
            return session
            
        except RedisError as e:
            logger.error(f"Failed to create session: {e}")
            raise
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """
        Retrieve a session by ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session object if found and valid, None otherwise
        """
        try:
            session_key = self._get_session_key(session_id)
            session_data = self._redis_client.get(session_key)
            
            if session_data is None:
                logger.debug(f"Session {session_id} not found or expired")
                return None
            
            session = self._deserialize_session(session_data)
            logger.debug(f"Retrieved session {session_id}")
            return session
            
        except RedisError as e:
            logger.error(f"Failed to retrieve session {session_id}: {e}")
            return None
    
    def update_session_activity(self, session_id: str) -> bool:
        """
        Update session's last activity timestamp.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session was updated successfully, False otherwise
        """
        try:
            session = self.get_session(session_id)
            if session is None:
                logger.warning(f"Cannot update activity for non-existent session {session_id}")
                return False
            
            # Update activity timestamp
            session.update_activity()
            
            # Store updated session while preserving TTL
            session_key = self._get_session_key(session_id)
            session_data = self._serialize_session(session)
            ttl = self._redis_client.ttl(session_key)
            
            if ttl > 0:
                self._redis_client.setex(session_key, ttl, session_data)
            else:
                self._redis_client.set(session_key, session_data)
            
            logger.debug(f"Updated activity for session {session_id}")
            return True
            
        except RedisError as e:
            logger.error(f"Failed to update session activity {session_id}: {e}")
            return False
    
    def increment_task_count(self, session_id: str) -> bool:
        """
        Increment the task count for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if task count was incremented successfully, False otherwise
        """
        try:
            session = self.get_session(session_id)
            if session is None:
                logger.warning(f"Cannot increment task count for non-existent session {session_id}")
                return False
            
            # Increment task count and update activity
            session.increment_task_count()
            
            # Store updated session while preserving TTL
            session_key = self._get_session_key(session_id)
            session_data = self._serialize_session(session)
            ttl = self._redis_client.ttl(session_key)
            
            if ttl > 0:
                self._redis_client.setex(session_key, ttl, session_data)
            else:
                self._redis_client.set(session_key, session_data)
            
            logger.debug(f"Incremented task count for session {session_id} to {session.task_count}")
            return True
            
        except RedisError as e:
            logger.error(f"Failed to increment task count for session {session_id}: {e}")
            return False
    
    def validate_session(self, session_id: str) -> bool:
        """
        Validate that a session exists and is active.
        
        Args:
            session_id: Session identifier to validate
            
        Returns:
            True if session is valid, False otherwise
        """
        try:
            session = self.get_session(session_id)
            if session is None:
                return False
            
            # Update activity timestamp for valid sessions
            self.update_session_activity(session_id)
            return True
            
        except Exception as e:
            logger.error(f"Failed to validate session {session_id}: {e}")
            return False
    
    def extend_session(self, session_id: str, extend_hours: int = 24) -> bool:
        """
        Extend session expiration time.
        
        Args:
            session_id: Session identifier
            extend_hours: Hours to extend the session
            
        Returns:
            True if session was extended successfully, False otherwise
        """
        try:
            session_key = self._get_session_key(session_id)
            
            # Check if session exists
            if not self._redis_client.exists(session_key):
                logger.warning(f"Cannot extend non-existent session {session_id}")
                return False
            
            # Extend TTL
            extend_seconds = extend_hours * 3600
            current_ttl = self._redis_client.ttl(session_key)
            new_ttl = max(current_ttl, 0) + extend_seconds
            
            self._redis_client.expire(session_key, new_ttl)
            
            logger.debug(f"Extended session {session_id} by {extend_hours} hours")
            return True
            
        except RedisError as e:
            logger.error(f"Failed to extend session {session_id}: {e}")
            return False
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session from Redis.
        
        Args:
            session_id: Session identifier to delete
            
        Returns:
            True if session was deleted successfully, False otherwise
        """
        try:
            session_key = self._get_session_key(session_id)
            deleted = self._redis_client.delete(session_key) > 0
            
            logger.debug(f"Deleted session {session_id}: {deleted}")
            return deleted
            
        except RedisError as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False
    
    def get_active_sessions(self) -> List[Session]:
        """
        Get all currently active sessions.
        
        Returns:
            List of active Session objects
        """
        try:
            session_keys = self._redis_client.keys("session:*")
            sessions = []
            
            for session_key in session_keys:
                session_data = self._redis_client.get(session_key)
                if session_data:
                    try:
                        session = self._deserialize_session(session_data)
                        sessions.append(session)
                    except Exception as e:
                        logger.warning(f"Failed to deserialize session from {session_key}: {e}")
            
            logger.debug(f"Retrieved {len(sessions)} active sessions")
            return sessions
            
        except RedisError as e:
            logger.error(f"Failed to get active sessions: {e}")
            return []
    
    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions (Redis handles this automatically).
        
        This method is mainly for logging and monitoring purposes
        since Redis automatically removes expired keys.
        
        Returns:
            Number of sessions that were found to be expired
        """
        try:
            # Get all session keys
            all_session_keys = self._redis_client.keys("session:*")
            initial_count = len(all_session_keys)
            
            # Check which ones still exist (non-expired)
            existing_session_keys = []
            for key in all_session_keys:
                if self._redis_client.exists(key):
                    existing_session_keys.append(key)
            
            expired_count = initial_count - len(existing_session_keys)
            
            if expired_count > 0:
                logger.info(f"Found {expired_count} expired sessions")
            
            return expired_count
            
        except RedisError as e:
            logger.error(f"Failed to cleanup expired sessions: {e}")
            return 0
    
    def get_session_statistics(self) -> Dict[str, int]:
        """
        Get session statistics for monitoring.
        
        Returns:
            Dictionary with session statistics
        """
        try:
            active_sessions = self.get_active_sessions()
            
            total_tasks = sum(session.task_count for session in active_sessions)
            
            # Calculate session age statistics
            now = beijing_now()
            session_ages = []
            for session in active_sessions:
                age_hours = (now - session.created_at).total_seconds() / 3600
                session_ages.append(age_hours)
            
            stats = {
                "active_sessions": len(active_sessions),
                "total_tasks": total_tasks,
                "avg_tasks_per_session": total_tasks / len(active_sessions) if active_sessions else 0,
                "avg_session_age_hours": sum(session_ages) / len(session_ages) if session_ages else 0
            }
            
            logger.debug(f"Session statistics: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get session statistics: {e}")
            return {
                "active_sessions": 0,
                "total_tasks": 0,
                "avg_tasks_per_session": 0,
                "avg_session_age_hours": 0
            }
    
    def health_check(self) -> bool:
        """
        Check if session manager Redis connection is healthy.
        
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
                logger.info("Session manager Redis connection closed")
        except Exception as e:
            logger.error(f"Error closing session manager Redis connection: {e}")