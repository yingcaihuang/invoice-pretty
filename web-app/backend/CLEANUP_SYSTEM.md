# File Cleanup and Expiration System

This document describes the automatic file cleanup and expiration system implemented for the Web Invoice Processor.

## Overview

The cleanup system ensures that the application doesn't accumulate unlimited storage usage by automatically removing old files and updating task statuses accordingly. It consists of several components working together to maintain system health.

## Components

### 1. Periodic Cleanup Tasks

The system uses Celery Beat scheduler to run periodic cleanup tasks:

- **cleanup-expired-tasks**: Runs every hour to clean up expired task references in Redis
- **cleanup-old-files**: Runs every 6 hours to remove files older than 24 hours
- **update-expired-task-status**: Runs 5 minutes after file cleanup to update task statuses
- **storage-usage-monitoring**: Runs every 12 hours to monitor and log storage usage

### 2. File Storage Manager

The `FileStorageManager` class provides methods for:

- `cleanup_old_files(max_age_hours)`: Remove files older than specified age
- `cleanup_task_files(session_id, task_id)`: Remove all files for a specific task
- `get_storage_usage()`: Get current storage usage statistics
- `verify_file_access()`: Check if files exist and are accessible

### 3. Task Status Updates

When files are cleaned up, the system automatically updates task statuses:

- Tasks with cleaned files are marked as `EXPIRED`
- Error message indicates files were automatically cleaned up
- Download attempts for expired tasks return appropriate error messages

## Configuration

### Environment Variables

- `CLEANUP_INTERVAL`: File cleanup interval in hours (default: 24)
- `STORAGE_PATH`: Base path for file storage (default: ./storage)
- `REDIS_URL`: Redis connection URL for task storage

### Celery Beat Schedule

The cleanup schedule is configured in `app/core/celery.py`:

```python
beat_schedule={
    'cleanup-expired-tasks': {
        'task': 'cleanup_expired_tasks',
        'schedule': 3600.0,  # Every hour
    },
    'cleanup-old-files': {
        'task': 'cleanup_old_files', 
        'schedule': 6 * 3600.0,  # Every 6 hours
        'args': (storage_path, 24),  # Clean files older than 24 hours
    },
    'update-expired-task-status': {
        'task': 'update_expired_task_status',
        'schedule': 6 * 3600.0 + 300,  # 5 minutes after file cleanup
    },
    'storage-usage-monitoring': {
        'task': 'monitor_storage_usage',
        'schedule': 12 * 3600.0,  # Every 12 hours
    }
}
```

## Manual Cleanup Operations

The system provides API endpoints for manual cleanup operations:

### Trigger File Cleanup

```bash
POST /api/cleanup/files?max_age_hours=24
```

Manually trigger file cleanup for files older than specified hours.

### Trigger Task Status Updates

```bash
POST /api/cleanup/tasks
```

Manually trigger expired task status updates.

### Get Storage Usage

```bash
GET /api/cleanup/storage/usage
```

Get current storage usage statistics in both bytes and human-readable format.

### Monitor Storage

```bash
POST /api/cleanup/storage/monitor
```

Manually trigger storage usage monitoring and logging.

### Get Cleanup Status

```bash
GET /api/cleanup/status
```

Get overall status of cleanup system and storage health.

## File Organization

The system organizes files in the following structure:

```
storage/
├── uploads/
│   └── {session_id}/
│       └── {task_id}_{filename}
├── outputs/
│   └── {session_id}/
│       └── {task_id}_{filename}
└── temp/
    └── {task_id}/
        └── temporary files
```

## Cleanup Process

1. **File Age Check**: Files are checked against the configured maximum age (default: 24 hours)
2. **File Removal**: Old files are removed from uploads, outputs, and temp directories
3. **Directory Cleanup**: Empty session directories are removed
4. **Task Status Update**: Tasks with removed files are marked as EXPIRED
5. **Logging**: All cleanup operations are logged with statistics

## Monitoring and Logging

The cleanup system provides comprehensive logging:

- **INFO**: Successful cleanup operations with statistics
- **WARNING**: High storage usage alerts (>1GB total)
- **ERROR**: Cleanup failures and retry attempts
- **DEBUG**: Detailed file operations and progress

## Docker Deployment

The cleanup system is integrated into Docker deployment:

### Services

- `celery-worker`: Processes PDF tasks and cleanup operations
- `celery-beat`: Runs periodic cleanup tasks on schedule

### Volumes

- `celery_beat_data`: Persists beat scheduler state across restarts
- `./storage`: Shared storage volume for all services

### Starting Services

```bash
# Development
docker-compose -f docker-compose.dev.yml up

# Production  
docker-compose up
```

## Error Handling

The cleanup system includes robust error handling:

- **Partial Failures**: Continue cleanup even if some files fail to delete
- **Service Unavailability**: Graceful degradation when Redis is unavailable
- **Retry Logic**: Automatic retry for transient failures
- **Error Logging**: Detailed error messages for troubleshooting

## Performance Considerations

- **Rate Limiting**: Cleanup operations are rate-limited to avoid system overload
- **Batch Processing**: Files are processed in batches to manage memory usage
- **Background Execution**: All cleanup runs in background to avoid blocking user requests
- **Monitoring**: Storage usage is monitored to detect potential issues early

## Security

- **Path Validation**: All file paths are validated to prevent directory traversal
- **Session Isolation**: Files are organized by session to prevent cross-session access
- **Safe Deletion**: Files are only deleted after verification of ownership and age

## Testing

The cleanup system includes comprehensive tests:

- **Unit Tests**: Test individual cleanup functions
- **Integration Tests**: Test end-to-end cleanup workflows
- **Performance Tests**: Verify cleanup performance under load

Run tests with:

```bash
python test_cleanup.py
```

## Troubleshooting

### Common Issues

1. **High Storage Usage**: Check cleanup schedule and file retention settings
2. **Cleanup Failures**: Check file permissions and disk space
3. **Task Status Issues**: Verify Redis connectivity and task storage health
4. **Beat Scheduler Not Running**: Ensure celery-beat service is started

### Monitoring Commands

```bash
# Check storage usage
curl http://localhost:8000/api/cleanup/storage/usage

# Check cleanup status
curl http://localhost:8000/api/cleanup/status

# Trigger manual cleanup
curl -X POST http://localhost:8000/api/cleanup/files
```