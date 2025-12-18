#!/bin/bash

# Start Celery worker for Web Invoice Processor
# This script starts a Celery worker to process PDF tasks asynchronously

echo "Starting Celery worker for Web Invoice Processor..."

# Set environment variables if not already set
export REDIS_URL=${REDIS_URL:-"redis://localhost:6379"}
export STORAGE_PATH=${STORAGE_PATH:-"./storage"}

# Create storage directories if they don't exist
mkdir -p "$STORAGE_PATH/uploads"
mkdir -p "$STORAGE_PATH/outputs" 
mkdir -p "$STORAGE_PATH/temp"

echo "Storage directories created at: $STORAGE_PATH"
echo "Redis URL: $REDIS_URL"

# Start Celery worker with appropriate settings
celery -A app.core.celery:celery_app worker \
    --loglevel=info \
    --concurrency=2 \
    --max-tasks-per-child=100 \
    --prefetch-multiplier=1 \
    --without-gossip \
    --without-mingle \
    --without-heartbeat

echo "Celery worker stopped."