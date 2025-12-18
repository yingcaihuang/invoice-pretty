"""
Application configuration settings
"""
import os
import logging
from pathlib import Path
from pydantic import Field, validator
from pydantic_settings import BaseSettings
from typing import Optional


logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Server settings
    port: int = Field(default=8000, ge=1, le=65535, description="Server port")
    debug: bool = Field(default=False, description="Enable debug mode")
    
    # Redis settings
    redis_url: str = Field(default="redis://localhost:6379", description="Redis connection URL")
    
    # Storage settings
    storage_path: str = Field(default="./storage", description="Base path for file storage")
    max_file_size: int = Field(default=52428800, ge=1024, description="Maximum file size in bytes (50MB)")
    cleanup_interval: int = Field(default=24, ge=1, description="File cleanup interval in hours")
    
    # Task processing settings
    max_concurrent_tasks: int = Field(default=4, ge=1, le=32, description="Maximum concurrent processing tasks")
    
    # Health check settings
    health_check_timeout: int = Field(default=30, ge=5, le=300, description="Health check timeout in seconds")
    
    @validator('storage_path')
    def validate_storage_path(cls, v):
        """Ensure storage path is absolute and create if it doesn't exist"""
        path = Path(v).resolve()
        
        # Create storage directories if they don't exist
        try:
            path.mkdir(parents=True, exist_ok=True)
            (path / "uploads").mkdir(exist_ok=True)
            (path / "outputs").mkdir(exist_ok=True)
            (path / "temp").mkdir(exist_ok=True)
            logger.info(f"Storage directories created at: {path}")
        except Exception as e:
            logger.error(f"Failed to create storage directories: {e}")
            raise ValueError(f"Cannot create storage directories at {path}: {e}")
        
        return str(path)
    
    @validator('redis_url')
    def validate_redis_url(cls, v):
        """Validate Redis URL format"""
        if not v.startswith(('redis://', 'rediss://')):
            raise ValueError("Redis URL must start with redis:// or rediss://")
        return v
    
    @validator('max_file_size')
    def validate_max_file_size(cls, v):
        """Ensure max file size is reasonable"""
        if v > 1024 * 1024 * 1024:  # 1GB
            logger.warning(f"Large max file size configured: {v / (1024*1024):.1f}MB")
        return v
    
    def validate_configuration(self) -> bool:
        """Validate the complete configuration"""
        try:
            # Check storage path accessibility
            storage = Path(self.storage_path)
            if not storage.exists():
                logger.error(f"Storage path does not exist: {storage}")
                return False
            
            if not storage.is_dir():
                logger.error(f"Storage path is not a directory: {storage}")
                return False
            
            # Check write permissions
            test_file = storage / "test_write_permission"
            try:
                test_file.write_text("test")
                test_file.unlink()
            except Exception as e:
                logger.error(f"No write permission to storage path: {e}")
                return False
            
            logger.info("Configuration validation successful")
            return True
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

# Validate configuration on import
if not settings.validate_configuration():
    logger.error("Configuration validation failed - some features may not work correctly")