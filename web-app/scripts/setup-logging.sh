#!/bin/bash

# Logging configuration setup for Web Invoice Processor

set -e

# Configuration
LOG_DIR="./logs"
COMPOSE_FILE="docker-compose.yml"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Create logging directories
setup_log_directories() {
    log_info "Setting up logging directories..."
    
    mkdir -p "$LOG_DIR"
    mkdir -p "$LOG_DIR/web"
    mkdir -p "$LOG_DIR/celery"
    mkdir -p "$LOG_DIR/redis"
    mkdir -p "$LOG_DIR/nginx"  # For future nginx integration
    
    # Set proper permissions
    chmod 755 "$LOG_DIR"
    chmod 755 "$LOG_DIR"/*
    
    log_info "Log directories created at: $LOG_DIR"
}

# Create logrotate configuration
setup_logrotate() {
    log_info "Setting up log rotation..."
    
    cat > "$LOG_DIR/logrotate.conf" << 'EOF'
# Web Invoice Processor Log Rotation Configuration

./logs/web/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 root root
    postrotate
        # Send SIGUSR1 to reload logs (if supported)
        docker-compose -f docker-compose.yml kill -s USR1 web 2>/dev/null || true
    endscript
}

./logs/celery/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 root root
    postrotate
        docker-compose -f docker-compose.yml kill -s USR1 celery-worker 2>/dev/null || true
        docker-compose -f docker-compose.yml kill -s USR1 celery-beat 2>/dev/null || true
    endscript
}

./logs/redis/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 root root
}
EOF
    
    log_info "Logrotate configuration created"
}

# Create log monitoring script
create_log_monitor() {
    log_info "Creating log monitoring script..."
    
    cat > "$LOG_DIR/monitor-logs.sh" << 'EOF'
#!/bin/bash

# Log monitoring script for Web Invoice Processor

LOG_DIR="./logs"
ALERT_THRESHOLD=1000  # Alert if log file grows beyond this many lines per hour

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check log file sizes
check_log_sizes() {
    log_info "Checking log file sizes..."
    
    find "$LOG_DIR" -name "*.log" -type f | while read -r logfile; do
        if [ -f "$logfile" ]; then
            size=$(du -h "$logfile" | cut -f1)
            lines=$(wc -l < "$logfile" 2>/dev/null || echo "0")
            
            echo "  $(basename "$logfile"): $size ($lines lines)"
            
            # Alert if file is too large
            if [ "$lines" -gt 100000 ]; then
                log_warn "Large log file detected: $logfile ($lines lines)"
            fi
        fi
    done
}

# Check for error patterns
check_error_patterns() {
    log_info "Checking for error patterns in recent logs..."
    
    local error_count=0
    local patterns=("ERROR" "CRITICAL" "FATAL" "Exception" "Traceback")
    
    find "$LOG_DIR" -name "*.log" -type f -mtime -1 | while read -r logfile; do
        for pattern in "${patterns[@]}"; do
            local count=$(grep -c "$pattern" "$logfile" 2>/dev/null || echo "0")
            if [ "$count" -gt 0 ]; then
                log_warn "Found $count '$pattern' entries in $(basename "$logfile")"
                error_count=$((error_count + count))
            fi
        done
    done
    
    if [ "$error_count" -eq 0 ]; then
        log_info "No error patterns found in recent logs"
    fi
}

# Show recent errors
show_recent_errors() {
    local hours="${1:-1}"
    
    log_info "Recent errors (last $hours hour(s)):"
    
    find "$LOG_DIR" -name "*.log" -type f -mtime -1 | while read -r logfile; do
        local recent_errors=$(grep -E "(ERROR|CRITICAL|FATAL)" "$logfile" 2>/dev/null | tail -10)
        if [ -n "$recent_errors" ]; then
            echo ""
            echo "=== $(basename "$logfile") ==="
            echo "$recent_errors"
        fi
    done
}

# Clean old logs
clean_old_logs() {
    local days="${1:-30}"
    
    log_info "Cleaning logs older than $days days..."
    
    local deleted=0
    find "$LOG_DIR" -name "*.log*" -type f -mtime +$days | while read -r oldlog; do
        rm -f "$oldlog"
        deleted=$((deleted + 1))
        log_info "Deleted: $(basename "$oldlog")"
    done
    
    if [ "$deleted" -eq 0 ]; then
        log_info "No old logs to clean"
    fi
}

# Main function
case "${1:-check}" in
    "check")
        check_log_sizes
        check_error_patterns
        ;;
    "errors")
        show_recent_errors "$2"
        ;;
    "clean")
        clean_old_logs "$2"
        ;;
    "sizes")
        check_log_sizes
        ;;
    *)
        echo "Usage: $0 [check|errors|clean|sizes] [options]"
        echo ""
        echo "Commands:"
        echo "  check         - Check log sizes and error patterns"
        echo "  errors [hrs]  - Show recent errors (default: 1 hour)"
        echo "  clean [days]  - Clean logs older than N days (default: 30)"
        echo "  sizes         - Show log file sizes"
        ;;
esac
EOF
    
    chmod +x "$LOG_DIR/monitor-logs.sh"
    log_info "Log monitoring script created"
}

# Create centralized logging configuration
create_logging_config() {
    log_info "Creating centralized logging configuration..."
    
    cat > "$LOG_DIR/logging.json" << 'EOF'
{
    "version": 1,
    "disable_existing_loggers": false,
    "formatters": {
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        },
        "simple": {
            "format": "%(asctime)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "simple",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": "./logs/web/application.log",
            "maxBytes": 10485760,
            "backupCount": 10
        },
        "error_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "ERROR",
            "formatter": "detailed",
            "filename": "./logs/web/errors.log",
            "maxBytes": 10485760,
            "backupCount": 10
        }
    },
    "loggers": {
        "app": {
            "level": "DEBUG",
            "handlers": ["console", "file", "error_file"],
            "propagate": false
        },
        "celery": {
            "level": "INFO",
            "handlers": ["console", "file"],
            "propagate": false
        },
        "uvicorn": {
            "level": "INFO",
            "handlers": ["console", "file"],
            "propagate": false
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "file"]
    }
}
EOF
    
    log_info "Logging configuration created"
}

# Setup log aggregation script
create_log_aggregator() {
    log_info "Creating log aggregation script..."
    
    cat > "$LOG_DIR/aggregate-logs.sh" << 'EOF'
#!/bin/bash

# Log aggregation script for Web Invoice Processor

LOG_DIR="./logs"
OUTPUT_DIR="./logs/aggregated"

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Aggregate logs by date
aggregate_by_date() {
    local date="${1:-$(date +%Y-%m-%d)}"
    local output_file="$OUTPUT_DIR/all_logs_$date.log"
    
    echo "Aggregating logs for date: $date"
    
    # Clear output file
    > "$output_file"
    
    # Find all log files modified on the specified date
    find "$LOG_DIR" -name "*.log" -type f -newermt "$date 00:00:00" ! -newermt "$date 23:59:59" | while read -r logfile; do
        echo "=== $(basename "$logfile") ===" >> "$output_file"
        cat "$logfile" >> "$output_file"
        echo "" >> "$output_file"
    done
    
    echo "Aggregated logs saved to: $output_file"
}

# Aggregate error logs
aggregate_errors() {
    local hours="${1:-24}"
    local output_file="$OUTPUT_DIR/errors_last_${hours}h.log"
    
    echo "Aggregating errors from last $hours hours"
    
    # Clear output file
    > "$output_file"
    
    # Find recent log files and extract errors
    find "$LOG_DIR" -name "*.log" -type f -mtime -1 | while read -r logfile; do
        local errors=$(grep -E "(ERROR|CRITICAL|FATAL)" "$logfile" 2>/dev/null)
        if [ -n "$errors" ]; then
            echo "=== $(basename "$logfile") ===" >> "$output_file"
            echo "$errors" >> "$output_file"
            echo "" >> "$output_file"
        fi
    done
    
    echo "Error logs saved to: $output_file"
}

case "${1:-date}" in
    "date")
        aggregate_by_date "$2"
        ;;
    "errors")
        aggregate_errors "$2"
        ;;
    *)
        echo "Usage: $0 [date|errors] [options]"
        echo ""
        echo "Commands:"
        echo "  date [YYYY-MM-DD]  - Aggregate logs by date (default: today)"
        echo "  errors [hours]     - Aggregate error logs (default: 24 hours)"
        ;;
esac
EOF
    
    chmod +x "$LOG_DIR/aggregate-logs.sh"
    log_info "Log aggregation script created"
}

# Main setup function
main() {
    log_info "Setting up logging infrastructure..."
    
    setup_log_directories
    setup_logrotate
    create_log_monitor
    create_logging_config
    create_log_aggregator
    
    log_info "Logging setup completed successfully!"
    echo ""
    log_info "Available logging tools:"
    echo "  - Log monitoring: $LOG_DIR/monitor-logs.sh"
    echo "  - Log aggregation: $LOG_DIR/aggregate-logs.sh"
    echo "  - Log rotation config: $LOG_DIR/logrotate.conf"
    echo "  - Logging config: $LOG_DIR/logging.json"
    echo ""
    log_info "To set up automatic log rotation, add this to your crontab:"
    echo "  0 2 * * * /usr/sbin/logrotate $PWD/$LOG_DIR/logrotate.conf"
}

# Run main function
main "$@"