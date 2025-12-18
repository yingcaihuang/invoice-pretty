"""
Data models for the Web Invoice Processor application.

This module defines the core data structures used throughout the application,
including Task, Session, and FileUpload models with proper validation.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator
from ..utils.timezone import beijing_now


class TaskStatus(str, Enum):
    """Enumeration of possible task states."""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class Task(BaseModel):
    """
    Represents a processing task in the system.
    
    Each task corresponds to a user's request to process PDF files or ZIP archives.
    Tasks are uniquely identified by task_id and associated with a user session.
    """
    task_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique task identifier")
    session_id: str = Field(..., description="Session identifier that owns this task")
    status: TaskStatus = Field(default=TaskStatus.QUEUED, description="Current task status")
    progress: int = Field(default=0, ge=0, le=100, description="Processing progress percentage")
    input_files: List[str] = Field(default_factory=list, description="List of input file paths")
    output_files: List[str] = Field(default_factory=list, description="List of output file paths")
    error_message: Optional[str] = Field(default=None, description="Error message if task failed")
    celery_task_id: Optional[str] = Field(default=None, description="Celery task identifier for async processing")
    created_at: datetime = Field(default_factory=beijing_now, description="Task creation timestamp")
    updated_at: datetime = Field(default_factory=beijing_now, description="Last update timestamp")
    completed_at: Optional[datetime] = Field(default=None, description="Task completion timestamp")

    @validator('task_id')
    def validate_task_id_format(cls, v):
        """Ensure task_id is a valid UUID format."""
        try:
            UUID(v)
            return v
        except ValueError:
            raise ValueError("task_id must be a valid UUID format")

    @validator('session_id')
    def validate_session_id_not_empty(cls, v):
        """Ensure session_id is not empty."""
        if not v or not v.strip():
            raise ValueError("session_id cannot be empty")
        return v.strip()

    @validator('progress')
    def validate_progress_range(cls, v):
        """Ensure progress is within valid range."""
        if v < 0 or v > 100:
            raise ValueError("progress must be between 0 and 100")
        return v

    @validator('input_files')
    def validate_input_files_not_empty(cls, v):
        """Ensure input_files is a list (can be empty during creation)."""
        if v is None:
            return []
        return v

    def update_progress(self, progress: int) -> None:
        """Update task progress and timestamp."""
        if progress < 0 or progress > 100:
            raise ValueError("progress must be between 0 and 100")
        if progress < self.progress:
            raise ValueError("progress cannot decrease")
        self.progress = progress
        self.updated_at = beijing_now()

    def mark_completed(self, output_files: List[str]) -> None:
        """Mark task as completed with output files."""
        self.status = TaskStatus.COMPLETED
        self.progress = 100
        self.output_files = output_files
        self.completed_at = beijing_now()
        self.updated_at = beijing_now()

    def mark_failed(self, error_message: str) -> None:
        """Mark task as failed with error message."""
        self.status = TaskStatus.FAILED
        self.error_message = error_message
        self.updated_at = beijing_now()

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Session(BaseModel):
    """
    Represents a user session in the system.
    
    Sessions provide isolation between users without requiring authentication.
    Each session is identified by a unique session_id stored in browser localStorage.
    """
    session_id: str = Field(..., description="Unique session identifier")
    created_at: datetime = Field(default_factory=beijing_now, description="Session creation timestamp")
    last_activity: datetime = Field(default_factory=beijing_now, description="Last activity timestamp")
    task_count: int = Field(default=0, ge=0, description="Number of tasks created in this session")

    @validator('session_id')
    def validate_session_id_format(cls, v):
        """Ensure session_id is not empty and has valid format."""
        if not v or not v.strip():
            raise ValueError("session_id cannot be empty")
        
        # Accept both UUID format and frontend-generated format (session_xxx_timestamp)
        v = v.strip()
        if v.startswith('session_') and len(v) > 8:
            return v
        
        try:
            UUID(v)
            return v
        except ValueError:
            raise ValueError("session_id must be either a valid UUID or frontend-generated format")

    def update_activity(self) -> None:
        """Update the last activity timestamp."""
        self.last_activity = datetime.utcnow()

    def increment_task_count(self) -> None:
        """Increment the task count and update activity."""
        self.task_count += 1
        self.update_activity()

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class FileUpload(BaseModel):
    """
    Represents an uploaded file in the system.
    
    Tracks metadata about files uploaded by users for processing.
    """
    filename: str = Field(..., description="Original filename")
    size: int = Field(..., ge=0, description="File size in bytes")
    content_type: str = Field(..., description="MIME type of the file")
    task_id: str = Field(..., description="Associated task identifier")
    session_id: str = Field(..., description="Session that uploaded the file")
    upload_path: str = Field(..., description="Server path where file is stored")

    @validator('filename')
    def validate_filename_not_empty(cls, v):
        """Ensure filename is not empty."""
        if not v or not v.strip():
            raise ValueError("filename cannot be empty")
        return v.strip()

    @validator('size')
    def validate_file_size_positive(cls, v):
        """Ensure file size is positive."""
        if v < 0:
            raise ValueError("file size must be non-negative")
        return v

    @validator('content_type')
    def validate_content_type_allowed(cls, v):
        """Ensure content type is allowed for processing."""
        allowed_types = [
            'application/pdf',
            'application/zip',
            'application/x-zip-compressed',
            'application/octet-stream'  # Some browsers send this for ZIP files
        ]
        if v not in allowed_types:
            raise ValueError(f"content_type must be one of: {', '.join(allowed_types)}")
        return v

    @validator('task_id')
    def validate_task_id_format(cls, v):
        """Ensure task_id is a valid UUID format."""
        try:
            UUID(v)
            return v
        except ValueError:
            raise ValueError("task_id must be a valid UUID format")

    @validator('session_id')
    def validate_session_id_format(cls, v):
        """Ensure session_id is not empty and has valid format."""
        if not v or not v.strip():
            raise ValueError("session_id cannot be empty")
        
        # Accept both UUID format and frontend-generated format (session_xxx_timestamp)
        v = v.strip()
        if v.startswith('session_') and len(v) > 8:
            return v
        
        try:
            UUID(v)
            return v
        except ValueError:
            raise ValueError("session_id must be either a valid UUID or frontend-generated format")

    @validator('upload_path')
    def validate_upload_path_not_empty(cls, v):
        """Ensure upload_path is not empty."""
        if not v or not v.strip():
            raise ValueError("upload_path cannot be empty")
        return v.strip()

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }