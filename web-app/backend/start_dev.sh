#!/bin/bash

# Start Redis server in background (if not already running)
if ! pgrep -x "redis-server" > /dev/null; then
    echo "Starting Redis server..."
    redis-server --daemonize yes
fi

# Start Celery worker in background
echo "Starting Celery worker..."
celery -A app.core.celery worker --loglevel=info &

# Start FastAPI development server with hot reload
echo "Starting FastAPI development server..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload