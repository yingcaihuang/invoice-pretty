#!/bin/bash

# Production deployment script for Web Invoice Processor

set -e

echo "=== Web Invoice Processor Production Deployment ==="

# Configuration
COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env"
BACKUP_DIR="./backups"
LOG_DIR="./logs"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if Docker is installed and running
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        exit 1
    fi
    
    # Check if Docker Compose is available
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not available"
        exit 1
    fi
    
    # Use docker compose if available, otherwise docker-compose
    if docker compose version &> /dev/null; then
        DOCKER_COMPOSE="docker compose"
    else
        DOCKER_COMPOSE="docker-compose"
    fi
    
    log_info "Prerequisites check passed"
}

# Create necessary directories
create_directories() {
    log_info "Creating necessary directories..."
    
    mkdir -p "$BACKUP_DIR"
    mkdir -p "$LOG_DIR"
    mkdir -p "./storage/uploads"
    mkdir -p "./storage/outputs"
    mkdir -p "./storage/temp"
    
    log_info "Directories created"
}

# Validate environment configuration
validate_config() {
    log_info "Validating configuration..."
    
    if [ ! -f "$ENV_FILE" ]; then
        log_warn "Environment file $ENV_FILE not found, using defaults"
        cp .env.example "$ENV_FILE"
    fi
    
    # Source environment file
    set -a
    source "$ENV_FILE"
    set +a
    
    # Validate required variables
    required_vars=("REDIS_URL" "STORAGE_PATH")
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            log_error "Required environment variable $var is not set"
            exit 1
        fi
    done
    
    log_info "Configuration validation passed"
}

# Backup existing data
backup_data() {
    log_info "Creating backup..."
    
    timestamp=$(date +"%Y%m%d_%H%M%S")
    backup_file="$BACKUP_DIR/backup_$timestamp.tar.gz"
    
    if [ -d "./storage" ]; then
        tar -czf "$backup_file" ./storage
        log_info "Backup created: $backup_file"
    else
        log_warn "No existing storage directory to backup"
    fi
}

# Pull latest images
pull_images() {
    log_info "Pulling latest Docker images..."
    
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" pull
    
    log_info "Images pulled successfully"
}

# Build application images
build_images() {
    log_info "Building application images..."
    
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" build --no-cache
    
    log_info "Images built successfully"
}

# Deploy services
deploy_services() {
    log_info "Deploying services..."
    
    # Stop existing services gracefully
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" down --timeout 30
    
    # Start services
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" up -d
    
    log_info "Services deployed"
}

# Wait for services to be healthy
wait_for_health() {
    log_info "Waiting for services to be healthy..."
    
    max_attempts=30
    attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if $DOCKER_COMPOSE -f "$COMPOSE_FILE" ps | grep -q "healthy"; then
            log_info "Services are healthy"
            return 0
        fi
        
        attempt=$((attempt + 1))
        log_info "Waiting for services... ($attempt/$max_attempts)"
        sleep 10
    done
    
    log_error "Services failed to become healthy within timeout"
    return 1
}

# Run post-deployment tests
run_tests() {
    log_info "Running post-deployment tests..."
    
    # Test API health endpoint
    if command -v curl &> /dev/null; then
        port=${PORT:-8000}
        if curl -f "http://localhost:$port/health" &> /dev/null; then
            log_info "Health check passed"
        else
            log_error "Health check failed"
            return 1
        fi
    else
        log_warn "curl not available, skipping health check"
    fi
    
    # Test Redis connectivity
    if $DOCKER_COMPOSE -f "$COMPOSE_FILE" exec -T redis redis-cli ping | grep -q "PONG"; then
        log_info "Redis connectivity test passed"
    else
        log_error "Redis connectivity test failed"
        return 1
    fi
    
    log_info "Post-deployment tests passed"
}

# Show deployment status
show_status() {
    log_info "Deployment status:"
    
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" ps
    
    echo ""
    log_info "Service logs (last 10 lines):"
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" logs --tail=10
    
    echo ""
    log_info "Application should be available at:"
    port=${PORT:-8000}
    echo "  - Web Interface: http://localhost:$port"
    echo "  - Health Check: http://localhost:$port/health"
    echo "  - API Documentation: http://localhost:$port/docs"
}

# Cleanup on failure
cleanup_on_failure() {
    log_error "Deployment failed, cleaning up..."
    
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" down
    
    # Restore from backup if available
    latest_backup=$(ls -t "$BACKUP_DIR"/backup_*.tar.gz 2>/dev/null | head -1)
    if [ -n "$latest_backup" ]; then
        log_info "Restoring from backup: $latest_backup"
        rm -rf ./storage
        tar -xzf "$latest_backup"
    fi
}

# Main deployment function
main() {
    log_info "Starting production deployment..."
    
    # Set trap for cleanup on failure
    trap cleanup_on_failure ERR
    
    check_prerequisites
    create_directories
    validate_config
    backup_data
    pull_images
    build_images
    deploy_services
    
    if wait_for_health; then
        run_tests
        show_status
        log_info "Deployment completed successfully!"
    else
        log_error "Deployment failed - services are not healthy"
        exit 1
    fi
}

# Parse command line arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "status")
        $DOCKER_COMPOSE -f "$COMPOSE_FILE" ps
        ;;
    "logs")
        $DOCKER_COMPOSE -f "$COMPOSE_FILE" logs -f
        ;;
    "stop")
        log_info "Stopping services..."
        $DOCKER_COMPOSE -f "$COMPOSE_FILE" down
        ;;
    "restart")
        log_info "Restarting services..."
        $DOCKER_COMPOSE -f "$COMPOSE_FILE" restart
        ;;
    "backup")
        backup_data
        ;;
    "help")
        echo "Usage: $0 [deploy|status|logs|stop|restart|backup|help]"
        echo ""
        echo "Commands:"
        echo "  deploy   - Deploy the application (default)"
        echo "  status   - Show service status"
        echo "  logs     - Show service logs"
        echo "  stop     - Stop all services"
        echo "  restart  - Restart all services"
        echo "  backup   - Create backup of storage data"
        echo "  help     - Show this help message"
        ;;
    *)
        log_error "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac