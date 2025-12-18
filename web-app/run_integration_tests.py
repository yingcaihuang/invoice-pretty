#!/usr/bin/env python3
"""
Comprehensive integration and deployment test runner
Executes all end-to-end, performance, and security tests
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional


class TestRunner:
    """Manages execution of integration tests"""
    
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.backend_dir = base_dir / "backend"
        self.results = {}
        
    def run_test_suite(self, test_file: str, test_name: str, 
                      timeout: int = 300, verbose: bool = False) -> Dict:
        """Run a specific test suite"""
        print(f"\n{'='*60}")
        print(f"Running {test_name}")
        print(f"{'='*60}")
        
        test_path = self.backend_dir / test_file
        if not test_path.exists():
            return {
                "name": test_name,
                "status": "skipped",
                "reason": f"Test file not found: {test_file}",
                "duration": 0
            }
        
        cmd = [
            sys.executable, "-m", "pytest",
            str(test_path),
            "-v" if verbose else "-q",
            "--tb=short",
            "-x",  # Stop on first failure
            f"--timeout={timeout}",
            "--disable-warnings"
        ]
        
        start_time = time.time()
        try:
            result = subprocess.run(
                cmd,
                cwd=self.backend_dir,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                status = "passed"
                print(f"✅ {test_name} PASSED ({duration:.1f}s)")
            else:
                status = "failed"
                print(f"❌ {test_name} FAILED ({duration:.1f}s)")
                if verbose:
                    print("STDOUT:", result.stdout)
                    print("STDERR:", result.stderr)
            
            return {
                "name": test_name,
                "status": status,
                "duration": duration,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            print(f"⏰ {test_name} TIMEOUT ({duration:.1f}s)")
            return {
                "name": test_name,
                "status": "timeout",
                "duration": duration,
                "reason": f"Test exceeded {timeout}s timeout"
            }
        except Exception as e:
            duration = time.time() - start_time
            print(f"💥 {test_name} ERROR ({duration:.1f}s): {e}")
            return {
                "name": test_name,
                "status": "error",
                "duration": duration,
                "error": str(e)
            }
    
    def check_application_health(self) -> bool:
        """Check if the application is running and healthy"""
        try:
            import requests
            response = requests.get("http://localhost:8000/api/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                return health_data.get("status") in ["healthy", "degraded"]
        except Exception as e:
            print(f"Health check failed: {e}")
        return False
    
    def start_application(self) -> bool:
        """Start the application using docker-compose"""
        print("Starting application with docker-compose...")
        
        compose_file = self.base_dir / "docker-compose.yml"
        if not compose_file.exists():
            print("❌ docker-compose.yml not found")
            return False
        
        try:
            # Stop any existing containers
            subprocess.run([
                "docker-compose", "down", "-v"
            ], cwd=self.base_dir, capture_output=True)
            
            # Start services
            result = subprocess.run([
                "docker-compose", "up", "-d", "--build"
            ], cwd=self.base_dir, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                print(f"❌ Failed to start application: {result.stderr}")
                return False
            
            # Wait for application to be ready
            print("Waiting for application to be ready...")
            for attempt in range(30):  # 30 attempts, 2 seconds each = 60 seconds max
                if self.check_application_health():
                    print("✅ Application is ready")
                    return True
                time.sleep(2)
            
            print("❌ Application failed to become ready")
            return False
            
        except subprocess.TimeoutExpired:
            print("❌ Application startup timeout")
            return False
        except Exception as e:
            print(f"❌ Error starting application: {e}")
            return False
    
    def stop_application(self):
        """Stop the application"""
        print("Stopping application...")
        try:
            subprocess.run([
                "docker-compose", "down", "-v"
            ], cwd=self.base_dir, capture_output=True, timeout=60)
            print("✅ Application stopped")
        except Exception as e:
            print(f"⚠️ Error stopping application: {e}")
    
    def run_all_tests(self, start_app: bool = True, verbose: bool = False) -> Dict:
        """Run all integration tests"""
        print("🚀 Starting comprehensive integration and deployment testing")
        print(f"Base directory: {self.base_dir}")
        
        # Test suites to run
        test_suites = [
            {
                "file": "test_e2e_workflows.py",
                "name": "End-to-End Workflows",
                "timeout": 600,  # 10 minutes
                "requires_app": True
            },
            {
                "file": "../test_docker_deployment.py",
                "name": "Docker Deployment",
                "timeout": 900,  # 15 minutes
                "requires_app": False
            },
            {
                "file": "test_performance_load.py",
                "name": "Performance and Load Testing",
                "timeout": 1200,  # 20 minutes
                "requires_app": True
            },
            {
                "file": "test_security_access_control.py",
                "name": "Security and Access Control",
                "timeout": 600,  # 10 minutes
                "requires_app": True
            }
        ]
        
        app_started = False
        
        try:
            # Start application if needed
            if start_app:
                app_started = self.start_application()
                if not app_started:
                    print("❌ Failed to start application. Skipping tests that require running app.")
            
            # Run each test suite
            for suite in test_suites:
                if suite["requires_app"] and start_app and not app_started:
                    self.results[suite["name"]] = {
                        "name": suite["name"],
                        "status": "skipped",
                        "reason": "Application not running",
                        "duration": 0
                    }
                    continue
                
                result = self.run_test_suite(
                    suite["file"],
                    suite["name"],
                    suite["timeout"],
                    verbose
                )
                self.results[suite["name"]] = result
        
        finally:
            # Stop application
            if start_app and app_started:
                self.stop_application()
        
        return self.results
    
    def generate_report(self, output_file: Optional[str] = None) -> str:
        """Generate test report"""
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results.values() if r["status"] == "passed"])
        failed_tests = len([r for r in self.results.values() if r["status"] == "failed"])
        skipped_tests = len([r for r in self.results.values() if r["status"] == "skipped"])
        error_tests = len([r for r in self.results.values() if r["status"] == "error"])
        timeout_tests = len([r for r in self.results.values() if r["status"] == "timeout"])
        
        total_duration = sum(r.get("duration", 0) for r in self.results.values())
        
        report = f"""
{'='*80}
INTEGRATION AND DEPLOYMENT TEST REPORT
{'='*80}

Summary:
  Total Test Suites: {total_tests}
  Passed: {passed_tests}
  Failed: {failed_tests}
  Skipped: {skipped_tests}
  Errors: {error_tests}
  Timeouts: {timeout_tests}
  Total Duration: {total_duration:.1f}s ({total_duration/60:.1f} minutes)

Detailed Results:
"""
        
        for name, result in self.results.items():
            status_emoji = {
                "passed": "✅",
                "failed": "❌",
                "skipped": "⏭️",
                "error": "💥",
                "timeout": "⏰"
            }.get(result["status"], "❓")
            
            report += f"\n{status_emoji} {name}: {result['status'].upper()}"
            report += f" ({result.get('duration', 0):.1f}s)"
            
            if result["status"] in ["failed", "error", "timeout"]:
                if "reason" in result:
                    report += f"\n   Reason: {result['reason']}"
                if "error" in result:
                    report += f"\n   Error: {result['error']}"
        
        report += f"\n\n{'='*80}\n"
        
        # Save to file if requested
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report)
            print(f"📄 Report saved to: {output_file}")
        
        return report
    
    def save_results_json(self, output_file: str):
        """Save detailed results as JSON"""
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"📊 Detailed results saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Run integration and deployment tests")
    parser.add_argument("--no-app", action="store_true", 
                       help="Don't start/stop the application")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Verbose output")
    parser.add_argument("--report", "-r", type=str,
                       help="Save report to file")
    parser.add_argument("--json", "-j", type=str,
                       help="Save detailed results as JSON")
    parser.add_argument("--suite", "-s", type=str,
                       help="Run specific test suite only")
    
    args = parser.parse_args()
    
    # Determine base directory
    script_dir = Path(__file__).parent
    base_dir = script_dir
    
    runner = TestRunner(base_dir)
    
    if args.suite:
        # Run specific suite
        suite_map = {
            "e2e": ("test_e2e_workflows.py", "End-to-End Workflows"),
            "docker": ("../test_docker_deployment.py", "Docker Deployment"),
            "performance": ("test_performance_load.py", "Performance and Load Testing"),
            "security": ("test_security_access_control.py", "Security and Access Control")
        }
        
        if args.suite in suite_map:
            file, name = suite_map[args.suite]
            result = runner.run_test_suite(file, name, 600, args.verbose)
            runner.results[name] = result
        else:
            print(f"❌ Unknown test suite: {args.suite}")
            print(f"Available suites: {', '.join(suite_map.keys())}")
            sys.exit(1)
    else:
        # Run all tests
        runner.run_all_tests(start_app=not args.no_app, verbose=args.verbose)
    
    # Generate and display report
    report = runner.generate_report(args.report)
    print(report)
    
    # Save JSON results if requested
    if args.json:
        runner.save_results_json(args.json)
    
    # Exit with appropriate code
    failed_count = len([r for r in runner.results.values() 
                       if r["status"] in ["failed", "error", "timeout"]])
    
    if failed_count > 0:
        print(f"❌ {failed_count} test suite(s) failed")
        sys.exit(1)
    else:
        print("✅ All test suites passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()