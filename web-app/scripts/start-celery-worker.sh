#!/bin/bash

# Celery worker startup script

set -e

echo "Starting Celery Worker..."

# Validate environment variables
if [ -z "$REDIS_URL" ]; then
    echo "Error: REDIS_URL environment variable is required"
    exit 1
fi

# Wait for Redis to be available
echo "Waiting for Redis to be ready..."
until redis-cli -u "$REDIS_URL" ping > /dev/null 2>&1; do
    echo "Redis is unavailable - sleeping"
    sleep 1
done
echo "Redis is ready!"

# Create storage directories if they don't exist
mkdir -p "${STORAGE_PATH:-/app/storage}/uploads"
mkdir -p "${STORAGE_PATH:-/app/storage}/outputs"
mkdir -p "${STORAGE_PATH:-/app/storage}/temp"

echo "Storage directories created"

# Start Celery worker
echo "Starting Celery worker with concurrency ${MAX_CONCURRENT_TASKS:-4}..."
exec celery -A app.core.celery worker \
    --loglevel=info \
    --concurrency="${MAX_CONCURRENT_TASKS:-4}" \
    --max-tasks-per-child=1000 \
    --time-limit=3600 \
    --soft-time-limit=3300