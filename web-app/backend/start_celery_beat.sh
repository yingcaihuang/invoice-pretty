#!/bin/bash

# Start Celery beat scheduler for Web Invoice Processor
# This script starts the Celery beat scheduler to run periodic cleanup tasks

echo "Starting Celery beat scheduler for Web Invoice Processor..."

# Set environment variables if not already set
export REDIS_URL=${REDIS_URL:-"redis://localhost:6379"}
export STORAGE_PATH=${STORAGE_PATH:-"./storage"}

# Create storage directories if they don't exist
mkdir -p "$STORAGE_PATH/uploads"
mkdir -p "$STORAGE_PATH/outputs" 
mkdir -p "$STORAGE_PATH/temp"

echo "Storage directories created at: $STORAGE_PATH"
echo "Redis URL: $REDIS_URL"

# Create beat data directory if it doesn't exist
mkdir -p /app/beat_data

# Remove existing beat schedule files to start fresh
rm -f /app/beat_data/celerybeat-schedule*
rm -f /app/beat_data/celerybeat.pid

echo "Starting Celery beat scheduler..."

# Start Celery beat scheduler with explicit schedule file path in beat_data directory
celery -A app.core.celery:celery_app beat \
    --loglevel=info \
    --schedule=/app/beat_data/celerybeat-schedule.db \
    --pidfile=/app/beat_data/celerybeat.pid

echo "Celery beat scheduler stopped."