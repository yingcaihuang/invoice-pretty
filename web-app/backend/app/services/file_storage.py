"""
File system storage manager for the Web Invoice Processor.

This module provides a file system-based storage interface for managing
uploaded files, temporary files, and output files with proper organization
and cleanup capabilities.
"""

import logging
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from uuid import uuid4

from fastapi import UploadFile

from ..models.data_models import FileUpload


logger = logging.getLogger(__name__)


class FileStorageManager:
    """
    File system storage manager for handling file operations.
    
    Provides methods for storing uploaded files, managing temporary files,
    organizing output files, and performing cleanup operations.
    """
    
    def __init__(self, base_storage_path: str = "/app/storage"):
        """
        Initialize the file storage manager.
        
        Args:
            base_storage_path: Base directory for all file storage
        """
        self.base_path = Path(base_storage_path)
        self.uploads_path = self.base_path / "uploads"
        self.outputs_path = self.base_path / "outputs"
        self.temp_path = self.base_path / "temp"
        
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """Create necessary storage directories if they don't exist."""
        try:
            self.base_path.mkdir(parents=True, exist_ok=True)
            self.uploads_path.mkdir(parents=True, exist_ok=True)
            self.outputs_path.mkdir(parents=True, exist_ok=True)
            self.temp_path.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Storage directories initialized at {self.base_path}")
        except OSError as e:
            logger.error(f"Failed to create storage directories: {e}")
            raise
    
    def _get_session_upload_path(self, session_id: str) -> Path:
        """Get upload directory path for a session."""
        return self.uploads_path / session_id
    
    def _get_session_output_path(self, session_id: str) -> Path:
        """Get output directory path for a session."""
        return self.outputs_path / session_id
    
    def _get_task_temp_path(self, task_id: str) -> Path:
        """Get temporary directory path for a task."""
        return self.temp_path / task_id
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename to prevent path traversal and other security issues.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename safe for filesystem use
        """
        # Remove path components and dangerous characters
        safe_name = os.path.basename(filename)
        safe_name = "".join(c for c in safe_name if c.isalnum() or c in ".-_")
        
        # Ensure filename is not empty and has reasonable length
        if not safe_name or len(safe_name) > 255:
            safe_name = f"file_{uuid4().hex[:8]}"
        
        return safe_name
    
    def store_upload(self, session_id: str, task_id: str, file: UploadFile) -> Optional[FileUpload]:
        """
        Store an uploaded file to the filesystem.
        
        Args:
            session_id: Session identifier
            task_id: Task identifier
            file: FastAPI UploadFile object
            
        Returns:
            FileUpload object with metadata, or None if storage failed
        """
        try:
            # Create session upload directory
            session_upload_path = self._get_session_upload_path(session_id)
            session_upload_path.mkdir(parents=True, exist_ok=True)
            
            # Generate safe filename
            safe_filename = self._sanitize_filename(file.filename or "unknown")
            unique_filename = f"{task_id}_{safe_filename}"
            file_path = session_upload_path / unique_filename
            
            # Write file to disk
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Get file size
            file_size = file_path.stat().st_size
            
            # Create FileUpload object
            file_upload = FileUpload(
                filename=file.filename or safe_filename,
                size=file_size,
                content_type=file.content_type or "application/octet-stream",
                task_id=task_id,
                session_id=session_id,
                upload_path=str(file_path)
            )
            
            logger.debug(f"Stored upload file {unique_filename} for task {task_id}")
            return file_upload
            
        except Exception as e:
            logger.error(f"Failed to store upload file for task {task_id}: {e}")
            return None
    
    def get_upload_path(self, session_id: str, task_id: str, filename: str) -> Optional[Path]:
        """
        Get the path to an uploaded file.
        
        Args:
            session_id: Session identifier
            task_id: Task identifier
            filename: Original filename
            
        Returns:
            Path to the file if it exists, None otherwise
        """
        try:
            session_upload_path = self._get_session_upload_path(session_id)
            safe_filename = self._sanitize_filename(filename)
            unique_filename = f"{task_id}_{safe_filename}"
            file_path = session_upload_path / unique_filename
            
            if file_path.exists() and file_path.is_file():
                return file_path
            
            logger.debug(f"Upload file not found: {file_path}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get upload path for {filename}: {e}")
            return None
    
    def create_temp_directory(self, task_id: str) -> Optional[Path]:
        """
        Create a temporary directory for task processing.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Path to temporary directory, or None if creation failed
        """
        try:
            temp_dir = self._get_task_temp_path(task_id)
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            logger.debug(f"Created temp directory for task {task_id}")
            return temp_dir
            
        except Exception as e:
            logger.error(f"Failed to create temp directory for task {task_id}: {e}")
            return None
    
    def store_output(self, session_id: str, task_id: str, 
                    output_data: bytes, filename: str) -> Optional[Path]:
        """
        Store processed output file.
        
        Args:
            session_id: Session identifier
            task_id: Task identifier
            output_data: Processed file data
            filename: Output filename
            
        Returns:
            Path to stored output file, or None if storage failed
        """
        try:
            # Create session output directory
            session_output_path = self._get_session_output_path(session_id)
            session_output_path.mkdir(parents=True, exist_ok=True)
            
            # Generate safe filename
            safe_filename = self._sanitize_filename(filename)
            unique_filename = f"{task_id}_{safe_filename}"
            output_path = session_output_path / unique_filename
            
            # Write output data to file
            with open(output_path, "wb") as f:
                f.write(output_data)
            
            logger.debug(f"Stored output file {unique_filename} for task {task_id}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to store output file for task {task_id}: {e}")
            return None
    
    def get_output_path(self, session_id: str, task_id: str, filename: str) -> Optional[Path]:
        """
        Get the path to an output file.
        
        Args:
            session_id: Session identifier
            task_id: Task identifier
            filename: Output filename
            
        Returns:
            Path to the output file if it exists, None otherwise
        """
        try:
            session_output_path = self._get_session_output_path(session_id)
            safe_filename = self._sanitize_filename(filename)
            unique_filename = f"{task_id}_{safe_filename}"
            output_path = session_output_path / unique_filename
            
            if output_path.exists() and output_path.is_file():
                return output_path
            
            logger.debug(f"Output file not found: {output_path}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get output path for {filename}: {e}")
            return None
    
    def cleanup_task_files(self, session_id: str, task_id: str) -> bool:
        """
        Clean up all files associated with a task.
        
        Args:
            session_id: Session identifier
            task_id: Task identifier
            
        Returns:
            True if cleanup was successful, False otherwise
        """
        try:
            cleanup_success = True
            
            # Clean up upload files
            session_upload_path = self._get_session_upload_path(session_id)
            if session_upload_path.exists():
                for file_path in session_upload_path.glob(f"{task_id}_*"):
                    try:
                        file_path.unlink()
                        logger.debug(f"Deleted upload file: {file_path}")
                    except OSError as e:
                        logger.warning(f"Failed to delete upload file {file_path}: {e}")
                        cleanup_success = False
            
            # Clean up output files
            session_output_path = self._get_session_output_path(session_id)
            if session_output_path.exists():
                for file_path in session_output_path.glob(f"{task_id}_*"):
                    try:
                        file_path.unlink()
                        logger.debug(f"Deleted output file: {file_path}")
                    except OSError as e:
                        logger.warning(f"Failed to delete output file {file_path}: {e}")
                        cleanup_success = False
            
            # Clean up temp directory
            temp_dir = self._get_task_temp_path(task_id)
            if temp_dir.exists():
                try:
                    shutil.rmtree(temp_dir)
                    logger.debug(f"Deleted temp directory: {temp_dir}")
                except OSError as e:
                    logger.warning(f"Failed to delete temp directory {temp_dir}: {e}")
                    cleanup_success = False
            
            logger.info(f"Cleanup task {task_id} files: {'success' if cleanup_success else 'partial'}")
            return cleanup_success
            
        except Exception as e:
            logger.error(f"Failed to cleanup files for task {task_id}: {e}")
            return False
    
    def cleanup_old_files(self, max_age_hours: int = 24) -> Dict[str, int]:
        """
        Clean up files older than specified age.
        
        Args:
            max_age_hours: Maximum age in hours before files are deleted
            
        Returns:
            Dictionary with cleanup statistics
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            cutoff_timestamp = cutoff_time.timestamp()
            
            stats = {
                "uploads_deleted": 0,
                "outputs_deleted": 0,
                "temp_dirs_deleted": 0,
                "errors": 0
            }
            
            # Clean up old upload files
            for session_dir in self.uploads_path.iterdir():
                if session_dir.is_dir():
                    for file_path in session_dir.iterdir():
                        if file_path.is_file() and file_path.stat().st_mtime < cutoff_timestamp:
                            try:
                                file_path.unlink()
                                stats["uploads_deleted"] += 1
                            except OSError as e:
                                logger.warning(f"Failed to delete old upload file {file_path}: {e}")
                                stats["errors"] += 1
                    
                    # Remove empty session directories
                    try:
                        if not any(session_dir.iterdir()):
                            session_dir.rmdir()
                    except OSError:
                        pass  # Directory not empty or other error
            
            # Clean up old output files
            for session_dir in self.outputs_path.iterdir():
                if session_dir.is_dir():
                    for file_path in session_dir.iterdir():
                        if file_path.is_file() and file_path.stat().st_mtime < cutoff_timestamp:
                            try:
                                file_path.unlink()
                                stats["outputs_deleted"] += 1
                            except OSError as e:
                                logger.warning(f"Failed to delete old output file {file_path}: {e}")
                                stats["errors"] += 1
                    
                    # Remove empty session directories
                    try:
                        if not any(session_dir.iterdir()):
                            session_dir.rmdir()
                    except OSError:
                        pass  # Directory not empty or other error
            
            # Clean up old temp directories
            for temp_dir in self.temp_path.iterdir():
                if temp_dir.is_dir() and temp_dir.stat().st_mtime < cutoff_timestamp:
                    try:
                        shutil.rmtree(temp_dir)
                        stats["temp_dirs_deleted"] += 1
                    except OSError as e:
                        logger.warning(f"Failed to delete old temp directory {temp_dir}: {e}")
                        stats["errors"] += 1
            
            logger.info(f"Cleanup completed: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Failed to cleanup old files: {e}")
            return {"uploads_deleted": 0, "outputs_deleted": 0, "temp_dirs_deleted": 0, "errors": 1}
    
    def get_storage_usage(self) -> Dict[str, int]:
        """
        Get storage usage statistics.
        
        Returns:
            Dictionary with storage usage information in bytes
        """
        try:
            def get_directory_size(path: Path) -> int:
                """Calculate total size of directory."""
                total_size = 0
                if path.exists() and path.is_dir():
                    for file_path in path.rglob("*"):
                        if file_path.is_file():
                            try:
                                total_size += file_path.stat().st_size
                            except OSError:
                                pass  # Skip files that can't be accessed
                return total_size
            
            usage = {
                "uploads_size": get_directory_size(self.uploads_path),
                "outputs_size": get_directory_size(self.outputs_path),
                "temp_size": get_directory_size(self.temp_path),
                "total_size": 0
            }
            
            usage["total_size"] = sum(usage.values())
            
            logger.debug(f"Storage usage: {usage}")
            return usage
            
        except Exception as e:
            logger.error(f"Failed to get storage usage: {e}")
            return {"uploads_size": 0, "outputs_size": 0, "temp_size": 0, "total_size": 0}
    
    def verify_file_access(self, session_id: str, task_id: str, filename: str, 
                          file_type: str = "output") -> bool:
        """
        Verify that a session has access to a specific file.
        
        Args:
            session_id: Session identifier
            task_id: Task identifier
            filename: Filename to verify
            file_type: Type of file ("upload" or "output")
            
        Returns:
            True if access is allowed, False otherwise
        """
        try:
            if file_type == "upload":
                file_path = self.get_upload_path(session_id, task_id, filename)
            elif file_type == "output":
                file_path = self.get_output_path(session_id, task_id, filename)
            else:
                logger.warning(f"Invalid file type for access verification: {file_type}")
                return False
            
            # File exists and is accessible
            access_allowed = file_path is not None and file_path.exists()
            
            logger.debug(f"File access verification for {filename}: {access_allowed}")
            return access_allowed
            
        except Exception as e:
            logger.error(f"Failed to verify file access for {filename}: {e}")
            return False