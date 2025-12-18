"""
Performance and load testing for the web invoice processor
Tests concurrent user capacity, file processing performance, memory usage, and system behavior under load
"""
import asyncio
import concurrent.futures
import gc
import json
import os
import psutil
import statistics
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import pytest
import requests
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO


@dataclass
class PerformanceMetrics:
    """Container for performance metrics"""
    response_times: List[float]
    success_count: int
    error_count: int
    throughput: float  # requests per second
    memory_usage: List[float]  # MB
    cpu_usage: List[float]  # percentage
    start_time: float
    end_time: float
    
    @property
    def duration(self) -> float:
        return self.end_time - self.start_time
    
    @property
    def avg_response_time(self) -> float:
        return statistics.mean(self.response_times) if self.response_times else 0
    
    @property
    def p95_response_time(self) -> float:
        if not self.response_times:
            return 0
        sorted_times = sorted(self.response_times)
        index = int(0.95 * len(sorted_times))
        return sorted_times[index]
    
    @property
    def success_rate(self) -> float:
        total = self.success_count + self.error_count
        return (self.success_count / total * 100) if total > 0 else 0
    
    @property
    def avg_memory_usage(self) -> float:
        return statistics.mean(self.memory_usage) if self.memory_usage else 0
    
    @property
    def peak_memory_usage(self) -> float:
        return max(self.memory_usage) if self.memory_usage else 0
    
    @property
    def avg_cpu_usage(self) -> float:
        return statistics.mean(self.cpu_usage) if self.cpu_usage else 0


class PerformanceTestClient:
    """Enhanced client for performance testing"""
    
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
    
    def upload_file(self, filename: str, content: bytes) -> Tuple[Dict, float]:
        """Upload a file and return response with timing"""
        start_time = time.time()
        files = [("files", (filename, content, "application/pdf"))]
        response = self.session.post(f"{self.base_url}/api/upload", files=files)
        end_time = time.time()
        
        response.raise_for_status()
        return response.json(), end_time - start_time
    
    def get_task_status(self, task_id: str) -> Tuple[Dict, float]:
        """Get task status with timing"""
        start_time = time.time()
        response = self.session.get(f"{self.base_url}/api/task/{task_id}/status")
        end_time = time.time()
        
        response.raise_for_status()
        return response.json(), end_time - start_time
    
    def health_check(self) -> Tuple[Dict, float]:
        """Health check with timing"""
        start_time = time.time()
        response = self.session.get(f"{self.base_url}/api/health")
        end_time = time.time()
        
        response.raise_for_status()
        return response.json(), end_time - start_time


class SystemMonitor:
    """Monitor system resources during testing"""
    
    def __init__(self):
        self.monitoring = False
        self.memory_readings = []
        self.cpu_readings = []
        self.monitor_thread = None
    
    def start_monitoring(self):
        """Start monitoring system resources"""
        self.monitoring = True
        self.memory_readings.clear()
        self.cpu_readings.clear()
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop monitoring and return readings"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
        return self.memory_readings.copy(), self.cpu_readings.copy()
    
    def _monitor_loop(self):
        """Monitor loop running in separate thread"""
        process = psutil.Process()
        
        while self.monitoring:
            try:
                # Memory usage in MB
                memory_mb = process.memory_info().rss / 1024 / 1024
                self.memory_readings.append(memory_mb)
                
                # CPU usage percentage
                cpu_percent = process.cpu_percent()
                self.cpu_readings.append(cpu_percent)
                
                time.sleep(0.5)  # Sample every 500ms
            except Exception as e:
                print(f"Monitoring error: {e}")
                break


def create_test_pdf(filename: str, size_kb: int = 50) -> bytes:
    """Create a test PDF of approximately specified size"""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    
    # Calculate content to reach approximate size
    base_content = f"Test PDF: {filename}\n"
    content_per_line = "This is test content to increase file size. " * 10
    
    # Estimate lines needed (rough calculation)
    lines_needed = max(1, (size_kb * 1024) // len(content_per_line.encode()))
    
    c.drawString(100, 750, base_content)
    
    y_position = 730
    for i in range(min(lines_needed, 30)):  # Limit to prevent huge files
        if y_position < 50:
            c.showPage()
            y_position = 750
        
        c.drawString(100, y_position, f"Line {i+1}: {content_per_line}")
        y_position -= 20
    
    c.save()
    buffer.seek(0)
    return buffer.read()


class TestConcurrentUserCapacity:
    """Test system capacity with concurrent users"""
    
    def test_concurrent_sessions(self):
        """Test multiple concurrent user sessions"""
        num_users = 10
        monitor = SystemMonitor()
        monitor.start_monitoring()
        
        def create_user_session():
            """Create a session for one user"""
            try:
                client = PerformanceTestClient()
                session_id = client.create_session()
                return {"success": True, "session_id": session_id}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        start_time = time.time()
        
        # Create concurrent sessions
        with ThreadPoolExecutor(max_workers=num_users) as executor:
            futures = [executor.submit(create_user_session) for _ in range(num_users)]
            results = [future.result() for future in as_completed(futures)]
        
        end_time = time.time()
        memory_readings, cpu_readings = monitor.stop_monitoring()
        
        # Analyze results
        successful_sessions = [r for r in results if r["success"]]
        failed_sessions = [r for r in results if not r["success"]]
        
        print(f"Session Creation Results:")
        print(f"  Successful: {len(successful_sessions)}/{num_users}")
        print(f"  Failed: {len(failed_sessions)}")
        print(f"  Duration: {end_time - start_time:.2f}s")
        print(f"  Peak Memory: {max(memory_readings):.1f}MB" if memory_readings else "N/A")
        print(f"  Avg CPU: {statistics.mean(cpu_readings):.1f}%" if cpu_readings else "N/A")
        
        # Assertions
        assert len(successful_sessions) >= num_users * 0.9, "Less than 90% session creation success"
        
        # Verify unique session IDs
        session_ids = [r["session_id"] for r in successful_sessions]
        assert len(set(session_ids)) == len(session_ids), "Duplicate session IDs detected"
    
    def test_concurrent_file_uploads(self):
        """Test concurrent file uploads from multiple users"""
        num_users = 5
        files_per_user = 2
        monitor = SystemMonitor()
        
        # Pre-create sessions
        clients = []
        for i in range(num_users):
            client = PerformanceTestClient()
            client.create_session()
            clients.append(client)
        
        def upload_files_for_user(client: PerformanceTestClient, user_id: int):
            """Upload files for one user"""
            results = []
            for file_num in range(files_per_user):
                try:
                    filename = f"user_{user_id}_file_{file_num}.pdf"
                    pdf_content = create_test_pdf(filename, size_kb=100)
                    
                    upload_result, upload_time = client.upload_file(filename, pdf_content)
                    results.append({
                        "success": True,
                        "task_id": upload_result["taskId"],
                        "upload_time": upload_time,
                        "user_id": user_id,
                        "file_num": file_num
                    })
                except Exception as e:
                    results.append({
                        "success": False,
                        "error": str(e),
                        "user_id": user_id,
                        "file_num": file_num
                    })
            return results
        
        monitor.start_monitoring()
        start_time = time.time()
        
        # Execute concurrent uploads
        with ThreadPoolExecutor(max_workers=num_users) as executor:
            futures = [
                executor.submit(upload_files_for_user, client, i)
                for i, client in enumerate(clients)
            ]
            all_results = []
            for future in as_completed(futures):
                all_results.extend(future.result())
        
        end_time = time.time()
        memory_readings, cpu_readings = monitor.stop_monitoring()
        
        # Analyze results
        successful_uploads = [r for r in all_results if r["success"]]
        failed_uploads = [r for r in all_results if not r["success"]]
        upload_times = [r["upload_time"] for r in successful_uploads]
        
        print(f"Concurrent Upload Results:")
        print(f"  Total uploads: {len(all_results)}")
        print(f"  Successful: {len(successful_uploads)}")
        print(f"  Failed: {len(failed_uploads)}")
        print(f"  Success rate: {len(successful_uploads)/len(all_results)*100:.1f}%")
        print(f"  Avg upload time: {statistics.mean(upload_times):.2f}s" if upload_times else "N/A")
        print(f"  P95 upload time: {sorted(upload_times)[int(0.95*len(upload_times))]:.2f}s" if upload_times else "N/A")
        print(f"  Peak memory: {max(memory_readings):.1f}MB" if memory_readings else "N/A")
        
        # Assertions
        assert len(successful_uploads) >= len(all_results) * 0.8, "Less than 80% upload success rate"
        if upload_times:
            assert statistics.mean(upload_times) < 10.0, "Average upload time too high"
    
    def test_concurrent_processing_load(self):
        """Test system under concurrent processing load"""
        num_concurrent_tasks = 8
        monitor = SystemMonitor()
        
        # Create clients and upload files
        clients_and_tasks = []
        for i in range(num_concurrent_tasks):
            client = PerformanceTestClient()
            client.create_session()
            
            # Upload a file
            filename = f"load_test_{i}.pdf"
            pdf_content = create_test_pdf(filename, size_kb=200)
            upload_result, _ = client.upload_file(filename, pdf_content)
            
            clients_and_tasks.append((client, upload_result["taskId"]))
        
        def monitor_task_completion(client: PerformanceTestClient, task_id: str):
            """Monitor a task until completion"""
            start_time = time.time()
            status_checks = 0
            
            while time.time() - start_time < 120:  # 2 minute timeout
                try:
                    status, check_time = client.get_task_status(task_id)
                    status_checks += 1
                    
                    if status["status"] in ["completed", "failed"]:
                        return {
                            "success": status["status"] == "completed",
                            "task_id": task_id,
                            "duration": time.time() - start_time,
                            "status_checks": status_checks,
                            "final_status": status["status"]
                        }
                    
                    time.sleep(2)  # Check every 2 seconds
                except Exception as e:
                    return {
                        "success": False,
                        "task_id": task_id,
                        "error": str(e),
                        "duration": time.time() - start_time
                    }
            
            return {
                "success": False,
                "task_id": task_id,
                "error": "timeout",
                "duration": time.time() - start_time
            }
        
        monitor.start_monitoring()
        start_time = time.time()
        
        # Monitor all tasks concurrently
        with ThreadPoolExecutor(max_workers=num_concurrent_tasks) as executor:
            futures = [
                executor.submit(monitor_task_completion, client, task_id)
                for client, task_id in clients_and_tasks
            ]
            results = [future.result() for future in as_completed(futures)]
        
        end_time = time.time()
        memory_readings, cpu_readings = monitor.stop_monitoring()
        
        # Analyze results
        successful_tasks = [r for r in results if r["success"]]
        failed_tasks = [r for r in results if not r["success"]]
        processing_times = [r["duration"] for r in successful_tasks]
        
        print(f"Concurrent Processing Results:")
        print(f"  Total tasks: {len(results)}")
        print(f"  Successful: {len(successful_tasks)}")
        print(f"  Failed: {len(failed_tasks)}")
        print(f"  Success rate: {len(successful_tasks)/len(results)*100:.1f}%")
        print(f"  Avg processing time: {statistics.mean(processing_times):.1f}s" if processing_times else "N/A")
        print(f"  Max processing time: {max(processing_times):.1f}s" if processing_times else "N/A")
        print(f"  Peak memory: {max(memory_readings):.1f}MB" if memory_readings else "N/A")
        print(f"  Avg CPU: {statistics.mean(cpu_readings):.1f}%" if cpu_readings else "N/A")
        
        # Assertions
        assert len(successful_tasks) >= len(results) * 0.7, "Less than 70% processing success rate"
        if processing_times:
            assert max(processing_times) < 180, "Processing time exceeded 3 minutes"


class TestFileProcessingPerformance:
    """Test file processing performance characteristics"""
    
    def test_single_file_processing_speed(self):
        """Test processing speed for single files of various sizes"""
        file_sizes = [50, 100, 500, 1000]  # KB
        results = []
        
        for size_kb in file_sizes:
            client = PerformanceTestClient()
            client.create_session()
            
            # Create test file
            filename = f"speed_test_{size_kb}kb.pdf"
            pdf_content = create_test_pdf(filename, size_kb=size_kb)
            
            # Upload and process
            start_time = time.time()
            upload_result, upload_time = client.upload_file(filename, pdf_content)
            task_id = upload_result["taskId"]
            
            # Wait for completion
            while time.time() - start_time < 60:
                status, _ = client.get_task_status(task_id)
                if status["status"] in ["completed", "failed"]:
                    break
                time.sleep(1)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            results.append({
                "size_kb": size_kb,
                "file_size_bytes": len(pdf_content),
                "upload_time": upload_time,
                "total_time": total_time,
                "success": status["status"] == "completed",
                "throughput_kb_per_sec": size_kb / total_time if total_time > 0 else 0
            })
            
            print(f"File size {size_kb}KB: {total_time:.2f}s total, {upload_time:.2f}s upload")
        
        # Analyze performance scaling
        successful_results = [r for r in results if r["success"]]
        assert len(successful_results) >= len(results) * 0.8, "Less than 80% processing success"
        
        # Check that processing time scales reasonably with file size
        if len(successful_results) >= 2:
            times = [r["total_time"] for r in successful_results]
            sizes = [r["size_kb"] for r in successful_results]
            
            # Larger files should not take exponentially longer
            max_time = max(times)
            min_time = min(times)
            max_size = max(sizes)
            min_size = min(sizes)
            
            time_ratio = max_time / min_time if min_time > 0 else float('inf')
            size_ratio = max_size / min_size if min_size > 0 else float('inf')
            
            print(f"Performance scaling: {time_ratio:.1f}x time for {size_ratio:.1f}x size")
            assert time_ratio <= size_ratio * 2, "Processing time scales poorly with file size"
    
    def test_batch_processing_efficiency(self):
        """Test efficiency of batch processing vs individual files"""
        num_files = 5
        file_size_kb = 100
        
        # Test individual processing
        individual_times = []
        for i in range(num_files):
            client = PerformanceTestClient()
            client.create_session()
            
            filename = f"individual_{i}.pdf"
            pdf_content = create_test_pdf(filename, size_kb=file_size_kb)
            
            start_time = time.time()
            upload_result, _ = client.upload_file(filename, pdf_content)
            task_id = upload_result["taskId"]
            
            # Wait for completion
            while time.time() - start_time < 60:
                status, _ = client.get_task_status(task_id)
                if status["status"] in ["completed", "failed"]:
                    break
                time.sleep(1)
            
            individual_times.append(time.time() - start_time)
        
        # Test batch processing
        client = PerformanceTestClient()
        client.create_session()
        
        files = []
        for i in range(num_files):
            filename = f"batch_{i}.pdf"
            pdf_content = create_test_pdf(filename, size_kb=file_size_kb)
            files.append((filename, pdf_content))
        
        start_time = time.time()
        
        # Upload all files in batch
        files_data = []
        for filename, content in files:
            files_data.append(("files", (filename, content, "application/pdf")))
        
        response = client.session.post(f"{client.base_url}/api/upload", files=files_data)
        response.raise_for_status()
        batch_result = response.json()
        task_id = batch_result["taskId"]
        
        # Wait for batch completion
        while time.time() - start_time < 120:
            status, _ = client.get_task_status(task_id)
            if status["status"] in ["completed", "failed"]:
                break
            time.sleep(1)
        
        batch_time = time.time() - start_time
        total_individual_time = sum(individual_times)
        
        print(f"Individual processing: {total_individual_time:.1f}s total")
        print(f"Batch processing: {batch_time:.1f}s total")
        print(f"Efficiency gain: {total_individual_time/batch_time:.1f}x" if batch_time > 0 else "N/A")
        
        # Batch should be more efficient than individual processing
        assert batch_time < total_individual_time * 0.8, "Batch processing not significantly more efficient"


class TestMemoryUsageAndCleanup:
    """Test memory usage patterns and cleanup behavior"""
    
    def test_memory_usage_during_processing(self):
        """Test memory usage patterns during file processing"""
        monitor = SystemMonitor()
        
        client = PerformanceTestClient()
        client.create_session()
        
        # Get baseline memory
        baseline_memory = psutil.Process().memory_info().rss / 1024 / 1024
        
        monitor.start_monitoring()
        
        # Process several files sequentially
        for i in range(5):
            filename = f"memory_test_{i}.pdf"
            pdf_content = create_test_pdf(filename, size_kb=500)
            
            upload_result, _ = client.upload_file(filename, pdf_content)
            task_id = upload_result["taskId"]
            
            # Wait for completion
            start_time = time.time()
            while time.time() - start_time < 60:
                status, _ = client.get_task_status(task_id)
                if status["status"] in ["completed", "failed"]:
                    break
                time.sleep(1)
            
            # Force garbage collection
            gc.collect()
            time.sleep(2)
        
        memory_readings, cpu_readings = monitor.stop_monitoring()
        
        final_memory = psutil.Process().memory_info().rss / 1024 / 1024
        peak_memory = max(memory_readings) if memory_readings else final_memory
        
        print(f"Memory Usage Analysis:")
        print(f"  Baseline: {baseline_memory:.1f}MB")
        print(f"  Peak: {peak_memory:.1f}MB")
        print(f"  Final: {final_memory:.1f}MB")
        print(f"  Peak increase: {peak_memory - baseline_memory:.1f}MB")
        print(f"  Final increase: {final_memory - baseline_memory:.1f}MB")
        
        # Memory should not grow unbounded
        memory_growth = final_memory - baseline_memory
        assert memory_growth < 200, f"Memory growth too high: {memory_growth:.1f}MB"
        
        # Peak memory should be reasonable
        peak_growth = peak_memory - baseline_memory
        assert peak_growth < 500, f"Peak memory usage too high: {peak_growth:.1f}MB"
    
    def test_cleanup_effectiveness(self):
        """Test that cleanup processes effectively free resources"""
        client = PerformanceTestClient()
        client.create_session()
        
        # Create several tasks
        task_ids = []
        for i in range(3):
            filename = f"cleanup_test_{i}.pdf"
            pdf_content = create_test_pdf(filename, size_kb=200)
            
            upload_result, _ = client.upload_file(filename, pdf_content)
            task_ids.append(upload_result["taskId"])
        
        # Wait for all to complete
        for task_id in task_ids:
            start_time = time.time()
            while time.time() - start_time < 60:
                status, _ = client.get_task_status(task_id)
                if status["status"] in ["completed", "failed"]:
                    break
                time.sleep(1)
        
        # Get memory before cleanup
        before_cleanup = psutil.Process().memory_info().rss / 1024 / 1024
        
        # Trigger cleanup (if there's a cleanup endpoint)
        try:
            cleanup_response = client.session.post(f"{client.base_url}/api/cleanup")
            if cleanup_response.status_code == 200:
                print("Cleanup endpoint triggered successfully")
        except:
            print("No cleanup endpoint available")
        
        # Force garbage collection
        gc.collect()
        time.sleep(5)
        
        after_cleanup = psutil.Process().memory_info().rss / 1024 / 1024
        
        print(f"Cleanup Effectiveness:")
        print(f"  Before cleanup: {before_cleanup:.1f}MB")
        print(f"  After cleanup: {after_cleanup:.1f}MB")
        print(f"  Memory freed: {before_cleanup - after_cleanup:.1f}MB")
        
        # Cleanup should free some memory or at least not increase it
        assert after_cleanup <= before_cleanup + 10, "Memory increased after cleanup"


class TestSystemBehaviorUnderLoad:
    """Test system behavior under various load conditions"""
    
    def test_sustained_load_stability(self):
        """Test system stability under sustained load"""
        duration_minutes = 2  # Reduced for testing
        requests_per_minute = 30
        
        monitor = SystemMonitor()
        monitor.start_monitoring()
        
        # Create multiple clients
        num_clients = 5
        clients = []
        for i in range(num_clients):
            client = PerformanceTestClient()
            client.create_session()
            clients.append(client)
        
        def sustained_load_worker(client: PerformanceTestClient, worker_id: int):
            """Worker function for sustained load"""
            results = []
            start_time = time.time()
            request_count = 0
            
            while time.time() - start_time < duration_minutes * 60:
                try:
                    # Alternate between health checks and file uploads
                    if request_count % 3 == 0:
                        # Health check
                        health_data, response_time = client.health_check()
                        results.append({
                            "type": "health_check",
                            "success": True,
                            "response_time": response_time,
                            "worker_id": worker_id
                        })
                    else:
                        # File upload
                        filename = f"sustained_{worker_id}_{request_count}.pdf"
                        pdf_content = create_test_pdf(filename, size_kb=50)
                        upload_result, response_time = client.upload_file(filename, pdf_content)
                        results.append({
                            "type": "upload",
                            "success": True,
                            "response_time": response_time,
                            "task_id": upload_result["taskId"],
                            "worker_id": worker_id
                        })
                    
                    request_count += 1
                    
                    # Rate limiting
                    time.sleep(60 / requests_per_minute)
                    
                except Exception as e:
                    results.append({
                        "type": "error",
                        "success": False,
                        "error": str(e),
                        "worker_id": worker_id
                    })
                    time.sleep(1)  # Brief pause on error
            
            return results
        
        # Run sustained load
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=num_clients) as executor:
            futures = [
                executor.submit(sustained_load_worker, client, i)
                for i, client in enumerate(clients)
            ]
            all_results = []
            for future in as_completed(futures):
                all_results.extend(future.result())
        
        end_time = time.time()
        memory_readings, cpu_readings = monitor.stop_monitoring()
        
        # Analyze sustained load results
        successful_requests = [r for r in all_results if r["success"]]
        failed_requests = [r for r in all_results if not r["success"]]
        response_times = [r["response_time"] for r in successful_requests if "response_time" in r]
        
        print(f"Sustained Load Results ({duration_minutes} minutes):")
        print(f"  Total requests: {len(all_results)}")
        print(f"  Successful: {len(successful_requests)}")
        print(f"  Failed: {len(failed_requests)}")
        print(f"  Success rate: {len(successful_requests)/len(all_results)*100:.1f}%")
        print(f"  Avg response time: {statistics.mean(response_times):.3f}s" if response_times else "N/A")
        print(f"  P95 response time: {sorted(response_times)[int(0.95*len(response_times))]:.3f}s" if response_times else "N/A")
        print(f"  Peak memory: {max(memory_readings):.1f}MB" if memory_readings else "N/A")
        print(f"  Avg CPU: {statistics.mean(cpu_readings):.1f}%" if cpu_readings else "N/A")
        
        # Assertions for stability
        success_rate = len(successful_requests) / len(all_results) * 100
        assert success_rate >= 95, f"Success rate too low: {success_rate:.1f}%"
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            assert avg_response_time < 5.0, f"Average response time too high: {avg_response_time:.3f}s"
    
    def test_error_recovery(self):
        """Test system recovery from error conditions"""
        client = PerformanceTestClient()
        client.create_session()
        
        # Test recovery from invalid requests
        error_scenarios = [
            ("invalid_file", b"not a pdf", "text/plain"),
            ("empty_file", b"", "application/pdf"),
            ("large_filename", b"small content", "application/pdf")
        ]
        
        recovery_results = []
        
        for scenario_name, content, content_type in error_scenarios:
            # Send invalid request
            try:
                files = [("files", (f"{scenario_name}.pdf", content, content_type))]
                response = client.session.post(f"{client.base_url}/api/upload", files=files)
                error_occurred = response.status_code >= 400
            except Exception:
                error_occurred = True
            
            # Test recovery with valid request
            try:
                valid_filename = f"recovery_after_{scenario_name}.pdf"
                valid_content = create_test_pdf(valid_filename, size_kb=50)
                upload_result, response_time = client.upload_file(valid_filename, valid_content)
                
                recovery_results.append({
                    "scenario": scenario_name,
                    "error_occurred": error_occurred,
                    "recovery_success": True,
                    "recovery_time": response_time
                })
            except Exception as e:
                recovery_results.append({
                    "scenario": scenario_name,
                    "error_occurred": error_occurred,
                    "recovery_success": False,
                    "error": str(e)
                })
        
        # Analyze recovery
        successful_recoveries = [r for r in recovery_results if r["recovery_success"]]
        
        print(f"Error Recovery Results:")
        for result in recovery_results:
            print(f"  {result['scenario']}: {'✓' if result['recovery_success'] else '✗'}")
        
        assert len(successful_recoveries) == len(recovery_results), "System did not recover from all error scenarios"


if __name__ == "__main__":
    # Run performance tests
    pytest.main([__file__, "-v", "--tb=short", "-s"])