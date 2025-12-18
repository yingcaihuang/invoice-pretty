#!/bin/bash

# Production startup script for web application

set -e

echo "Starting Web Invoice Processor..."

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

# Set proper permissions
chmod 755 "${STORAGE_PATH:-/app/storage}"
chmod 755 "${STORAGE_PATH:-/app/storage}/uploads"
chmod 755 "${STORAGE_PATH:-/app/storage}/outputs"
chmod 755 "${STORAGE_PATH:-/app/storage}/temp"

echo "Storage directories created and configured"

# Start the FastAPI application
echo "Starting FastAPI server on port ${PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --workers 1