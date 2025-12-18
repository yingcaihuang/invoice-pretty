"""
Docker deployment and scaling tests
Tests Docker container deployment, scaling, and configuration
"""
import json
import os
import subprocess
import time
import requests
from typing import Dict, List, Optional
import pytest
import docker
from pathlib import Path


class DockerTestManager:
    """Manager for Docker-based testing"""
    
    def __init__(self):
        self.client = docker.from_env()
        self.containers = []
        self.networks = []
        self.volumes = []
    
    def cleanup(self):
        """Clean up all created Docker resources"""
        # Stop and remove containers
        for container in self.containers:
            try:
                container.stop(timeout=10)
                container.remove()
            except Exception as e:
                print(f"Error cleaning up container {container.name}: {e}")
        
        # Remove networks
        for network in self.networks:
            try:
                network.remove()
            except Exception as e:
                print(f"Error cleaning up network {network.name}: {e}")
        
        # Remove volumes
        for volume in self.volumes:
            try:
                volume.remove()
            except Exception as e:
                print(f"Error cleaning up volume {volume.name}: {e}")
        
        self.containers.clear()
        self.networks.clear()
        self.volumes.clear()
    
    def build_image(self, dockerfile_path: str, tag: str) -> str:
        """Build Docker image"""
        build_path = Path(dockerfile_path).parent
        image, logs = self.client.images.build(
            path=str(build_path),
            dockerfile=dockerfile_path,
            tag=tag,
            rm=True
        )
        return image.id
    
    def run_container(self, image: str, **kwargs) -> docker.models.containers.Container:
        """Run a container and track it for cleanup"""
        container = self.client.containers.run(image, detach=True, **kwargs)
        self.containers.append(container)
        return container
    
    def create_network(self, name: str) -> docker.models.networks.Network:
        """Create a network and track it for cleanup"""
        network = self.client.networks.create(name)
        self.networks.append(network)
        return network
    
    def create_volume(self, name: str) -> docker.models.volumes.Volume:
        """Create a volume and track it for cleanup"""
        volume = self.client.volumes.create(name)
        self.volumes.append(volume)
        return volume
    
    def wait_for_health(self, container: docker.models.containers.Container, 
                       timeout: int = 60) -> bool:
        """Wait for container to become healthy"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            container.reload()
            health = container.attrs.get('State', {}).get('Health', {})
            status = health.get('Status', 'none')
            
            if status == 'healthy':
                return True
            elif status == 'unhealthy':
                return False
            
            time.sleep(2)
        
        return False
    
    def get_container_logs(self, container: docker.models.containers.Container) -> str:
        """Get container logs"""
        return container.logs().decode('utf-8')


class TestDockerDeployment:
    """Test Docker container deployment"""
    
    @pytest.fixture
    def docker_manager(self):
        """Create Docker test manager"""
        manager = DockerTestManager()
        yield manager
        manager.cleanup()
    
    def test_single_container_deployment(self, docker_manager):
        """Test single container deployment with docker-compose"""
        # Change to web-app directory
        original_dir = os.getcwd()
        web_app_dir = Path(__file__).parent / "web-app"
        os.chdir(web_app_dir)
        
        try:
            # Build and start services using docker-compose
            result = subprocess.run([
                "docker-compose", "up", "-d", "--build"
            ], capture_output=True, text=True, timeout=300)
            
            assert result.returncode == 0, f"Docker compose failed: {result.stderr}"
            
            # Wait for services to be ready
            time.sleep(30)
            
            # Test health endpoint
            max_retries = 10
            for attempt in range(max_retries):
                try:
                    response = requests.get("http://localhost:8000/api/health", timeout=10)
                    if response.status_code == 200:
                        health_data = response.json()
                        assert health_data["status"] in ["healthy", "degraded"]
                        break
                except requests.exceptions.RequestException:
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(5)
            
            # Test basic API functionality
            # Create session
            session_response = requests.post("http://localhost:8000/api/session")
            assert session_response.status_code == 200
            session_data = session_response.json()
            session_id = session_data["session_id"]
            
            # Test file upload endpoint (without actual file)
            headers = {"X-Session-ID": session_id}
            upload_response = requests.post(
                "http://localhost:8000/api/upload",
                headers=headers,
                files={"files": ("test.txt", b"test", "text/plain")}
            )
            # Should either accept or reject with proper error
            assert upload_response.status_code in [200, 400, 422]
            
        finally:
            # Cleanup
            subprocess.run(["docker-compose", "down", "-v"], capture_output=True)
            os.chdir(original_dir)
    
    def test_environment_variable_configuration(self, docker_manager):
        """Test environment variable configuration"""
        # Create custom environment variables
        env_vars = {
            "PORT": "8080",
            "MAX_FILE_SIZE": "10485760",  # 10MB
            "CLEANUP_INTERVAL": "12",
            "MAX_CONCURRENT_TASKS": "2",
            "DEBUG": "true"
        }
        
        # Create network for containers
        network = docker_manager.create_network("test-network")
        
        # Start Redis container
        redis_container = docker_manager.run_container(
            "redis:7-alpine",
            name="test-redis",
            network=network.name,
            command=["redis-server", "--appendonly", "yes"],
            healthcheck={
                "test": ["CMD", "redis-cli", "ping"],
                "interval": 10000000000,  # 10s in nanoseconds
                "timeout": 5000000000,    # 5s in nanoseconds
                "retries": 5
            }
        )
        
        # Wait for Redis to be ready
        time.sleep(10)
        
        # Build application image
        web_app_dir = Path(__file__).parent / "web-app"
        dockerfile_path = web_app_dir / "Dockerfile"
        
        if dockerfile_path.exists():
            image_id = docker_manager.build_image(str(dockerfile_path), "test-web-app")
            
            # Start web application with custom environment
            env_vars["REDIS_URL"] = "redis://test-redis:6379"
            
            web_container = docker_manager.run_container(
                "test-web-app",
                name="test-web-app",
                network=network.name,
                environment=env_vars,
                ports={"8000/tcp": 8080},
                healthcheck={
                    "test": ["CMD", "curl", "-f", "http://localhost:8000/health"],
                    "interval": 30000000000,  # 30s in nanoseconds
                    "timeout": 10000000000,   # 10s in nanoseconds
                    "retries": 3,
                    "start_period": 40000000000  # 40s in nanoseconds
                }
            )
            
            # Wait for application to be ready
            assert docker_manager.wait_for_health(web_container, timeout=120)
            
            # Test that custom port is working
            response = requests.get("http://localhost:8080/api/health", timeout=10)
            assert response.status_code == 200
            
            # Verify configuration is applied (if health endpoint returns config info)
            health_data = response.json()
            assert health_data["status"] in ["healthy", "degraded"]
    
    def test_container_scaling(self, docker_manager):
        """Test horizontal scaling with multiple containers"""
        # This test simulates load balancer scenario
        # Create network
        network = docker_manager.create_network("scaling-test-network")
        
        # Create shared Redis
        redis_container = docker_manager.run_container(
            "redis:7-alpine",
            name="scaling-redis",
            network=network.name,
            command=["redis-server", "--appendonly", "yes"]
        )
        
        time.sleep(10)  # Wait for Redis
        
        # Build application image
        web_app_dir = Path(__file__).parent / "web-app"
        dockerfile_path = web_app_dir / "Dockerfile"
        
        if dockerfile_path.exists():
            image_id = docker_manager.build_image(str(dockerfile_path), "scaling-test-app")
            
            # Start multiple application instances
            containers = []
            ports = [8001, 8002, 8003]
            
            for i, port in enumerate(ports):
                container = docker_manager.run_container(
                    "scaling-test-app",
                    name=f"scaling-app-{i+1}",
                    network=network.name,
                    environment={
                        "REDIS_URL": "redis://scaling-redis:6379",
                        "PORT": "8000"
                    },
                    ports={"8000/tcp": port}
                )
                containers.append((container, port))
            
            # Wait for all containers to be ready
            time.sleep(30)
            
            # Test that all instances are responding
            for container, port in containers:
                response = requests.get(f"http://localhost:{port}/api/health", timeout=10)
                assert response.status_code == 200
                
                health_data = response.json()
                assert health_data["status"] in ["healthy", "degraded"]
            
            # Test session sharing across instances
            # Create session on first instance
            session_response = requests.post(f"http://localhost:{ports[0]}/api/session")
            assert session_response.status_code == 200
            session_data = session_response.json()
            session_id = session_data["session_id"]
            
            # Verify session exists on other instances
            headers = {"X-Session-ID": session_id}
            for port in ports[1:]:
                # Try to access session-protected endpoint
                response = requests.get(
                    f"http://localhost:{port}/api/task/dummy-task-id/status",
                    headers=headers
                )
                # Should return 404 (task not found) rather than 401 (session invalid)
                assert response.status_code in [404, 400]  # Not 401
    
    def test_graceful_shutdown(self, docker_manager):
        """Test graceful shutdown handling"""
        # Create network and Redis
        network = docker_manager.create_network("shutdown-test-network")
        
        redis_container = docker_manager.run_container(
            "redis:7-alpine",
            name="shutdown-redis",
            network=network.name
        )
        
        time.sleep(10)
        
        # Build and start application
        web_app_dir = Path(__file__).parent / "web-app"
        dockerfile_path = web_app_dir / "Dockerfile"
        
        if dockerfile_path.exists():
            image_id = docker_manager.build_image(str(dockerfile_path), "shutdown-test-app")
            
            web_container = docker_manager.run_container(
                "shutdown-test-app",
                name="shutdown-test-web",
                network=network.name,
                environment={"REDIS_URL": "redis://shutdown-redis:6379"},
                ports={"8000/tcp": 8004}
            )
            
            # Wait for startup
            time.sleep(20)
            
            # Verify it's running
            response = requests.get("http://localhost:8004/api/health", timeout=10)
            assert response.status_code == 200
            
            # Send graceful shutdown signal
            web_container.kill(signal="SIGTERM")
            
            # Wait for graceful shutdown
            try:
                web_container.wait(timeout=30)
                exit_code = web_container.attrs['State']['ExitCode']
                # Exit code 0 indicates graceful shutdown
                assert exit_code == 0, f"Container did not shut down gracefully, exit code: {exit_code}"
            except Exception as e:
                # Get logs for debugging
                logs = docker_manager.get_container_logs(web_container)
                print(f"Container logs during shutdown:\n{logs}")
                raise
    
    def test_volume_persistence(self, docker_manager):
        """Test data persistence with volumes"""
        # Create volumes
        storage_volume = docker_manager.create_volume("test-storage")
        redis_volume = docker_manager.create_volume("test-redis-data")
        
        # Create network
        network = docker_manager.create_network("persistence-test-network")
        
        # Start Redis with persistent volume
        redis_container = docker_manager.run_container(
            "redis:7-alpine",
            name="persistence-redis",
            network=network.name,
            volumes={redis_volume.name: {"bind": "/data", "mode": "rw"}},
            command=["redis-server", "--appendonly", "yes"]
        )
        
        time.sleep(10)
        
        # Build and start application with storage volume
        web_app_dir = Path(__file__).parent / "web-app"
        dockerfile_path = web_app_dir / "Dockerfile"
        
        if dockerfile_path.exists():
            image_id = docker_manager.build_image(str(dockerfile_path), "persistence-test-app")
            
            web_container = docker_manager.run_container(
                "persistence-test-app",
                name="persistence-test-web",
                network=network.name,
                environment={"REDIS_URL": "redis://persistence-redis:6379"},
                volumes={storage_volume.name: {"bind": "/app/storage", "mode": "rw"}},
                ports={"8000/tcp": 8005}
            )
            
            # Wait for startup
            time.sleep(20)
            
            # Create a session and verify it's stored
            session_response = requests.post("http://localhost:8005/api/session")
            assert session_response.status_code == 200
            session_data = session_response.json()
            session_id = session_data["session_id"]
            
            # Stop and restart containers
            web_container.stop()
            redis_container.stop()
            
            # Start Redis again with same volume
            redis_container2 = docker_manager.run_container(
                "redis:7-alpine",
                name="persistence-redis-2",
                network=network.name,
                volumes={redis_volume.name: {"bind": "/data", "mode": "rw"}},
                command=["redis-server", "--appendonly", "yes"]
            )
            
            time.sleep(10)
            
            # Start web app again with same storage volume
            web_container2 = docker_manager.run_container(
                "persistence-test-app",
                name="persistence-test-web-2",
                network=network.name,
                environment={"REDIS_URL": "redis://persistence-redis-2:6379"},
                volumes={storage_volume.name: {"bind": "/app/storage", "mode": "rw"}},
                ports={"8000/tcp": 8006}
            )
            
            time.sleep(20)
            
            # Verify session still exists (if session persistence is implemented)
            headers = {"X-Session-ID": session_id}
            response = requests.get(
                f"http://localhost:8006/api/task/dummy-task/status",
                headers=headers
            )
            # Should return 404 (task not found) rather than 401 (session invalid)
            # This indicates session was persisted
            assert response.status_code in [404, 400]  # Not 401


class TestContainerHealthAndMonitoring:
    """Test container health checks and monitoring"""
    
    def test_health_check_endpoint(self):
        """Test health check endpoint functionality"""
        # This assumes the application is running
        try:
            response = requests.get("http://localhost:8000/api/health", timeout=10)
            assert response.status_code == 200
            
            health_data = response.json()
            assert "status" in health_data
            assert health_data["status"] in ["healthy", "degraded", "unhealthy"]
            assert "services" in health_data
            assert "timestamp" in health_data
            
            # Verify service status structure
            services = health_data["services"]
            assert "redis" in services
            assert "file_storage" in services
            
        except requests.exceptions.RequestException:
            pytest.skip("Application not running for health check test")
    
    def test_container_resource_limits(self, docker_manager):
        """Test container behavior under resource constraints"""
        # Create network
        network = docker_manager.create_network("resource-test-network")
        
        # Start Redis
        redis_container = docker_manager.run_container(
            "redis:7-alpine",
            name="resource-redis",
            network=network.name,
            mem_limit="128m"  # Limit Redis memory
        )
        
        time.sleep(10)
        
        # Build and start application with memory limit
        web_app_dir = Path(__file__).parent / "web-app"
        dockerfile_path = web_app_dir / "Dockerfile"
        
        if dockerfile_path.exists():
            image_id = docker_manager.build_image(str(dockerfile_path), "resource-test-app")
            
            web_container = docker_manager.run_container(
                "resource-test-app",
                name="resource-test-web",
                network=network.name,
                environment={"REDIS_URL": "redis://resource-redis:6379"},
                ports={"8000/tcp": 8007},
                mem_limit="256m",  # Limit application memory
                cpu_quota=50000,   # Limit CPU to 50%
                cpu_period=100000
            )
            
            # Wait for startup
            time.sleep(30)
            
            # Test that application still works under constraints
            response = requests.get("http://localhost:8007/api/health", timeout=15)
            assert response.status_code == 200
            
            health_data = response.json()
            assert health_data["status"] in ["healthy", "degraded"]
            
            # Test basic functionality
            session_response = requests.post("http://localhost:8007/api/session")
            assert session_response.status_code == 200


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v", "--tb=short"])