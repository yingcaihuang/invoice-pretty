"""
End-to-end testing for complete user workflows
Tests complete user journeys from upload to download
"""
import asyncio
import json
import os
import tempfile
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional

import pytest
import requests
from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

from app.main import app


class E2ETestClient:
    """Enhanced test client for end-to-end testing"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session_id: Optional[str] = None
        self.session = requests.Session()
        
    def create_session(self) -> str:
        """Create a new session and store the session ID"""
        response = self.session.post(f"{self.base_url}/api/session")
        response.raise_for_status()
        data = response.json()
        self.session_id = data["session_id"]
        self.session.headers.update({"X-Session-ID": self.session_id})
        return self.session_id
    
    def upload_files(self, files: List[tuple]) -> Dict:
        """Upload files and return task information"""
        if not self.session_id:
            raise ValueError("Session not created")
            
        files_data = []
        for filename, content in files:
            files_data.append(("files", (filename, content, "application/pdf")))
        
        response = self.session.post(f"{self.base_url}/api/upload", files=files_data)
        response.raise_for_status()
        return response.json()
    
    def get_task_status(self, task_id: str) -> Dict:
        """Get task status"""
        response = self.session.get(f"{self.base_url}/api/task/{task_id}/status")
        response.raise_for_status()
        return response.json()
    
    def wait_for_completion(self, task_id: str, timeout: int = 60) -> Dict:
        """Wait for task completion with timeout"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            status = self.get_task_status(task_id)
            if status["status"] in ["completed", "failed"]:
                return status
            time.sleep(1)
        raise TimeoutError(f"Task {task_id} did not complete within {timeout} seconds")
    
    def download_file(self, task_id: str, filename: str) -> bytes:
        """Download a processed file"""
        response = self.session.get(f"{self.base_url}/api/download/{task_id}/{filename}")
        response.raise_for_status()
        return response.content
    
    def health_check(self) -> Dict:
        """Check application health"""
        response = self.session.get(f"{self.base_url}/api/health")
        response.raise_for_status()
        return response.json()


def create_test_pdf(filename: str, content: str = "Test PDF Content") -> bytes:
    """Create a test PDF file"""
    from io import BytesIO
    buffer = BytesIO()
    
    # Create PDF with reportlab
    c = canvas.Canvas(buffer, pagesize=letter)
    c.drawString(100, 750, content)
    c.drawString(100, 730, f"Filename: {filename}")
    c.drawString(100, 710, f"Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    c.save()
    
    buffer.seek(0)
    return buffer.read()


def create_test_zip(pdf_files: Dict[str, str]) -> bytes:
    """Create a test ZIP file containing PDF files"""
    import zipfile
    from io import BytesIO
    
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for filename, content in pdf_files.items():
            pdf_data = create_test_pdf(filename, content)
            zip_file.writestr(filename, pdf_data)
    
    zip_buffer.seek(0)
    return zip_buffer.read()


class TestCompleteUserWorkflows:
    """Test complete user workflows from upload to download"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def e2e_client(self):
        """Create E2E test client"""
        return E2ETestClient()
    
    def test_single_pdf_upload_and_processing(self, e2e_client):
        """Test complete workflow: single PDF upload -> processing -> download"""
        # Create session
        session_id = e2e_client.create_session()
        assert session_id
        assert len(session_id) == 36  # UUID length
        
        # Create test PDF
        pdf_content = create_test_pdf("test_invoice.pdf", "Invoice #12345")
        
        # Upload file
        upload_result = e2e_client.upload_files([("test_invoice.pdf", pdf_content)])
        assert upload_result["status"] == "queued"
        task_id = upload_result["taskId"]
        assert task_id
        
        # Wait for processing completion
        final_status = e2e_client.wait_for_completion(task_id, timeout=30)
        assert final_status["status"] == "completed"
        assert "downloadUrls" in final_status
        assert len(final_status["downloadUrls"]) > 0
        
        # Download processed file
        download_url = final_status["downloadUrls"][0]
        filename = download_url.split("/")[-1]
        processed_content = e2e_client.download_file(task_id, filename)
        assert len(processed_content) > 0
        assert processed_content.startswith(b"%PDF")  # Valid PDF header
    
    def test_multiple_pdf_batch_processing(self, e2e_client):
        """Test batch processing of multiple PDF files"""
        # Create session
        session_id = e2e_client.create_session()
        
        # Create multiple test PDFs
        pdf_files = [
            ("invoice_001.pdf", create_test_pdf("invoice_001.pdf", "Invoice #001")),
            ("invoice_002.pdf", create_test_pdf("invoice_002.pdf", "Invoice #002")),
            ("invoice_003.pdf", create_test_pdf("invoice_003.pdf", "Invoice #003"))
        ]
        
        # Upload batch
        upload_result = e2e_client.upload_files(pdf_files)
        assert upload_result["status"] == "queued"
        task_id = upload_result["taskId"]
        
        # Wait for completion
        final_status = e2e_client.wait_for_completion(task_id, timeout=45)
        assert final_status["status"] == "completed"
        assert len(final_status["downloadUrls"]) > 0
        
        # Verify all files can be downloaded
        for download_url in final_status["downloadUrls"]:
            filename = download_url.split("/")[-1]
            content = e2e_client.download_file(task_id, filename)
            assert len(content) > 0
            assert content.startswith(b"%PDF")
    
    def test_zip_file_processing(self, e2e_client):
        """Test ZIP file upload and processing"""
        # Create session
        session_id = e2e_client.create_session()
        
        # Create ZIP with multiple PDFs
        pdf_files = {
            "doc1.pdf": "Document 1 Content",
            "doc2.pdf": "Document 2 Content",
            "subfolder/doc3.pdf": "Document 3 Content"
        }
        zip_content = create_test_zip(pdf_files)
        
        # Upload ZIP
        upload_result = e2e_client.upload_files([("test_archive.zip", zip_content)])
        assert upload_result["status"] == "queued"
        task_id = upload_result["taskId"]
        
        # Wait for completion
        final_status = e2e_client.wait_for_completion(task_id, timeout=60)
        assert final_status["status"] == "completed"
        assert len(final_status["downloadUrls"]) > 0
        
        # Download and verify processed files
        for download_url in final_status["downloadUrls"]:
            filename = download_url.split("/")[-1]
            content = e2e_client.download_file(task_id, filename)
            assert len(content) > 0
            assert content.startswith(b"%PDF")
    
    def test_error_handling_invalid_files(self, e2e_client):
        """Test error handling for invalid file uploads"""
        # Create session
        session_id = e2e_client.create_session()
        
        # Try to upload invalid file type
        invalid_content = b"This is not a PDF file"
        
        try:
            upload_result = e2e_client.upload_files([("invalid.txt", invalid_content)])
            # Should either reject immediately or fail during processing
            if upload_result["status"] == "queued":
                final_status = e2e_client.wait_for_completion(upload_result["taskId"], timeout=30)
                assert final_status["status"] == "failed"
                assert "error" in final_status or "message" in final_status
        except requests.exceptions.HTTPError as e:
            # Immediate rejection is also acceptable
            assert e.response.status_code in [400, 422]
    
    def test_large_file_handling(self, e2e_client):
        """Test handling of large files within limits"""
        # Create session
        session_id = e2e_client.create_session()
        
        # Create a larger PDF (but within limits)
        large_pdf = create_large_test_pdf("large_invoice.pdf", pages=10)
        
        # Upload large file
        upload_result = e2e_client.upload_files([("large_invoice.pdf", large_pdf)])
        assert upload_result["status"] == "queued"
        task_id = upload_result["taskId"]
        
        # Wait for completion (longer timeout for large files)
        final_status = e2e_client.wait_for_completion(task_id, timeout=120)
        assert final_status["status"] == "completed"
        assert len(final_status["downloadUrls"]) > 0
    
    def test_concurrent_task_isolation(self, e2e_client):
        """Test that concurrent tasks from same session are properly isolated"""
        # Create session
        session_id = e2e_client.create_session()
        
        # Create multiple different PDFs
        pdf1 = create_test_pdf("task1.pdf", "Task 1 Content")
        pdf2 = create_test_pdf("task2.pdf", "Task 2 Content")
        
        # Upload files concurrently
        upload1 = e2e_client.upload_files([("task1.pdf", pdf1)])
        upload2 = e2e_client.upload_files([("task2.pdf", pdf2)])
        
        task1_id = upload1["taskId"]
        task2_id = upload2["taskId"]
        
        # Verify different task IDs
        assert task1_id != task2_id
        
        # Wait for both to complete
        status1 = e2e_client.wait_for_completion(task1_id, timeout=30)
        status2 = e2e_client.wait_for_completion(task2_id, timeout=30)
        
        assert status1["status"] == "completed"
        assert status2["status"] == "completed"
        
        # Verify each task only returns its own files
        assert status1["taskId"] == task1_id
        assert status2["taskId"] == task2_id
    
    def test_progress_tracking(self, e2e_client):
        """Test real-time progress tracking during processing"""
        # Create session
        session_id = e2e_client.create_session()
        
        # Create test file
        pdf_content = create_test_pdf("progress_test.pdf", "Progress Test")
        
        # Upload file
        upload_result = e2e_client.upload_files([("progress_test.pdf", pdf_content)])
        task_id = upload_result["taskId"]
        
        # Monitor progress
        progress_values = []
        start_time = time.time()
        
        while time.time() - start_time < 30:
            status = e2e_client.get_task_status(task_id)
            progress_values.append(status.get("progress", 0))
            
            if status["status"] in ["completed", "failed"]:
                break
            time.sleep(0.5)
        
        # Verify progress tracking
        assert len(progress_values) > 0
        final_progress = progress_values[-1]
        
        if status["status"] == "completed":
            assert final_progress == 100
        
        # Verify progress is monotonic (non-decreasing)
        for i in range(1, len(progress_values)):
            assert progress_values[i] >= progress_values[i-1], f"Progress decreased: {progress_values[i-1]} -> {progress_values[i]}"


def create_large_test_pdf(filename: str, pages: int = 5) -> bytes:
    """Create a larger test PDF with multiple pages"""
    from io import BytesIO
    buffer = BytesIO()
    
    c = canvas.Canvas(buffer, pagesize=letter)
    
    for page in range(pages):
        c.drawString(100, 750, f"Page {page + 1} of {pages}")
        c.drawString(100, 730, f"Filename: {filename}")
        c.drawString(100, 710, f"Large content page {page + 1}")
        
        # Add some content to make it larger
        for i in range(20):
            c.drawString(100, 690 - i * 20, f"Line {i + 1}: This is test content for a larger PDF file")
        
        if page < pages - 1:
            c.showPage()
    
    c.save()
    buffer.seek(0)
    return buffer.read()


class TestSessionIsolation:
    """Test session isolation across multiple browsers/sessions"""
    
    def test_multiple_session_isolation(self):
        """Test that multiple sessions cannot access each other's tasks"""
        # Create two separate clients (simulating different browsers)
        client1 = E2ETestClient()
        client2 = E2ETestClient()
        
        # Create separate sessions
        session1_id = client1.create_session()
        session2_id = client2.create_session()
        
        assert session1_id != session2_id
        
        # Upload file in session 1
        pdf_content = create_test_pdf("session1_file.pdf", "Session 1 Content")
        upload1 = client1.upload_files([("session1_file.pdf", pdf_content)])
        task1_id = upload1["taskId"]
        
        # Upload file in session 2
        pdf_content2 = create_test_pdf("session2_file.pdf", "Session 2 Content")
        upload2 = client2.upload_files([("session2_file.pdf", pdf_content2)])
        task2_id = upload2["taskId"]
        
        # Wait for completion
        status1 = client1.wait_for_completion(task1_id, timeout=30)
        status2 = client2.wait_for_completion(task2_id, timeout=30)
        
        # Verify session 1 cannot access session 2's task
        try:
            client1.get_task_status(task2_id)
            assert False, "Session 1 should not be able to access Session 2's task"
        except requests.exceptions.HTTPError as e:
            assert e.response.status_code in [401, 403, 404]
        
        # Verify session 2 cannot access session 1's task
        try:
            client2.get_task_status(task1_id)
            assert False, "Session 2 should not be able to access Session 1's task"
        except requests.exceptions.HTTPError as e:
            assert e.response.status_code in [401, 403, 404]
        
        # Verify each session can access its own tasks
        own_status1 = client1.get_task_status(task1_id)
        own_status2 = client2.get_task_status(task2_id)
        
        assert own_status1["taskId"] == task1_id
        assert own_status2["taskId"] == task2_id
    
    def test_session_without_header(self):
        """Test that requests without session headers are rejected"""
        client = requests.Session()  # No session header
        
        # Try to upload without session
        pdf_content = create_test_pdf("no_session.pdf", "No Session Test")
        files = [("files", ("no_session.pdf", pdf_content, "application/pdf"))]
        
        response = client.post("http://localhost:8000/api/upload", files=files)
        assert response.status_code == 400
        
        error_data = response.json()
        assert error_data["error"] is True
        assert "session" in error_data["message"].lower()


class TestErrorHandlingAndEdgeCases:
    """Test comprehensive error handling and edge cases"""
    
    def test_invalid_task_id_format(self, e2e_client):
        """Test handling of invalid task ID formats"""
        session_id = e2e_client.create_session()
        
        # Test various invalid task ID formats
        invalid_ids = [
            "not-a-uuid",
            "12345",
            "",
            "invalid-uuid-format-too-long-to-be-valid",
            "00000000-0000-0000-0000-000000000000"  # Valid format but non-existent
        ]
        
        for invalid_id in invalid_ids:
            try:
                e2e_client.get_task_status(invalid_id)
                assert False, f"Should have failed for invalid ID: {invalid_id}"
            except requests.exceptions.HTTPError as e:
                assert e.response.status_code in [400, 404]
    
    def test_download_non_existent_file(self, e2e_client):
        """Test downloading non-existent files"""
        session_id = e2e_client.create_session()
        
        # Create and complete a task
        pdf_content = create_test_pdf("test.pdf", "Test Content")
        upload_result = e2e_client.upload_files([("test.pdf", pdf_content)])
        task_id = upload_result["taskId"]
        
        final_status = e2e_client.wait_for_completion(task_id, timeout=30)
        assert final_status["status"] == "completed"
        
        # Try to download non-existent file
        try:
            e2e_client.download_file(task_id, "non_existent_file.pdf")
            assert False, "Should have failed for non-existent file"
        except requests.exceptions.HTTPError as e:
            assert e.response.status_code == 404
    
    def test_system_health_during_load(self, e2e_client):
        """Test system health check during processing load"""
        # Check initial health
        health = e2e_client.health_check()
        assert health["status"] in ["healthy", "degraded"]
        
        # Create multiple concurrent tasks
        clients = [E2ETestClient() for _ in range(3)]
        tasks = []
        
        for i, client in enumerate(clients):
            client.create_session()
            pdf_content = create_test_pdf(f"load_test_{i}.pdf", f"Load Test {i}")
            upload_result = client.upload_files([(f"load_test_{i}.pdf", pdf_content)])
            tasks.append((client, upload_result["taskId"]))
        
        # Check health during processing
        health_during_load = e2e_client.health_check()
        assert health_during_load["status"] in ["healthy", "degraded"]
        
        # Wait for all tasks to complete
        for client, task_id in tasks:
            status = client.wait_for_completion(task_id, timeout=60)
            assert status["status"] == "completed"
        
        # Check health after processing
        final_health = e2e_client.health_check()
        assert final_health["status"] in ["healthy", "degraded"]


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v", "--tb=short"])