"""
File download API endpoints.

This module handles secure file downloads with session-based access control
and proper file serving with appropriate headers.
"""

import logging
import os
from pathlib import Path

from fastapi import APIRouter, Request, HTTPException, Path as PathParam
from fastapi.responses import FileResponse

logger = logging.getLogger(__name__)

download_router = APIRouter(prefix="/download", tags=["download"])


@download_router.get("/{task_id}/{filename}")
async def download_file(
    request: Request,
    task_id: str = PathParam(..., description="Unique task identifier"),
    filename: str = PathParam(..., description="Filename to download"),
    inline: bool = False,
    session: str = None
):
    """
    Download a processed file with session-based access control.
    
    Args:
        request: FastAPI request object (contains session info)
        task_id: Unique task identifier
        filename: Filename to download
        
    Returns:
        FileResponse with the requested file
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
        
        # Verify task is completed
        if task.status.value != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"Task is not completed (status: {task.status.value})"
            )
        
        # Verify file access
        if not file_storage.verify_file_access(session_id, task_id, filename, "output"):
            raise HTTPException(
                status_code=404,
                detail=f"File {filename} not found or access denied"
            )
        
        # URL decode the filename to handle special characters
        from urllib.parse import unquote
        decoded_filename = unquote(filename)
        
        # Get file path
        file_path = file_storage.get_output_path(session_id, task_id, decoded_filename)
        logger.info(f"Download request - Task: {task_id}, Original: {filename}, Decoded: {decoded_filename}, File path: {file_path}")
        if file_path is None or not file_path.exists():
            logger.error(f"File not found - Task: {task_id}, Decoded: {decoded_filename}, Expected path: {file_path}")
            raise HTTPException(
                status_code=404,
                detail=f"File {decoded_filename} not found"
            )
        
        # Determine content type based on file extension
        content_type = "application/octet-stream"
        if filename.lower().endswith('.pdf'):
            content_type = "application/pdf"
        elif filename.lower().endswith('.zip'):
            content_type = "application/zip"
        
        # Log download activity
        logger.info(f"File {'preview' if inline else 'download'}: {filename} for task {task_id} by session {session_id}")
        
        # Determine content disposition based on inline parameter
        if inline:
            content_disposition = f"inline; filename=\"{decoded_filename}\""
        else:
            content_disposition = f"attachment; filename=\"{decoded_filename}\""
        
        # Return file response
        return FileResponse(
            path=str(file_path),
            filename=decoded_filename,
            media_type=content_type,
            headers={
                "Content-Disposition": content_disposition,
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download file {filename} for task {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to download file")


@download_router.head("/{task_id}/{filename}")
async def check_file_availability(
    request: Request,
    task_id: str = PathParam(..., description="Unique task identifier"),
    filename: str = PathParam(..., description="Filename to check")
):
    """
    Check if a file is available for download without actually downloading it.
    
    Args:
        request: FastAPI request object (contains session info)
        task_id: Unique task identifier
        filename: Filename to check
        
    Returns:
        HTTP 200 if file is available, appropriate error code otherwise
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
        
        # Verify task is completed
        if task.status.value != "completed":
            raise HTTPException(
                status_code=400,
                detail=f"Task is not completed (status: {task.status.value})"
            )
        
        # Verify file access
        if not file_storage.verify_file_access(session_id, task_id, filename, "output"):
            raise HTTPException(
                status_code=404,
                detail=f"File {filename} not found or access denied"
            )
        
        # URL decode the filename to handle special characters
        from urllib.parse import unquote
        decoded_filename = unquote(filename)
        
        # Get file path and check existence
        file_path = file_storage.get_output_path(session_id, task_id, decoded_filename)
        if file_path is None or not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"File {decoded_filename} not found"
            )
        
        # Get file size
        file_size = file_path.stat().st_size
        
        # Determine content type
        content_type = "application/octet-stream"
        if filename.lower().endswith('.pdf'):
            content_type = "application/pdf"
        elif filename.lower().endswith('.zip'):
            content_type = "application/zip"
        
        # Return headers without body
        return FileResponse(
            path=str(file_path),
            filename=decoded_filename,
            media_type=content_type,
            headers={
                "Content-Length": str(file_size),
                "Content-Type": content_type,
                "Cache-Control": "no-cache, no-store, must-revalidate"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to check file availability {filename} for task {task_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to check file availability")