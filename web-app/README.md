# Web Invoice Processor

A web-based PDF invoice layout processor that transforms the existing desktop application into a scalable web service.

## Project Structure

```
web-app/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── core/           # Configuration and utilities
│   │   ├── models/         # Data models
│   │   └── services/       # Business logic
│   ├── storage/            # File storage directories
│   └── requirements.txt    # Python dependencies
├── frontend/               # React frontend
│   ├── src/               # React source code
│   ├── public/            # Static assets
│   └── package.json       # Node.js dependencies
└── docker-compose.yml     # Production deployment
```

## Development Setup

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd web-app/backend
   ```

2. Set up Python virtual environment:
   ```bash
   ./setup_venv.sh
   ```

3. Activate virtual environment:
   ```bash
   source venv/bin/activate
   ```

4. Copy environment configuration:
   ```bash
   cp .env.example .env
   ```

5. Start development server:
   ```bash
   ./start_dev.sh
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd web-app/frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start development server:
   ```bash
   npm start
   ```

### Docker Development

For full development environment with hot reload:

```bash
cd web-app
docker-compose -f docker-compose.dev.yml up
```

## Production Deployment

Build and run with Docker:

```bash
cd web-app
docker-compose up --build
```

## Services

- **Frontend**: http://localhost:3000 (development)
- **Backend API**: http://localhost:8000
- **Redis**: localhost:6379

## Features

- Web-based file upload interface
- Asynchronous PDF processing with Celery
- Real-time task status tracking
- Session-based user isolation
- Automatic file cleanup
- Docker containerization
- Responsive design with Tailwind CSS

## Requirements

- Python 3.11+
- Node.js 18+
- Redis
- Docker (for containerized deployment)