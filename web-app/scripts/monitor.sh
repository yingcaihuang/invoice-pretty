#!/bin/bash

# Monitoring script for Web Invoice Processor

set -e

# Configuration
COMPOSE_FILE="docker-compose.yml"
LOG_DIR="./logs"
ALERT_EMAIL=""  # Set this to receive email alerts

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

log_debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

# Check if Docker Compose is available
check_docker_compose() {
    if docker compose version &> /dev/null; then
        DOCKER_COMPOSE="docker compose"
    elif command -v docker-compose &> /dev/null; then
        DOCKER_COMPOSE="docker-compose"
    else
        log_error "Docker Compose is not available"
        exit 1
    fi
}

# Get service status
get_service_status() {
    local service="$1"
    local status=$($DOCKER_COMPOSE -f "$COMPOSE_FILE" ps -q "$service" 2>/dev/null)
    
    if [ -n "$status" ]; then
        local health=$($DOCKER_COMPOSE -f "$COMPOSE_FILE" ps "$service" 2>/dev/null | grep "$service" | awk '{print $4}')
        echo "$health"
    else
        echo "not_running"
    fi
}

# Check service health
check_service_health() {
    local service="$1"
    local status=$(get_service_status "$service")
    
    case "$status" in
        "Up (healthy)")
            echo "healthy"
            return 0
            ;;
        "Up")
            echo "running"
            return 0
            ;;
        "Up (unhealthy)")
            echo "unhealthy"
            return 1
            ;;
        "Exit"*)
            echo "exited"
            return 1
            ;;
        "not_running")
            echo "not_running"
            return 1
            ;;
        *)
            echo "unknown"
            return 1
            ;;
    esac
}

# Check API health
check_api_health() {
    local port="${PORT:-8000}"
    local url="http://localhost:$port/health"
    
    if command -v curl &> /dev/null; then
        local response=$(curl -s -w "%{http_code}" -o /tmp/health_response "$url" 2>/dev/null || echo "000")
        
        if [ "$response" = "200" ]; then
            local status=$(cat /tmp/health_response 2>/dev/null | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
            echo "$status"
            rm -f /tmp/health_response
            return 0
        else
            rm -f /tmp/health_response
            echo "unreachable"
            return 1
        fi
    else
        echo "curl_unavailable"
        return 1
    fi
}

# Check Redis connectivity
check_redis_health() {
    if $DOCKER_COMPOSE -f "$COMPOSE_FILE" exec -T redis redis-cli ping 2>/dev/null | grep -q "PONG"; then
        echo "healthy"
        return 0
    else
        echo "unhealthy"
        return 1
    fi
}

# Get resource usage
get_resource_usage() {
    local service="$1"
    local container_id=$($DOCKER_COMPOSE -f "$COMPOSE_FILE" ps -q "$service" 2>/dev/null)
    
    if [ -n "$container_id" ]; then
        docker stats --no-stream --format "table {{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}" "$container_id" 2>/dev/null | tail -n 1
    else
        echo "N/A\tN/A\tN/A\tN/A"
    fi
}

# Show system status
show_status() {
    log_info "=== Web Invoice Processor System Status ==="
    echo ""
    
    # Service status
    echo "Service Status:"
    printf "%-15s %-15s %-15s %-30s\n" "SERVICE" "STATUS" "HEALTH" "RESOURCE_USAGE"
    printf "%-15s %-15s %-15s %-30s\n" "-------" "------" "------" "--------------"
    
    services=("web" "redis" "celery-worker" "celery-beat")
    
    for service in "${services[@]}"; do
        local status=$(get_service_status "$service")
        local health=$(check_service_health "$service" && echo "OK" || echo "FAIL")
        local resources=$(get_resource_usage "$service")
        
        printf "%-15s %-15s %-15s %-30s\n" "$service" "$status" "$health" "$resources"
    done
    
    echo ""
    
    # API Health
    echo "API Health:"
    local api_health=$(check_api_health)
    printf "%-15s %-15s\n" "API" "$api_health"
    
    # Redis Health
    local redis_health=$(check_redis_health)
    printf "%-15s %-15s\n" "Redis" "$redis_health"
    
    echo ""
    
    # Storage usage
    if [ -d "./storage" ]; then
        echo "Storage Usage:"
        du -sh ./storage/* 2>/dev/null | while read size path; do
            printf "%-15s %-15s\n" "$(basename "$path")" "$size"
        done
        echo ""
    fi
    
    # Recent logs
    echo "Recent Activity (last 5 log entries):"
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" logs --tail=5 2>/dev/null | tail -10
}

# Monitor continuously
monitor_continuous() {
    local interval="${1:-30}"
    
    log_info "Starting continuous monitoring (interval: ${interval}s)"
    log_info "Press Ctrl+C to stop"
    
    while true; do
        clear
        show_status
        
        # Check for issues
        local issues=0
        
        services=("web" "redis" "celery-worker" "celery-beat")
        for service in "${services[@]}"; do
            if ! check_service_health "$service" >/dev/null; then
                issues=$((issues + 1))
            fi
        done
        
        if [ $issues -gt 0 ]; then
            log_warn "Found $issues service issue(s)"
        fi
        
        echo ""
        echo "Next update in ${interval}s... (Ctrl+C to stop)"
        sleep "$interval"
    done
}

# Check for alerts
check_alerts() {
    local issues=()
    
    # Check service health
    services=("web" "redis" "celery-worker" "celery-beat")
    for service in "${services[@]}"; do
        if ! check_service_health "$service" >/dev/null; then
            issues+=("Service $service is not healthy")
        fi
    done
    
    # Check API health
    if ! check_api_health >/dev/null; then
        issues+=("API health check failed")
    fi
    
    # Check Redis health
    if ! check_redis_health >/dev/null; then
        issues+=("Redis connectivity failed")
    fi
    
    # Check disk space
    local storage_usage=$(df ./storage 2>/dev/null | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ -n "$storage_usage" ] && [ "$storage_usage" -gt 90 ]; then
        issues+=("Storage usage is high: ${storage_usage}%")
    fi
    
    # Report issues
    if [ ${#issues[@]} -gt 0 ]; then
        log_error "Found ${#issues[@]} issue(s):"
        for issue in "${issues[@]}"; do
            log_error "  - $issue"
        done
        
        # Send email alert if configured
        if [ -n "$ALERT_EMAIL" ] && command -v mail &> /dev/null; then
            {
                echo "Web Invoice Processor Alert"
                echo "Timestamp: $(date)"
                echo ""
                echo "Issues found:"
                for issue in "${issues[@]}"; do
                    echo "  - $issue"
                done
            } | mail -s "Web Invoice Processor Alert" "$ALERT_EMAIL"
        fi
        
        return 1
    else
        log_info "All systems healthy"
        return 0
    fi
}

# Show logs
show_logs() {
    local service="${1:-}"
    local lines="${2:-50}"
    
    if [ -n "$service" ]; then
        log_info "Showing logs for service: $service"
        $DOCKER_COMPOSE -f "$COMPOSE_FILE" logs --tail="$lines" -f "$service"
    else
        log_info "Showing logs for all services"
        $DOCKER_COMPOSE -f "$COMPOSE_FILE" logs --tail="$lines" -f
    fi
}

# Restart unhealthy services
restart_unhealthy() {
    log_info "Checking for unhealthy services..."
    
    local restarted=0
    services=("web" "redis" "celery-worker" "celery-beat")
    
    for service in "${services[@]}"; do
        if ! check_service_health "$service" >/dev/null; then
            log_warn "Restarting unhealthy service: $service"
            $DOCKER_COMPOSE -f "$COMPOSE_FILE" restart "$service"
            restarted=$((restarted + 1))
            sleep 5  # Wait a bit between restarts
        fi
    done
    
    if [ $restarted -eq 0 ]; then
        log_info "No unhealthy services found"
    else
        log_info "Restarted $restarted service(s)"
    fi
}

# Show help
show_help() {
    echo "Web Invoice Processor Monitoring Script"
    echo ""
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  status              - Show current system status"
    echo "  monitor [interval]  - Monitor continuously (default: 30s)"
    echo "  alerts              - Check for alerts and issues"
    echo "  logs [service] [lines] - Show logs (default: all services, 50 lines)"
    echo "  restart-unhealthy   - Restart any unhealthy services"
    echo "  help                - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 status                    # Show current status"
    echo "  $0 monitor 60                # Monitor with 60s interval"
    echo "  $0 logs web 100              # Show 100 lines of web service logs"
    echo "  $0 alerts                    # Check for issues"
}

# Main function
main() {
    check_docker_compose
    
    case "${1:-status}" in
        "status")
            show_status
            ;;
        "monitor")
            monitor_continuous "$2"
            ;;
        "alerts")
            check_alerts
            ;;
        "logs")
            show_logs "$2" "$3"
            ;;
        "restart-unhealthy")
            restart_unhealthy
            ;;
        "help"|"--help"|"-h")
            show_help
            ;;
        *)
            log_error "Unknown command: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Handle Ctrl+C gracefully
trap 'echo -e "\n${YELLOW}Monitoring stopped${NC}"; exit 0' INT

# Run main function
main "$@"