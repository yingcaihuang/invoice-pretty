#!/usr/bin/env python3
"""
Simple test script for cleanup functionality.

This script tests the file cleanup and storage monitoring features
to ensure they work correctly.
"""

import os
import sys
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from app.services.file_storage import FileStorageManager
from app.services.task_storage import TaskStorageInterface
from app.models.data_models import Task, TaskStatus


def test_file_cleanup():
    """Test file cleanup functionality."""
    print("Testing file cleanup functionality...")
    
    # Create temporary storage directory
    with tempfile.TemporaryDirectory() as temp_dir:
        storage_path = Path(temp_dir)
        file_storage = FileStorageManager(base_storage_path=str(storage_path))
        
        # Create some test files with different ages
        session_id = "test-session-123"
        task_id = "test-task-456"
        
        # Create session directories
        uploads_dir = storage_path / "uploads" / session_id
        outputs_dir = storage_path / "outputs" / session_id
        uploads_dir.mkdir(parents=True, exist_ok=True)
        outputs_dir.mkdir(parents=True, exist_ok=True)
        
        # Create test files
        old_file = uploads_dir / f"{task_id}_old_file.pdf"
        new_file = uploads_dir / f"{task_id}_new_file.pdf"
        output_file = outputs_dir / f"{task_id}_output.pdf"
        
        # Write test content
        old_file.write_text("old file content")
        new_file.write_text("new file content")
        output_file.write_text("output file content")
        
        # Make old file appear old by modifying its timestamp
        old_time = time.time() - (25 * 3600)  # 25 hours ago
        os.utime(old_file, (old_time, old_time))
        
        print(f"Created test files:")
        print(f"  Old file: {old_file} (25 hours old)")
        print(f"  New file: {new_file} (current)")
        print(f"  Output file: {output_file} (current)")
        
        # Get initial storage usage
        initial_usage = file_storage.get_storage_usage()
        print(f"Initial storage usage: {initial_usage}")
        
        # Run cleanup (files older than 24 hours)
        cleanup_stats = file_storage.cleanup_old_files(max_age_hours=24)
        print(f"Cleanup stats: {cleanup_stats}")
        
        # Check which files remain
        print(f"Files after cleanup:")
        print(f"  Old file exists: {old_file.exists()}")
        print(f"  New file exists: {new_file.exists()}")
        print(f"  Output file exists: {output_file.exists()}")
        
        # Get final storage usage
        final_usage = file_storage.get_storage_usage()
        print(f"Final storage usage: {final_usage}")
        
        # Verify cleanup worked correctly
        assert not old_file.exists(), "Old file should have been deleted"
        assert new_file.exists(), "New file should still exist"
        assert output_file.exists(), "Output file should still exist"
        assert cleanup_stats["uploads_deleted"] >= 1, "At least one upload should have been deleted"
        
        print("✅ File cleanup test passed!")


def test_storage_monitoring():
    """Test storage usage monitoring."""
    print("\nTesting storage usage monitoring...")
    
    # Create temporary storage directory
    with tempfile.TemporaryDirectory() as temp_dir:
        storage_path = Path(temp_dir)
        file_storage = FileStorageManager(base_storage_path=str(storage_path))
        
        # Create some test files
        uploads_dir = storage_path / "uploads" / "session1"
        outputs_dir = storage_path / "outputs" / "session1"
        temp_dir_path = storage_path / "temp" / "task1"
        
        uploads_dir.mkdir(parents=True, exist_ok=True)
        outputs_dir.mkdir(parents=True, exist_ok=True)
        temp_dir_path.mkdir(parents=True, exist_ok=True)
        
        # Create files of different sizes
        (uploads_dir / "file1.pdf").write_text("x" * 1000)  # 1KB
        (outputs_dir / "file2.pdf").write_text("x" * 2000)  # 2KB
        (temp_dir_path / "file3.tmp").write_text("x" * 500)  # 0.5KB
        
        # Get storage usage
        usage_stats = file_storage.get_storage_usage()
        print(f"Storage usage stats: {usage_stats}")
        
        # Verify usage calculation
        assert usage_stats["uploads_size"] >= 1000, "Uploads size should be at least 1KB"
        assert usage_stats["outputs_size"] >= 2000, "Outputs size should be at least 2KB"
        assert usage_stats["temp_size"] >= 500, "Temp size should be at least 0.5KB"
        assert usage_stats["total_size"] >= 3500, "Total size should be at least 3.5KB"
        
        print("✅ Storage monitoring test passed!")


def test_task_file_cleanup():
    """Test task-specific file cleanup."""
    print("\nTesting task-specific file cleanup...")
    
    # Create temporary storage directory
    with tempfile.TemporaryDirectory() as temp_dir:
        storage_path = Path(temp_dir)
        file_storage = FileStorageManager(base_storage_path=str(storage_path))
        
        session_id = "test-session-789"
        task_id = "test-task-101"
        
        # Create session directories
        uploads_dir = storage_path / "uploads" / session_id
        outputs_dir = storage_path / "outputs" / session_id
        temp_dir_path = storage_path / "temp" / task_id
        
        uploads_dir.mkdir(parents=True, exist_ok=True)
        outputs_dir.mkdir(parents=True, exist_ok=True)
        temp_dir_path.mkdir(parents=True, exist_ok=True)
        
        # Create task-specific files
        upload_file = uploads_dir / f"{task_id}_input.pdf"
        output_file = outputs_dir / f"{task_id}_output.pdf"
        temp_file = temp_dir_path / "temp_data.tmp"
        
        upload_file.write_text("upload content")
        output_file.write_text("output content")
        temp_file.write_text("temp content")
        
        print(f"Created task files:")
        print(f"  Upload: {upload_file.exists()}")
        print(f"  Output: {output_file.exists()}")
        print(f"  Temp: {temp_file.exists()}")
        
        # Clean up task files
        cleanup_success = file_storage.cleanup_task_files(session_id, task_id)
        print(f"Cleanup success: {cleanup_success}")
        
        # Verify files were deleted
        print(f"Files after cleanup:")
        print(f"  Upload: {upload_file.exists()}")
        print(f"  Output: {output_file.exists()}")
        print(f"  Temp: {temp_file.exists()}")
        
        assert not upload_file.exists(), "Upload file should have been deleted"
        assert not output_file.exists(), "Output file should have been deleted"
        assert not temp_file.exists(), "Temp file should have been deleted"
        assert cleanup_success, "Cleanup should have succeeded"
        
        print("✅ Task file cleanup test passed!")


if __name__ == "__main__":
    print("Running cleanup functionality tests...\n")
    
    try:
        test_file_cleanup()
        test_storage_monitoring()
        test_task_file_cleanup()
        
        print("\n🎉 All cleanup tests passed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)