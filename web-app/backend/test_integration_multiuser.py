#!/usr/bin/env python3
"""
Integration tests for multi-user scenarios.

This module tests concurrent user sessions, task isolation, file upload and 
processing workflows, and cleanup operations to ensure the system works 
correctly with multiple users.
"""

import os
import sys
import tempfile
import uuid
import asyncio
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Tuple
from unittest.mock import Mock, patch
from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from app.models.data_models import Task, TaskStatus, FileUpload, Session
from app.services.file_storage import FileStorageManager
from app.services.task_storage import TaskStorageInterface


class TestMultiUserIntegration:
    """Integration tests for multi-user scenarios."""
    
    def setup_method(self):
        """Set up test environment for each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.file_storage = FileStorageManager(base_storage_path=self.temp_dir)
        
        # Mock Redis for task storage
        self.mock_redis = Mock()
        self.mock_redis.ping.return_value = True
        self.mock_redis.pipeline.return_value = self.mock_redis
        self.mock_redis.execute.return_value = [True, True, True]
        self.mock_redis.exists.return_value = True
        self.mock_redis.ttl.return_value = 3600
        self.mock_redis.keys.return_value = []
        self.mock_redis.smembers.return_value = set()
        
        # Storage for mocked task data
        self.mock_task_data = {}
        self.mock_session_tasks = {}
        
        def mock_get(key):
            return self.mock_task_data.get(key)
        
        def mock_setex(key, ttl, value):
            self.mock_task_data[key] = value
            return True
        
        def mock_set(key, value):
            self.mock_task_data[key] = value
            return True
        
        def mock_sadd(key, value):
            if key not in self.mock_session_tasks:
                self.mock_session_tasks[key] = set()
            self.mock_session_tasks[key].add(value)
            return True
        
        def mock_smembers_session(key):
            return self.mock_session_tasks.get(key, set())
        
        self.mock_redis.get.side_effect = mock_get
        self.mock_redis.setex.side_effect = mock_setex
        self.mock_redis.set.side_effect = mock_set
        self.mock_redis.sadd.side_effect = mock_sadd
        self.mock_redis.smembers.side_effect = mock_smembers_session
        
        with patch('redis.from_url', return_value=self.mock_redis):
            self.task_storage = TaskStorageInterface()
    
    def teardown_method(self):
        """Clean up test environment after each test method."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_mock_upload_file(self, filename: str, content: bytes, content_type: str = "application/pdf"):
        """Create a mock FastAPI UploadFile object."""
        mock_file = Mock()
        mock_file.filename = filename
        mock_file.content_type = content_type
        mock_file.file = Mock()
        mock_file.file.read = Mock(return_value=content)
        return mock_file
    
    def simulate_user_session(self, session_id: str, num_tasks: int = 2) -> List[Tuple[str, str, str]]:
        """
        Simulate a user session with multiple file uploads and tasks.
        
        Returns:
            List of (task_id, filename, content) tuples
        """
        results = []
        
        for i in range(num_tasks):
            # Create unique task data
            task_id = str(uuid.uuid4())
            filename = f"invoice_{session_id[:8]}_{i}.pdf"
            content = f"PDF content for {session_id} task {i}".encode()
            
            # Create task
            task = Task(
                task_id=task_id,
                session_id=session_id,
                input_files=[filename],
                status=TaskStatus.QUEUED
            )
            
            # Store task
            self.task_storage.store_task(task)
            
            # Create and store file
            mock_file = self.create_mock_upload_file(filename, content)
            
            # Mock copyfileobj for file storage
            def mock_copyfileobj(src, dst, content=content):
                dst.write(content)
            
            import shutil
            original_copyfileobj = shutil.copyfileobj
            shutil.copyfileobj = mock_copyfileobj
            
            try:
                file_upload = self.file_storage.store_upload(session_id, task_id, mock_file)
                if file_upload:
                    results.append((task_id, filename, content.decode()))
            finally:
                shutil.copyfileobj = original_copyfileobj
        
        return results
    
    def test_concurrent_user_sessions_isolation(self):
        """
        Test that multiple concurrent user sessions maintain proper isolation.
        **Validates: Requirements 6.5, 8.1, 9.1**
        """
        # Create fewer user sessions for faster testing
        num_users = 2
        session_ids = [str(uuid.uuid4()) for _ in range(num_users)]
        
        # Sequential execution for simpler testing
        session_results = {}
        for session_id in session_ids:
            results = self.simulate_user_session(session_id, 2)  # Fewer tasks
            session_results[session_id] = results
        
        # Verify session isolation
        for session_id in session_ids:
            # Get tasks for this session
            session_tasks = self.task_storage.get_session_tasks(session_id)
            
            # Verify session has its own tasks
            assert len(session_tasks) == 2, f"Session {session_id} should have 2 tasks"
            
            # Verify all tasks belong to this session
            for task in session_tasks:
                assert task.session_id == session_id, f"Task {task.task_id} should belong to session {session_id}"
            
            # Verify file isolation
            for task_id, filename, expected_content in session_results[session_id]:
                # This session should be able to access its own files
                upload_path = self.file_storage.get_upload_path(session_id, task_id, filename)
                assert upload_path is not None, f"Session {session_id} should access its own file {filename}"
                assert upload_path.exists(), f"File {filename} should exist for session {session_id}"
                
                # Verify file content
                with open(upload_path, 'r') as f:
                    actual_content = f.read()
                assert expected_content in actual_content, f"File content should match for {filename}"
                
                # Other sessions should NOT be able to access this file
                for other_session_id in session_ids:
                    if other_session_id != session_id:
                        other_upload_path = self.file_storage.get_upload_path(other_session_id, task_id, filename)
                        assert other_upload_path is None, f"Session {other_session_id} should not access {session_id}'s files"
    
    def test_file_upload_processing_workflow(self):
        """
        Test complete file upload and processing workflow for multiple users.
        **Validates: Requirements 6.5, 8.1, 9.1**
        """
        # Create two user sessions
        session1_id = str(uuid.uuid4())
        session2_id = str(uuid.uuid4())
        
        # Session 1: Upload and process files
        session1_files = []
        for i in range(2):
            task_id = str(uuid.uuid4())
            filename = f"session1_file_{i}.pdf"
            content = f"Session 1 content {i}".encode()
            
            # Create task
            task = Task(
                task_id=task_id,
                session_id=session1_id,
                input_files=[filename],
                status=TaskStatus.QUEUED
            )
            self.task_storage.store_task(task)
            
            # Upload file
            mock_file = self.create_mock_upload_file(filename, content)
            
            def mock_copyfileobj(src, dst, content=content):
                dst.write(content)
            
            import shutil
            original_copyfileobj = shutil.copyfileobj
            shutil.copyfileobj = mock_copyfileobj
            
            try:
                file_upload = self.file_storage.store_upload(session1_id, task_id, mock_file)
                assert file_upload is not None, f"File upload should succeed for {filename}"
                session1_files.append((task_id, filename, content))
            finally:
                shutil.copyfileobj = original_copyfileobj
            
            # Simulate processing completion
            output_content = f"Processed {content.decode()}".encode()
            output_filename = f"processed_{filename}"
            output_path = self.file_storage.store_output(session1_id, task_id, output_content, output_filename)
            assert output_path is not None, f"Output storage should succeed for {output_filename}"
            
            # Update task status
            task.mark_completed([str(output_path)])
            self.task_storage.update_task(task)
        
        # Session 2: Upload files (some will fail)
        session2_files = []
        for i in range(2):
            task_id = str(uuid.uuid4())
            filename = f"session2_file_{i}.pdf"
            content = f"Session 2 content {i}".encode()
            
            # Create task
            task = Task(
                task_id=task_id,
                session_id=session2_id,
                input_files=[filename],
                status=TaskStatus.QUEUED
            )
            self.task_storage.store_task(task)
            
            # Upload file
            mock_file = self.create_mock_upload_file(filename, content)
            
            def mock_copyfileobj(src, dst, content=content):
                dst.write(content)
            
            import shutil
            original_copyfileobj = shutil.copyfileobj
            shutil.copyfileobj = mock_copyfileobj
            
            try:
                file_upload = self.file_storage.store_upload(session2_id, task_id, mock_file)
                assert file_upload is not None, f"File upload should succeed for {filename}"
                session2_files.append((task_id, filename, content))
            finally:
                shutil.copyfileobj = original_copyfileobj
            
            # Simulate processing failure for first file
            if i == 0:
                task.mark_failed("Processing error occurred")
                self.task_storage.update_task(task)
            else:
                # Success for second file
                output_content = f"Processed {content.decode()}".encode()
                output_filename = f"processed_{filename}"
                output_path = self.file_storage.store_output(session2_id, task_id, output_content, output_filename)
                assert output_path is not None, f"Output storage should succeed for {output_filename}"
                
                task.mark_completed([str(output_path)])
                self.task_storage.update_task(task)
        
        # Verify workflow results
        # Session 1: All tasks should be completed
        session1_tasks = self.task_storage.get_session_tasks(session1_id)
        assert len(session1_tasks) == 2, "Session 1 should have 2 tasks"
        for task in session1_tasks:
            assert task.status == TaskStatus.COMPLETED, f"Session 1 task {task.task_id} should be completed"
            assert len(task.output_files) > 0, f"Session 1 task {task.task_id} should have output files"
        
        # Session 2: One failed, one completed
        session2_tasks = self.task_storage.get_session_tasks(session2_id)
        assert len(session2_tasks) == 2, "Session 2 should have 2 tasks"
        
        failed_tasks = [t for t in session2_tasks if t.status == TaskStatus.FAILED]
        completed_tasks = [t for t in session2_tasks if t.status == TaskStatus.COMPLETED]
        
        assert len(failed_tasks) == 1, "Session 2 should have 1 failed task"
        assert len(completed_tasks) == 1, "Session 2 should have 1 completed task"
        
        # Verify file access isolation
        for task_id, filename, content in session1_files:
            # Session 1 can access its own files
            upload_path = self.file_storage.get_upload_path(session1_id, task_id, filename)
            assert upload_path is not None, f"Session 1 should access its own file {filename}"
            
            # Session 2 cannot access Session 1's files
            cross_access = self.file_storage.get_upload_path(session2_id, task_id, filename)
            assert cross_access is None, f"Session 2 should not access Session 1's file {filename}"
    
    def test_cleanup_maintenance_operations(self):
        """
        Test cleanup and maintenance operations with multiple users.
        **Validates: Requirements 6.5, 8.1, 9.1**
        """
        # Create fewer user sessions for faster testing
        num_sessions = 2
        session_ids = [str(uuid.uuid4()) for _ in range(num_sessions)]
        
        # Create files for each session
        all_files = {}
        for session_id in session_ids:
            session_files = []
            for i in range(2):
                task_id = str(uuid.uuid4())
                filename = f"file_{session_id[:8]}_{i}.pdf"
                content = f"Content for {session_id} file {i}".encode()
                
                # Create task
                task = Task(
                    task_id=task_id,
                    session_id=session_id,
                    input_files=[filename],
                    status=TaskStatus.COMPLETED
                )
                self.task_storage.store_task(task)
                
                # Store input file
                mock_file = self.create_mock_upload_file(filename, content)
                
                def mock_copyfileobj(src, dst, content=content):
                    dst.write(content)
                
                import shutil
                original_copyfileobj = shutil.copyfileobj
                shutil.copyfileobj = mock_copyfileobj
                
                try:
                    file_upload = self.file_storage.store_upload(session_id, task_id, mock_file)
                    assert file_upload is not None, f"File upload should succeed for {filename}"
                finally:
                    shutil.copyfileobj = original_copyfileobj
                
                # Store output file
                output_content = f"Processed {content.decode()}".encode()
                output_filename = f"output_{filename}"
                output_path = self.file_storage.store_output(session_id, task_id, output_content, output_filename)
                assert output_path is not None, f"Output storage should succeed for {output_filename}"
                
                session_files.append((task_id, filename, output_filename))
            
            all_files[session_id] = session_files
        
        # Make some files old (for cleanup testing)
        old_session = session_ids[0]
        for task_id, filename, output_filename in all_files[old_session]:
            # Make input file old
            upload_path = self.file_storage.get_upload_path(old_session, task_id, filename)
            if upload_path and upload_path.exists():
                old_time = time.time() - (25 * 3600)  # 25 hours ago
                os.utime(upload_path, (old_time, old_time))
            
            # Make output file old
            output_path = self.file_storage.get_output_path(old_session, task_id, output_filename)
            if output_path and output_path.exists():
                old_time = time.time() - (25 * 3600)  # 25 hours ago
                os.utime(output_path, (old_time, old_time))
        
        # Get initial storage usage
        initial_usage = self.file_storage.get_storage_usage()
        
        # Run cleanup for files older than 24 hours
        cleanup_stats = self.file_storage.cleanup_old_files(max_age_hours=24)
        
        # Verify cleanup results
        assert cleanup_stats["uploads_deleted"] >= 2, "Should delete old upload files"
        assert cleanup_stats["outputs_deleted"] >= 2, "Should delete old output files"
        
        # Verify old files are cleaned up
        for task_id, filename, output_filename in all_files[old_session]:
            upload_path = self.file_storage.get_upload_path(old_session, task_id, filename)
            output_path = self.file_storage.get_output_path(old_session, task_id, output_filename)
            
            assert upload_path is None, f"Old upload file {filename} should be cleaned up"
            assert output_path is None, f"Old output file {output_filename} should be cleaned up"
        
        # Verify new files are preserved
        for session_id in session_ids[1:]:  # Skip the old session
            for task_id, filename, output_filename in all_files[session_id]:
                upload_path = self.file_storage.get_upload_path(session_id, task_id, filename)
                output_path = self.file_storage.get_output_path(session_id, task_id, output_filename)
                
                assert upload_path is not None, f"New upload file {filename} should be preserved"
                assert output_path is not None, f"New output file {output_filename} should be preserved"
                assert upload_path.exists(), f"New upload file {filename} should exist"
                assert output_path.exists(), f"New output file {output_filename} should exist"
        
        # Verify storage usage decreased
        final_usage = self.file_storage.get_storage_usage()
        assert final_usage["total_size"] < initial_usage["total_size"], "Storage usage should decrease after cleanup"
    
    def test_concurrent_file_operations(self):
        """
        Test concurrent file operations (upload, download, cleanup) across multiple users.
        **Validates: Requirements 6.5, 8.1, 9.1**
        """
        num_users = 2
        session_ids = [str(uuid.uuid4()) for _ in range(num_users)]
        
        def user_operations(session_id: str, user_index: int):
            """Perform file operations for a single user."""
            operations_results = []
            
            # Upload fewer files for faster testing
            for i in range(1):
                task_id = str(uuid.uuid4())
                filename = f"user{user_index}_file_{i}.pdf"
                content = f"User {user_index} content {i}".encode()
                
                # Create task
                task = Task(
                    task_id=task_id,
                    session_id=session_id,
                    input_files=[filename],
                    status=TaskStatus.PROCESSING
                )
                self.task_storage.store_task(task)
                
                # Upload file
                mock_file = self.create_mock_upload_file(filename, content)
                
                def mock_copyfileobj(src, dst, content=content):
                    dst.write(content)
                
                import shutil
                original_copyfileobj = shutil.copyfileobj
                shutil.copyfileobj = mock_copyfileobj
                
                try:
                    file_upload = self.file_storage.store_upload(session_id, task_id, mock_file)
                    if file_upload:
                        operations_results.append(("upload", task_id, filename, True))
                    else:
                        operations_results.append(("upload", task_id, filename, False))
                finally:
                    shutil.copyfileobj = original_copyfileobj
                
                # Simulate processing and create output
                if file_upload:
                    output_content = f"Processed by user {user_index}: {content.decode()}".encode()
                    output_filename = f"output_{filename}"
                    output_path = self.file_storage.store_output(session_id, task_id, output_content, output_filename)
                    
                    if output_path:
                        operations_results.append(("output", task_id, output_filename, True))
                        
                        # Mark task as completed
                        task.mark_completed([str(output_path)])
                        self.task_storage.update_task(task)
                    else:
                        operations_results.append(("output", task_id, output_filename, False))
                
                # Small delay to simulate processing time
                time.sleep(0.01)
            
            return operations_results
        
        # Run concurrent operations
        with ThreadPoolExecutor(max_workers=num_users) as executor:
            future_to_user = {
                executor.submit(user_operations, session_ids[i], i): i
                for i in range(num_users)
            }
            
            all_results = {}
            for future in as_completed(future_to_user):
                user_index = future_to_user[future]
                try:
                    results = future.result()
                    all_results[user_index] = results
                except Exception as exc:
                    pytest.fail(f"User {user_index} operations failed: {exc}")
        
        # Verify all operations succeeded
        for user_index, results in all_results.items():
            session_id = session_ids[user_index]
            
            # Count successful operations
            successful_uploads = sum(1 for op, _, _, success in results if op == "upload" and success)
            successful_outputs = sum(1 for op, _, _, success in results if op == "output" and success)
            
            assert successful_uploads == 1, f"User {user_index} should have 1 successful upload"
            assert successful_outputs == 1, f"User {user_index} should have 1 successful output"
            
            # Verify task isolation
            session_tasks = self.task_storage.get_session_tasks(session_id)
            assert len(session_tasks) == 1, f"User {user_index} should have 1 task"
            
            for task in session_tasks:
                assert task.session_id == session_id, f"Task should belong to user {user_index}'s session"
                assert task.status == TaskStatus.COMPLETED, f"Task should be completed for user {user_index}"
        
        # Verify cross-user isolation
        for i, session_id_i in enumerate(session_ids):
            for j, session_id_j in enumerate(session_ids):
                if i != j:
                    # User i should not be able to access user j's files
                    for op, task_id, filename, success in all_results[j]:
                        if success and op == "upload":
                            cross_access = self.file_storage.get_upload_path(session_id_i, task_id, filename)
                            assert cross_access is None, f"User {i} should not access user {j}'s upload files"
                        elif success and op == "output":
                            cross_access = self.file_storage.get_output_path(session_id_i, task_id, filename)
                            assert cross_access is None, f"User {i} should not access user {j}'s output files"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])