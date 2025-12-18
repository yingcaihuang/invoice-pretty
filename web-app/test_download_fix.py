#!/usr/bin/env python3
"""
Test script to verify download functionality is working correctly.
"""

import requests
import json
import os

# Configuration
API_BASE_URL = "http://localhost:8000"
TEST_SESSION_ID = "session_test_download_123456789"

def test_download_flow():
    """Test the complete download flow."""
    
    print("🧪 Testing Download Functionality")
    print("=" * 50)
    
    # Headers with session ID
    headers = {
        'X-Session-ID': TEST_SESSION_ID
    }
    
    # Step 1: Check if there are any completed tasks
    print("1. Checking for completed tasks...")
    response = requests.get(f"{API_BASE_URL}/api/task/", headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Failed to get tasks: {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    tasks = response.json().get('tasks', [])
    completed_tasks = [task for task in tasks if task.get('status') == 'completed']
    
    print(f"Found {len(completed_tasks)} completed tasks")
    
    if not completed_tasks:
        print("⚠️  No completed tasks found. Upload and process a file first.")
        return False
    
    # Step 2: Get task status with download URLs
    task = completed_tasks[0]
    task_id = task['task_id']
    
    print(f"2. Getting task status for task: {task_id}")
    response = requests.get(f"{API_BASE_URL}/api/task/{task_id}/status", headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Failed to get task status: {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    task_status = response.json()
    download_urls = task_status.get('downloadUrls', [])
    
    print(f"Found {len(download_urls)} download URLs:")
    for i, url in enumerate(download_urls):
        print(f"  {i+1}. {url}")
    
    if not download_urls:
        print("❌ No download URLs found")
        return False
    
    # Step 3: Test download
    download_url = download_urls[0]
    print(f"3. Testing download: {download_url}")
    
    # Convert relative URL to absolute URL
    if download_url.startswith('/'):
        full_url = f"{API_BASE_URL}{download_url}"
    else:
        full_url = download_url
    
    print(f"Full URL: {full_url}")
    
    response = requests.get(full_url, headers=headers)
    
    if response.status_code == 200:
        print(f"✅ Download successful! File size: {len(response.content)} bytes")
        print(f"Content-Type: {response.headers.get('content-type')}")
        return True
    else:
        print(f"❌ Download failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False

if __name__ == "__main__":
    success = test_download_flow()
    if success:
        print("\n🎉 Download functionality is working correctly!")
    else:
        print("\n💥 Download functionality has issues that need to be fixed.")