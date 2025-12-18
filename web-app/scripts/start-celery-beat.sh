#!/bin/bash

# Celery beat scheduler startup script

set -e

echo "Starting Celery Beat Scheduler..."

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

# Start Celery beat scheduler
echo "Starting Celery beat scheduler..."
exec celery -A app.core.celery beat \
    --loglevel=info \
    --schedule=/app/celerybeat-schedule \
    --pidfile=/tmp/celerybeat.pid