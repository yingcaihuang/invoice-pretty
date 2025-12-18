# Quick Start Guide

This guide will help you get the Web Invoice Processor up and running quickly.

## Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher
- Redis (optional for development, required for production)
- Docker and Docker Compose (optional, for containerized deployment)

## Quick Development Setup

### Option 1: Using Make (Recommended)

```bash
# Set up both backend and frontend
make setup

# In one terminal, start the backend
make dev-backend

# In another terminal, start the frontend
make dev-frontend
```

### Option 2: Manual Setup

#### Backend

```bash
cd web-app/backend

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env

# Start development server
uvicorn app.main:app --reload
```

#### Frontend

```bash
cd web-app/frontend

# Install dependencies
npm install

# Start development server
npm start
```

### Option 3: Docker Development

```bash
cd web-app

# Start all services with hot reload
docker-compose -f docker-compose.dev.yml up
```

## Accessing the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Next Steps

1. Review the [README.md](README.md) for detailed documentation
2. Check the [requirements document](.kiro/specs/web-invoice-processor/requirements.md) for feature specifications
3. Review the [design document](.kiro/specs/web-invoice-processor/design.md) for architecture details
4. Follow the [tasks document](.kiro/specs/web-invoice-processor/tasks.md) for implementation progress

## Troubleshooting

### Backend won't start

- Ensure Python 3.11+ is installed: `python3 --version`
- Check if virtual environment is activated
- Verify all dependencies are installed: `pip list`

### Frontend won't start

- Ensure Node.js 18+ is installed: `node --version`
- Delete `node_modules` and reinstall: `rm -rf node_modules && npm install`
- Clear npm cache: `npm cache clean --force`

### Redis connection errors

- Install Redis: `brew install redis` (macOS) or `apt-get install redis` (Linux)
- Start Redis: `redis-server`
- Or use Docker: `docker run -d -p 6379:6379 redis:7-alpine`

## Development Workflow

1. Make changes to backend code in `web-app/backend/app/`
2. Make changes to frontend code in `web-app/frontend/src/`
3. Both servers will automatically reload on file changes
4. Test your changes in the browser at http://localhost:3000
5. Check API endpoints at http://localhost:8000/docs