#!/usr/bin/env python3
"""
Configuration validation script for Web Invoice Processor.

This script validates the application configuration and environment
variables to ensure the application can start successfully.
"""

import os
import sys
import logging
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, '/app')

from app.core.config import settings


def validate_environment():
    """Validate environment variables and configuration."""
    print("=== Web Invoice Processor Configuration Validation ===\n")
    
    errors = []
    warnings = []
    
    # Check required environment variables
    required_vars = ['REDIS_URL', 'STORAGE_PATH']
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            errors.append(f"Missing required environment variable: {var}")
        else:
            print(f"✓ {var}: {value}")
    
    # Check optional environment variables
    optional_vars = {
        'PORT': '8000',
        'DEBUG': 'false',
        'MAX_FILE_SIZE': '52428800',
        'CLEANUP_INTERVAL': '24',
        'MAX_CONCURRENT_TASKS': '4'
    }
    
    for var, default in optional_vars.items():
        value = os.getenv(var, default)
        print(f"✓ {var}: {value} (default: {default})")
    
    # Validate configuration using Pydantic settings
    try:
        print(f"\n=== Configuration Validation ===")
        print(f"✓ Port: {settings.port}")
        print(f"✓ Debug mode: {settings.debug}")
        print(f"✓ Redis URL: {settings.redis_url}")
        print(f"✓ Storage path: {settings.storage_path}")
        print(f"✓ Max file size: {settings.max_file_size / (1024*1024):.1f}MB")
        print(f"✓ Cleanup interval: {settings.cleanup_interval} hours")
        print(f"✓ Max concurrent tasks: {settings.max_concurrent_tasks}")
        
        # Validate configuration
        if settings.validate_configuration():
            print("✓ Configuration validation passed")
        else:
            errors.append("Configuration validation failed")
            
    except Exception as e:
        errors.append(f"Configuration validation error: {e}")
    
    # Check storage directories
    try:
        storage_path = Path(settings.storage_path)
        subdirs = ['uploads', 'outputs', 'temp']
        
        print(f"\n=== Storage Directory Validation ===")
        print(f"✓ Base storage path: {storage_path}")
        
        for subdir in subdirs:
            subdir_path = storage_path / subdir
            if subdir_path.exists() and subdir_path.is_dir():
                print(f"✓ {subdir} directory: {subdir_path}")
            else:
                warnings.append(f"Storage subdirectory missing: {subdir_path}")
                
    except Exception as e:
        errors.append(f"Storage validation error: {e}")
    
    # Test Redis connection
    try:
        import redis
        print(f"\n=== Redis Connection Test ===")
        
        redis_client = redis.from_url(settings.redis_url, socket_connect_timeout=5)
        redis_client.ping()
        print(f"✓ Redis connection successful: {settings.redis_url}")
        
        # Test basic operations
        redis_client.set("test_key", "test_value", ex=10)
        value = redis_client.get("test_key")
        if value == "test_value":
            print("✓ Redis read/write operations working")
        else:
            warnings.append("Redis read/write test failed")
            
        redis_client.delete("test_key")
        
    except Exception as e:
        errors.append(f"Redis connection failed: {e}")
    
    # Print summary
    print(f"\n=== Validation Summary ===")
    
    if errors:
        print(f"❌ {len(errors)} error(s) found:")
        for error in errors:
            print(f"   - {error}")
    
    if warnings:
        print(f"⚠️  {len(warnings)} warning(s) found:")
        for warning in warnings:
            print(f"   - {warning}")
    
    if not errors and not warnings:
        print("✅ All validations passed successfully!")
        return 0
    elif not errors:
        print("✅ Configuration is valid with warnings")
        return 0
    else:
        print("❌ Configuration validation failed")
        return 1


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.WARNING)
    
    try:
        exit_code = validate_environment()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nValidation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Validation script failed: {e}")
        sys.exit(1)