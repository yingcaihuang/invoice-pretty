# Web Invoice Processor Development Commands

.PHONY: help setup-backend setup-frontend setup dev-backend dev-frontend dev-docker build test clean

help:
	@echo "Available commands:"
	@echo "  setup          - Set up both backend and frontend"
	@echo "  setup-backend  - Set up Python backend environment"
	@echo "  setup-frontend - Set up Node.js frontend environment"
	@echo "  dev-backend    - Start backend development server"
	@echo "  dev-frontend   - Start frontend development server"
	@echo "  dev-docker     - Start development environment with Docker"
	@echo "  build          - Build production Docker image"
	@echo "  test           - Run tests"
	@echo "  clean          - Clean up generated files"

setup: setup-backend setup-frontend

setup-backend:
	cd backend && ./setup_venv.sh

setup-frontend:
	cd frontend && npm install

dev-backend:
	cd backend && ./start_dev.sh

dev-frontend:
	cd frontend && npm start

dev-docker:
	docker-compose -f docker-compose.dev.yml up --build

build:
	docker-compose build

test:
	cd backend && source venv/bin/activate && pytest
	cd frontend && npm test -- --run

clean:
	cd backend && rm -rf venv __pycache__ .pytest_cache
	cd frontend && rm -rf node_modules build
	docker-compose down -v
	docker system prune -f