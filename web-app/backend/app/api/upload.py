"""
File upload API endpoints.

This module handles file upload operations including validation,
storage, and task creation for PDF and ZIP files with async processing.
"""

import logging
import os
from typing import List

from fastapi import APIRouter, Request, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from ..models.data_models import Task, TaskStatus, FileUpload
from ..services.task_queue import TaskQueueManager

logger = logging.getLogger(__name__)

upload_router = APIRouter(prefix="/upload", tags=["upload"])

# Configuration
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 52428800))  # 50MB default
ALLOWED_CONTENT_TYPES = [
    "application/pdf",
    "application/zip", 
    "application/x-zip-compressed",
    "application/octet-stream"  # Some browsers send this for ZIP files
]
ALLOWED_EXTENSIONS = [".pdf", ".zip"]


def validate_file(file: UploadFile) -> tuple[bool, str]:
    """
    Validate uploaded file type and size.
    
    Args:
        file: FastAPI UploadFile object
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check file size
    if hasattr(file, 'size') and file.size and file.size > MAX_FILE_SIZE:
        return False, f"File size exceeds maximum limit of {MAX_FILE_SIZE} bytes"
    
    # Check content type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        return False, f"Invalid file type. Allowed types: PDF, ZIP"
    
    # Check file extension
    if file.filename:
        file_ext = os.path.splitext(file.filename.lower())[1]
        if file_ext not in ALLOWED_EXTENSIONS:
            return False, f"Invalid file extension. Allowed extensions: {', '.join(ALLOWED_EXTENSIONS)}"
    
    return True, ""


@upload_router.post("/")
async def upload_files(
    request: Request,
    files: List[UploadFile] = File(...)
):
    """
    Upload PDF files or ZIP archives for processing.
    
    Args:
        request: FastAPI request object (contains session info)
        files: List of uploaded files
        
    Returns:
        JSON response with task ID and status
    """
    try:
        # Get services from app state
        session_manager = request.app.state.session_manager
        task_storage = request.app.state.task_storage
        file_storage = request.app.state.file_storage
        
        # Get session ID from middleware
        session_id = request.state.session_id
        
        # Validate files
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        validated_files = []
        for file in files:
            is_valid, error_msg = validate_file(file)
            if not is_valid:
                raise HTTPException(status_code=400, detail=error_msg)
            validated_files.append(file)
        
        # Create new task
        task = Task(
            session_id=session_id,
            status=TaskStatus.QUEUED,
            input_files=[],  # Will be populated after file storage
            output_files=[],
            progress=0
        )
        
        # Store uploaded files
        stored_files = []
        input_file_paths = []
        
        for file in validated_files:
            # Reset file pointer to beginning
            await file.seek(0)
            
            # Store file
            file_upload = file_storage.store_upload(session_id, task.task_id, file)
            if file_upload is None:
                # Clean up any already stored files
                for stored_file in stored_files:
                    try:
                        os.unlink(stored_file.upload_path)
                    except OSError:
                        pass
                raise HTTPException(status_code=500, detail="Failed to store uploaded file")
            
            stored_files.append(file_upload)
            input_file_paths.append(file_upload.upload_path)
        
        # Update task with input file paths
        task.input_files = input_file_paths
        
        # Store task in Redis
        if not task_storage.store_task(task):
            # Clean up stored files on task storage failure
            for stored_file in stored_files:
                try:
                    os.unlink(stored_file.upload_path)
                except OSError:
                    pass
            raise HTTPException(status_code=500, detail="Failed to create processing task")
        
        # Initialize task queue manager and enqueue task for processing
        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            storage_path = os.getenv("STORAGE_PATH", "./storage")
            task_queue = TaskQueueManager(redis_url=redis_url, storage_path=storage_path)
            
            # Enqueue task for async processing
            if task_queue.enqueue_task(task.task_id, session_id):
                logger.info(f"Enqueued task {task.task_id} for async processing")
            else:
                logger.warning(f"Failed to enqueue task {task.task_id}, will remain in queued state")
        except Exception as queue_error:
            logger.error(f"Failed to enqueue task {task.task_id}: {queue_error}")
            # Don't fail the upload, task can be processed manually or retried
        
        # Increment session task count
        session_manager.increment_task_count(session_id)
        
        logger.info(f"Created task {task.task_id} with {len(validated_files)} files for session {session_id}")
        
        return {
            "taskId": task.task_id,  # Frontend expects camelCase
            "status": task.status.value,
            "message": f"Successfully uploaded {len(validated_files)} file(s) and queued for processing",
            "fileCount": len(validated_files),  # Frontend expects camelCase
            "createdAt": task.created_at.isoformat()  # Frontend expects camelCase
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed for session {request.state.session_id}: {e}")
        raise HTTPException(status_code=500, detail="File upload failed")


@upload_router.get("/limits")
async def get_upload_limits():
    """
    Get upload limits and allowed file types.
    
    Returns:
        JSON response with upload configuration
    """
    return {
        "max_file_size": MAX_FILE_SIZE,
        "max_file_size_mb": MAX_FILE_SIZE / (1024 * 1024),
        "allowed_content_types": ALLOWED_CONTENT_TYPES,
        "allowed_extensions": ALLOWED_EXTENSIONS
    }