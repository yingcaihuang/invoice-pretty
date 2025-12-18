#!/usr/bin/env python3
"""
Property-based tests for cleanup and maintenance functionality.

**Feature: web-invoice-processor, Property 24: Complete file removal**
**Feature: web-invoice-processor, Property 25: Cleanup status updates**

This module tests cleanup and maintenance properties using Hypothesis
for property-based testing to ensure correctness across many inputs.
"""

import os
import sys
import tempfile
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict
from unittest.mock import Mock, patch

import pytest
from hypothesis import given, strategies as st, settings, assume
from hypothesis.strategies import composite

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from app.models.data_models import Task, TaskStatus, FileUpload
from app.services.file_storage import FileStorageManager
from app.services.task_storage import TaskStorageInterface


# Custom strategies for generating test data
@composite
def valid_uuid_string(draw):
    """Generate valid UUID strings."""
    return str(uuid.uuid4())


@composite
def valid_session_id(draw):
    """Generate valid session IDs."""
    return draw(valid_uuid_string())


@composite
def valid_task_id(draw):
    """Generate valid task IDs."""
    return draw(valid_uuid_string())


@composite
def valid_filename(draw):
    """Generate valid filenames."""
    base_name = draw(st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')),
        min_size=1,
        max_size=50
    ))
    extension = draw(st.sampled_from(['.pdf', '.zip']))
    return f"{base_name}{extension}"


@composite
def file_content(draw):
    """Generate file content."""
    return draw(st.binary(min_size=1, max_size=1024))


@composite
def age_hours(draw):
    """Generate file age in hours."""
    return draw(st.integers(min_value=1, max_value=100))


class TestCleanupMaintenanceProperties:
    """Property-based tests for cleanup and maintenance functionality."""
    
    def setup_method(self):
        """Set up test environment for each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.file_storage = FileStorageManager(base_storage_path=self.temp_dir)
    
    def teardown_method(self):
        """Clean up test environment after each test method."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @given(
        session_id=valid_session_id(),
        task_id=valid_task_id(),
        input_files=st.lists(valid_filename(), min_size=1, max_size=5),
        output_files=st.lists(valid_filename(), min_size=1, max_size=5),
        file_contents=st.lists(file_content(), min_size=1, max_size=10)
    )
    @settings(max_examples=100)
    def test_property_24_complete_file_removal(self, session_id, task_id, input_files, output_files, file_contents):
        """
        **Feature: web-invoice-processor, Property 24: Complete file removal**
        **Validates: Requirements 8.2**
        
        For any cleanup operation, both input and output files should be removed from storage.
        """
        assume(len(file_contents) >= max(len(input_files), len(output_files)))
        
        # Store input files (simulate uploads)
        stored_input_paths = []
        for i, filename in enumerate(input_files):
            content = file_contents[i % len(file_contents)]
            
            # Create mock upload file
            mock_file = Mock()
            mock_file.filename = filename
            mock_file.content_type = "application/pdf"
            mock_file.file = Mock()
            mock_file.file.read = Mock(return_value=content)
            
            # Mock copyfileobj
            def mock_copyfileobj(src, dst, content=content):
                dst.write(content)
            
            import shutil
            original_copyfileobj = shutil.copyfileobj
            shutil.copyfileobj = mock_copyfileobj
            
            try:
                result = self.file_storage.store_upload(session_id, task_id, mock_file)
                if result:
                    stored_input_paths.append(result.upload_path)
            finally:
                shutil.copyfileobj = original_copyfileobj
        
        # Store output files
        stored_output_paths = []
        for i, filename in enumerate(output_files):
            content = file_contents[(i + len(input_files)) % len(file_contents)]
            output_path = self.file_storage.store_output(session_id, task_id, content, filename)
            if output_path:
                stored_output_paths.append(str(output_path))
        
        # Create temp directory for the task
        temp_dir = self.file_storage.create_temp_directory(task_id)
        if temp_dir:
            # Create some temp files
            temp_file = temp_dir / "temp_data.tmp"
            temp_file.write_bytes(b"temporary data")
        
        # Verify all files exist before cleanup
        for path_str in stored_input_paths:
            path = Path(path_str)
            assert path.exists(), f"Input file {path} should exist before cleanup"
        
        for path_str in stored_output_paths:
            path = Path(path_str)
            assert path.exists(), f"Output file {path} should exist before cleanup"
        
        if temp_dir:
            assert temp_dir.exists(), "Temp directory should exist before cleanup"
        
        # Perform cleanup
        cleanup_success = self.file_storage.cleanup_task_files(session_id, task_id)
        assert cleanup_success == True, "Cleanup should succeed"
        
        # Verify all files are removed after cleanup
        for path_str in stored_input_paths:
            path = Path(path_str)
            assert not path.exists(), f"Input file {path} should be removed after cleanup"
        
        for path_str in stored_output_paths:
            path = Path(path_str)
            assert not path.exists(), f"Output file {path} should be removed after cleanup"
        
        if temp_dir:
            assert not temp_dir.exists(), "Temp directory should be removed after cleanup"
        
        # Verify files are no longer accessible through the storage interface
        for filename in input_files:
            upload_path = self.file_storage.get_upload_path(session_id, task_id, filename)
            assert upload_path is None, f"Input file {filename} should not be accessible after cleanup"
        
        for filename in output_files:
            output_path = self.file_storage.get_output_path(session_id, task_id, filename)
            assert output_path is None, f"Output file {filename} should not be accessible after cleanup"
    
    @given(
        session_ids=st.lists(valid_session_id(), min_size=2, max_size=5),
        task_ids=st.lists(valid_task_id(), min_size=2, max_size=5),
        filenames=st.lists(valid_filename(), min_size=2, max_size=10),
        file_contents=st.lists(file_content(), min_size=2, max_size=10),
        old_hours=st.integers(min_value=25, max_value=100),  # Older than 24 hours
        new_hours=st.integers(min_value=1, max_value=23)     # Newer than 24 hours
    )
    @settings(max_examples=100)
    def test_property_25_cleanup_status_updates(self, session_ids, task_ids, filenames, file_contents, old_hours, new_hours):
        """
        **Feature: web-invoice-processor, Property 25: Cleanup status updates**
        **Validates: Requirements 8.3**
        
        For any task that undergoes cleanup, its status should be updated to indicate 
        files are no longer available.
        """
        assume(len(session_ids) >= 2)
        assume(len(task_ids) >= 2)
        assume(len(filenames) >= 2)
        assume(len(file_contents) >= 2)
        
        # Create old and new files
        old_files = []
        new_files = []
        
        # Create old files (will be cleaned up)
        for i in range(min(2, len(session_ids), len(task_ids))):
            session_id = session_ids[i]
            task_id = task_ids[i]
            filename = filenames[i % len(filenames)]
            content = file_contents[i % len(file_contents)]
            
            # Store output file
            output_path = self.file_storage.store_output(session_id, task_id, content, filename)
            if output_path:
                old_files.append((session_id, task_id, filename, output_path))
                
                # Make file old by modifying timestamp
                old_timestamp = time.time() - (old_hours * 3600)
                os.utime(output_path, (old_timestamp, old_timestamp))
        
        # Create new files (will not be cleaned up)
        start_idx = min(2, len(session_ids), len(task_ids))
        for i in range(start_idx, min(start_idx + 2, len(session_ids), len(task_ids))):
            if i < len(session_ids) and i < len(task_ids):
                session_id = session_ids[i]
                task_id = task_ids[i]
                filename = filenames[i % len(filenames)]
                content = file_contents[i % len(file_contents)]
                
                # Store output file
                output_path = self.file_storage.store_output(session_id, task_id, content, filename)
                if output_path:
                    new_files.append((session_id, task_id, filename, output_path))
                    
                    # Make file new by modifying timestamp
                    new_timestamp = time.time() - (new_hours * 3600)
                    os.utime(output_path, (new_timestamp, new_timestamp))
        
        # Verify files exist before cleanup
        for session_id, task_id, filename, output_path in old_files:
            assert output_path.exists(), f"Old file {filename} should exist before cleanup"
            access = self.file_storage.verify_file_access(session_id, task_id, filename, "output")
            assert access == True, f"Old file {filename} should be accessible before cleanup"
        
        for session_id, task_id, filename, output_path in new_files:
            assert output_path.exists(), f"New file {filename} should exist before cleanup"
            access = self.file_storage.verify_file_access(session_id, task_id, filename, "output")
            assert access == True, f"New file {filename} should be accessible before cleanup"
        
        # Run cleanup for files older than 24 hours
        cleanup_stats = self.file_storage.cleanup_old_files(max_age_hours=24)
        
        # Verify cleanup statistics
        assert cleanup_stats["outputs_deleted"] >= len(old_files), f"Should delete at least {len(old_files)} old files"
        assert cleanup_stats["errors"] == 0, "Cleanup should not have errors"
        
        # Verify old files are cleaned up and no longer accessible
        for session_id, task_id, filename, output_path in old_files:
            assert not output_path.exists(), f"Old file {filename} should be removed after cleanup"
            
            # File should no longer be accessible through storage interface
            retrieved_path = self.file_storage.get_output_path(session_id, task_id, filename)
            assert retrieved_path is None, f"Old file {filename} should not be retrievable after cleanup"
            
            # Access verification should return False
            access = self.file_storage.verify_file_access(session_id, task_id, filename, "output")
            assert access == False, f"Old file {filename} should not be accessible after cleanup"
        
        # Verify new files are preserved and still accessible
        for session_id, task_id, filename, output_path in new_files:
            assert output_path.exists(), f"New file {filename} should still exist after cleanup"
            
            # File should still be accessible through storage interface
            retrieved_path = self.file_storage.get_output_path(session_id, task_id, filename)
            assert retrieved_path is not None, f"New file {filename} should still be retrievable after cleanup"
            
            # Access verification should return True
            access = self.file_storage.verify_file_access(session_id, task_id, filename, "output")
            assert access == True, f"New file {filename} should still be accessible after cleanup"
    
    @given(
        session_id=valid_session_id(),
        task_ids=st.lists(valid_task_id(), min_size=3, max_size=10),
        filenames=st.lists(valid_filename(), min_size=3, max_size=10),
        file_contents=st.lists(file_content(), min_size=3, max_size=10)
    )
    @settings(max_examples=100)
    def test_storage_usage_monitoring_property(self, session_id, task_ids, filenames, file_contents):
        """
        Test that storage usage monitoring accurately reflects file operations.
        This supports Properties 24 and 25 by ensuring accurate storage tracking.
        """
        assume(len(task_ids) >= 3)
        assume(len(filenames) >= 3)
        assume(len(file_contents) >= 3)
        
        # Get initial storage usage
        initial_usage = self.file_storage.get_storage_usage()
        initial_total = initial_usage["total_size"]
        
        # Store files and track expected size increase
        expected_size_increase = 0
        stored_files = []
        
        for i in range(min(3, len(task_ids))):
            task_id = task_ids[i]
            filename = filenames[i % len(filenames)]
            content = file_contents[i % len(file_contents)]
            
            # Store output file
            output_path = self.file_storage.store_output(session_id, task_id, content, filename)
            if output_path:
                stored_files.append((task_id, filename, len(content)))
                expected_size_increase += len(content)
        
        # Check storage usage after storing files
        after_store_usage = self.file_storage.get_storage_usage()
        after_store_total = after_store_usage["total_size"]
        
        # Storage should have increased
        assert after_store_total >= initial_total, "Storage usage should increase after storing files"
        
        # Clean up some files
        files_to_cleanup = stored_files[:2]  # Clean up first 2 files
        expected_size_decrease = 0
        
        for task_id, filename, file_size in files_to_cleanup:
            cleanup_success = self.file_storage.cleanup_task_files(session_id, task_id)
            if cleanup_success:
                expected_size_decrease += file_size
        
        # Check storage usage after cleanup
        after_cleanup_usage = self.file_storage.get_storage_usage()
        after_cleanup_total = after_cleanup_usage["total_size"]
        
        # Storage should have decreased
        assert after_cleanup_total <= after_store_total, "Storage usage should decrease after cleanup"
        
        # Verify remaining files are still counted
        remaining_files = stored_files[2:]
        for task_id, filename, file_size in remaining_files:
            output_path = self.file_storage.get_output_path(session_id, task_id, filename)
            if output_path and output_path.exists():
                # File should still contribute to storage usage
                assert after_cleanup_total > initial_total, "Remaining files should contribute to storage usage"
    
    @given(
        session_id=valid_session_id(),
        task_id=valid_task_id()
    )
    @settings(max_examples=100)
    def test_cleanup_idempotency_property(self, session_id, task_id):
        """
        Test that cleanup operations are idempotent (can be run multiple times safely).
        This supports Properties 24 and 25 by ensuring cleanup robustness.
        """
        # First cleanup (no files exist)
        cleanup1 = self.file_storage.cleanup_task_files(session_id, task_id)
        assert cleanup1 == True, "Cleanup should succeed even when no files exist"
        
        # Create a file
        content = b"test content"
        output_path = self.file_storage.store_output(session_id, task_id, content, "test.pdf")
        
        if output_path:
            assert output_path.exists(), "File should exist after creation"
            
            # First cleanup (file exists)
            cleanup2 = self.file_storage.cleanup_task_files(session_id, task_id)
            assert cleanup2 == True, "Cleanup should succeed when files exist"
            assert not output_path.exists(), "File should be removed after cleanup"
            
            # Second cleanup (file already removed)
            cleanup3 = self.file_storage.cleanup_task_files(session_id, task_id)
            assert cleanup3 == True, "Cleanup should succeed when files already removed"
            
            # Third cleanup (still no files)
            cleanup4 = self.file_storage.cleanup_task_files(session_id, task_id)
            assert cleanup4 == True, "Multiple cleanups should be idempotent"


class TestTaskStorageCleanupProperties:
    """Property-based tests for task storage cleanup functionality."""
    
    def setup_method(self):
        """Set up test environment for each test method."""
        # Mock Redis for testing
        self.mock_redis = Mock()
        self.mock_redis.ping.return_value = True
        self.mock_redis.keys.return_value = []
        self.mock_redis.smembers.return_value = set()
        self.mock_redis.srem.return_value = 0
        self.mock_redis.exists.return_value = False
        
        with patch('redis.from_url', return_value=self.mock_redis):
            self.task_storage = TaskStorageInterface()
    
    @given(
        session_ids=st.lists(valid_session_id(), min_size=2, max_size=5),
        task_ids=st.lists(valid_task_id(), min_size=2, max_size=10)
    )
    @settings(max_examples=100)
    def test_expired_task_cleanup_property(self, session_ids, task_ids):
        """
        Test that expired task cleanup removes stale references properly.
        This supports Property 25 by ensuring task status consistency.
        """
        assume(len(session_ids) >= 2)
        assume(len(task_ids) >= 2)
        
        # Mock session keys and task IDs
        session_keys = [f"session:{sid}:tasks" for sid in session_ids[:2]]
        self.mock_redis.keys.return_value = session_keys
        
        # Mock stale task IDs (tasks that no longer exist)
        stale_task_ids = task_ids[:3] if len(task_ids) >= 3 else task_ids
        valid_task_ids = task_ids[3:] if len(task_ids) > 3 else []
        
        def mock_smembers(key):
            return set(stale_task_ids + valid_task_ids)
        
        def mock_exists(key):
            # Only valid task keys exist
            for task_id in valid_task_ids:
                if key == f"task:{task_id}":
                    return True
            return False
        
        self.mock_redis.smembers.side_effect = mock_smembers
        self.mock_redis.exists.side_effect = mock_exists
        self.mock_redis.srem.return_value = len(stale_task_ids)
        
        # Run cleanup
        cleaned_count = self.task_storage.cleanup_expired_tasks()
        
        # Verify cleanup results
        expected_cleaned = len(stale_task_ids) * len(session_keys)
        assert cleaned_count == expected_cleaned, f"Should clean {expected_cleaned} stale references"
        
        # Verify srem was called for stale task IDs
        if stale_task_ids:
            assert self.mock_redis.srem.called, "Should remove stale task IDs from session sets"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])