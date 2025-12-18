#!/usr/bin/env python3
"""
Property-based tests for completion and error handling functionality.

**Feature: web-invoice-processor, Property 13: Completion state consistency**
**Feature: web-invoice-processor, Property 14: Failure state handling**
**Feature: web-invoice-processor, Property 20: File serving correctness**
**Feature: web-invoice-processor, Property 22: URL expiration handling**

This module tests completion and error handling properties using Hypothesis
for property-based testing to ensure correctness across many inputs.
"""

import os
import sys
import tempfile
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional
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
def error_message(draw):
    """Generate error messages."""
    return draw(st.text(min_size=1, max_size=200))


@composite
def file_content(draw):
    """Generate file content."""
    return draw(st.binary(min_size=1, max_size=1024))


@composite
def output_filenames(draw):
    """Generate list of output filenames."""
    return draw(st.lists(valid_filename(), min_size=1, max_size=5))


class TestCompletionErrorProperties:
    """Property-based tests for completion and error handling functionality."""
    
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
        output_files=output_filenames(),
        file_contents=st.lists(file_content(), min_size=1, max_size=5)
    )
    @settings(max_examples=100)
    def test_property_13_completion_state_consistency(self, session_id, task_id, output_files, file_contents):
        """
        **Feature: web-invoice-processor, Property 13: Completion state consistency**
        **Validates: Requirements 4.3**
        
        For any task that completes successfully, its status should be "completed" 
        and it should have valid download URLs.
        """
        assume(len(output_files) == len(file_contents))
        
        # Create a task
        task = Task(
            task_id=task_id,
            session_id=session_id,
            input_files=["input.pdf"],
            status=TaskStatus.PROCESSING,
            progress=50
        )
        
        # Store output files
        stored_output_paths = []
        for filename, content in zip(output_files, file_contents):
            output_path = self.file_storage.store_output(session_id, task_id, content, filename)
            if output_path:
                stored_output_paths.append(str(output_path))
        
        # Mark task as completed
        task.mark_completed(stored_output_paths)
        
        # Verify completion state consistency
        assert task.status == TaskStatus.COMPLETED, f"Task status should be COMPLETED, got {task.status}"
        assert task.progress == 100, f"Completed task progress should be 100, got {task.progress}"
        assert task.completed_at is not None, "Completed task should have completion timestamp"
        assert len(task.output_files) == len(stored_output_paths), "Task should have all output files recorded"
        
        # Verify all output files are accessible
        for filename in output_files:
            output_path = self.file_storage.get_output_path(session_id, task_id, filename)
            assert output_path is not None, f"Output file {filename} should be accessible"
            assert output_path.exists(), f"Output file {filename} should exist on disk"
            
            # Verify file access
            access_allowed = self.file_storage.verify_file_access(session_id, task_id, filename, "output")
            assert access_allowed == True, f"Access should be allowed for output file {filename}"
    
    @given(
        session_id=valid_session_id(),
        task_id=valid_task_id(),
        error_msg=error_message()
    )
    @settings(max_examples=100)
    def test_property_14_failure_state_handling(self, session_id, task_id, error_msg):
        """
        **Feature: web-invoice-processor, Property 14: Failure state handling**
        **Validates: Requirements 4.4**
        
        For any task that encounters an error, its status should be "failed" 
        and it should include error details.
        """
        # Create a task in processing state
        task = Task(
            task_id=task_id,
            session_id=session_id,
            input_files=["input.pdf"],
            status=TaskStatus.PROCESSING,
            progress=30
        )
        
        # Mark task as failed
        task.mark_failed(error_msg)
        
        # Verify failure state consistency
        assert task.status == TaskStatus.FAILED, f"Task status should be FAILED, got {task.status}"
        assert task.error_message == error_msg, f"Task should have error message: {error_msg}"
        assert task.updated_at is not None, "Failed task should have updated timestamp"
        assert task.completed_at is None, "Failed task should not have completion timestamp"
        
        # Progress should remain unchanged when task fails
        assert task.progress == 30, "Progress should remain unchanged when task fails"
        
        # Output files should remain empty for failed tasks
        assert len(task.output_files) == 0, "Failed task should not have output files"
    
    @given(
        session_id=valid_session_id(),
        task_id=valid_task_id(),
        filename=valid_filename(),
        content=file_content()
    )
    @settings(max_examples=100)
    def test_property_20_file_serving_correctness(self, session_id, task_id, filename, content):
        """
        **Feature: web-invoice-processor, Property 20: File serving correctness**
        **Validates: Requirements 7.2**
        
        For any valid download request, the system should serve the correct file 
        with appropriate HTTP headers.
        """
        # Store an output file
        output_path = self.file_storage.store_output(session_id, task_id, content, filename)
        assert output_path is not None, "Output file should be stored successfully"
        
        # Retrieve the file
        retrieved_path = self.file_storage.get_output_path(session_id, task_id, filename)
        assert retrieved_path is not None, "Output file should be retrievable"
        assert retrieved_path.exists(), "Retrieved file should exist"
        
        # Verify file content is correct
        with open(retrieved_path, 'rb') as f:
            retrieved_content = f.read()
        
        assert retrieved_content == content, "Retrieved file content should match original content"
        
        # Verify file access permissions
        access_allowed = self.file_storage.verify_file_access(session_id, task_id, filename, "output")
        assert access_allowed == True, "File access should be allowed for correct session and task"
        
        # Verify file size is correct
        expected_size = len(content)
        actual_size = retrieved_path.stat().st_size
        assert actual_size == expected_size, f"File size should be {expected_size}, got {actual_size}"
    
    @given(
        session_id=valid_session_id(),
        task_id=valid_task_id(),
        filename=valid_filename(),
        content=file_content(),
        hours_old=st.integers(min_value=25, max_value=100)  # Files older than 24 hours
    )
    @settings(max_examples=100)
    def test_property_22_url_expiration_handling(self, session_id, task_id, filename, content, hours_old):
        """
        **Feature: web-invoice-processor, Property 22: URL expiration handling**
        **Validates: Requirements 7.4**
        
        For any expired download URL, access attempts should return appropriate error responses.
        """
        # Store an output file
        output_path = self.file_storage.store_output(session_id, task_id, content, filename)
        assert output_path is not None, "Output file should be stored successfully"
        
        # Simulate file aging by modifying its timestamp
        old_timestamp = datetime.now().timestamp() - (hours_old * 3600)
        os.utime(output_path, (old_timestamp, old_timestamp))
        
        # Run cleanup for files older than 24 hours
        cleanup_stats = self.file_storage.cleanup_old_files(max_age_hours=24)
        
        # Verify that old files are cleaned up
        assert cleanup_stats["outputs_deleted"] >= 1, "Old output files should be deleted"
        
        # Verify file is no longer accessible
        retrieved_path = self.file_storage.get_output_path(session_id, task_id, filename)
        assert retrieved_path is None, "Expired file should not be accessible"
        
        # Verify file access is denied
        access_allowed = self.file_storage.verify_file_access(session_id, task_id, filename, "output")
        assert access_allowed == False, "Access should be denied for expired files"
        
        # Verify file no longer exists on disk
        assert not output_path.exists(), "Expired file should not exist on disk"


class TestTaskStorageProperties:
    """Property-based tests for task storage functionality."""
    
    def setup_method(self):
        """Set up test environment for each test method."""
        # Mock Redis for testing
        self.mock_redis = Mock()
        self.mock_redis.ping.return_value = True
        self.mock_redis.pipeline.return_value = self.mock_redis
        self.mock_redis.execute.return_value = [True, True, True]
        self.mock_redis.exists.return_value = True
        self.mock_redis.ttl.return_value = 3600
        
        with patch('redis.from_url', return_value=self.mock_redis):
            self.task_storage = TaskStorageInterface()
    
    @given(
        session_id=valid_session_id(),
        task_id=valid_task_id(),
        progress_values=st.lists(st.integers(min_value=0, max_value=100), min_size=2, max_size=10)
    )
    @settings(max_examples=100)
    def test_progress_monotonic_property(self, session_id, task_id, progress_values):
        """
        Test that progress updates are monotonic (never decrease).
        This supports Properties 13 and 14 by ensuring progress consistency.
        """
        # Sort progress values to ensure they're monotonic
        sorted_progress = sorted(progress_values)
        
        # Create a task
        task = Task(
            task_id=task_id,
            session_id=session_id,
            input_files=["input.pdf"],
            status=TaskStatus.PROCESSING
        )
        
        # Mock task retrieval
        self.mock_redis.get.return_value = task.json()
        
        # Apply progress updates in order
        for progress in sorted_progress:
            success = self.task_storage.update_task_progress_only(task_id, progress)
            assert success == True, f"Progress update to {progress} should succeed"
            
            # Verify progress is updated correctly
            # Since we're mocking Redis, we verify the task object directly
            task.update_progress(progress)
            assert task.progress == progress, f"Task progress should be {progress}"
        
        # Test that progress cannot decrease
        if len(sorted_progress) > 1:
            final_progress = sorted_progress[-1]
            lower_progress = sorted_progress[0]
            
            # Attempting to set lower progress should not decrease the value
            task.update_progress(final_progress)  # Set to final value
            
            # Try to set to lower value - should remain at final value
            try:
                task.update_progress(lower_progress)
                # If no exception, progress should not have decreased
                assert task.progress >= final_progress, "Progress should not decrease"
            except ValueError:
                # Expected behavior - progress update should be rejected
                assert task.progress == final_progress, "Progress should remain at final value"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])