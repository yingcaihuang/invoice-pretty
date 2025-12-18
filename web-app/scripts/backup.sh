#!/bin/bash

# Backup and restore script for Web Invoice Processor

set -e

# Configuration
BACKUP_DIR="./backups"
STORAGE_DIR="./storage"
COMPOSE_FILE="docker-compose.yml"

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

# Create backup
create_backup() {
    local backup_name="${1:-$(date +"%Y%m%d_%H%M%S")}"
    local backup_file="$BACKUP_DIR/backup_$backup_name.tar.gz"
    
    log_info "Creating backup: $backup_name"
    
    # Create backup directory if it doesn't exist
    mkdir -p "$BACKUP_DIR"
    
    # Check if storage directory exists
    if [ ! -d "$STORAGE_DIR" ]; then
        log_warn "Storage directory $STORAGE_DIR does not exist"
        return 1
    fi
    
    # Create backup with metadata
    {
        echo "# Web Invoice Processor Backup"
        echo "# Created: $(date)"
        echo "# Hostname: $(hostname)"
        echo "# Storage path: $STORAGE_DIR"
        echo ""
    } > "$BACKUP_DIR/backup_$backup_name.info"
    
    # Create compressed backup
    tar -czf "$backup_file" \
        -C "$(dirname "$STORAGE_DIR")" \
        "$(basename "$STORAGE_DIR")" \
        --exclude="*.tmp" \
        --exclude="*.lock"
    
    # Add metadata to backup
    tar -rf "$backup_file" -C "$BACKUP_DIR" "backup_$backup_name.info"
    gzip "$backup_file"
    mv "$backup_file.gz" "$backup_file"
    
    # Clean up temporary info file
    rm -f "$BACKUP_DIR/backup_$backup_name.info"
    
    local backup_size=$(du -h "$backup_file" | cut -f1)
    log_info "Backup created successfully: $backup_file ($backup_size)"
    
    return 0
}

# List available backups
list_backups() {
    log_info "Available backups:"
    
    if [ ! -d "$BACKUP_DIR" ] || [ -z "$(ls -A "$BACKUP_DIR"/backup_*.tar.gz 2>/dev/null)" ]; then
        log_warn "No backups found in $BACKUP_DIR"
        return 1
    fi
    
    echo ""
    printf "%-20s %-10s %-20s\n" "BACKUP NAME" "SIZE" "DATE"
    printf "%-20s %-10s %-20s\n" "----------" "----" "----"
    
    for backup in "$BACKUP_DIR"/backup_*.tar.gz; do
        if [ -f "$backup" ]; then
            backup_name=$(basename "$backup" .tar.gz | sed 's/backup_//')
            backup_size=$(du -h "$backup" | cut -f1)
            backup_date=$(date -r "$backup" "+%Y-%m-%d %H:%M:%S" 2>/dev/null || stat -c %y "$backup" | cut -d' ' -f1-2)
            printf "%-20s %-10s %-20s\n" "$backup_name" "$backup_size" "$backup_date"
        fi
    done
    
    echo ""
}

# Restore from backup
restore_backup() {
    local backup_name="$1"
    
    if [ -z "$backup_name" ]; then
        log_error "Backup name is required"
        echo "Usage: $0 restore <backup_name>"
        list_backups
        return 1
    fi
    
    local backup_file="$BACKUP_DIR/backup_$backup_name.tar.gz"
    
    if [ ! -f "$backup_file" ]; then
        log_error "Backup file not found: $backup_file"
        list_backups
        return 1
    fi
    
    log_info "Restoring from backup: $backup_name"
    
    # Stop services if running
    if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
        log_info "Stopping services..."
        if docker compose version &> /dev/null; then
            docker compose -f "$COMPOSE_FILE" down 2>/dev/null || true
        else
            docker-compose -f "$COMPOSE_FILE" down 2>/dev/null || true
        fi
    fi
    
    # Backup current storage if it exists
    if [ -d "$STORAGE_DIR" ]; then
        local current_backup="current_$(date +"%Y%m%d_%H%M%S")"
        log_info "Backing up current storage as: $current_backup"
        create_backup "$current_backup"
        
        # Remove current storage
        rm -rf "$STORAGE_DIR"
    fi
    
    # Extract backup
    log_info "Extracting backup..."
    tar -xzf "$backup_file" -C "$(dirname "$STORAGE_DIR")"
    
    # Set proper permissions
    chmod -R 755 "$STORAGE_DIR"
    
    log_info "Restore completed successfully"
    
    # Restart services if compose file exists
    if [ -f "$COMPOSE_FILE" ]; then
        log_info "Restarting services..."
        if docker compose version &> /dev/null; then
            docker compose -f "$COMPOSE_FILE" up -d
        else
            docker-compose -f "$COMPOSE_FILE" up -d
        fi
    fi
}

# Clean old backups
clean_backups() {
    local keep_days="${1:-7}"
    
    log_info "Cleaning backups older than $keep_days days..."
    
    if [ ! -d "$BACKUP_DIR" ]; then
        log_warn "Backup directory $BACKUP_DIR does not exist"
        return 0
    fi
    
    local deleted_count=0
    
    # Find and delete old backups
    while IFS= read -r -d '' backup; do
        if [ -f "$backup" ]; then
            rm -f "$backup"
            deleted_count=$((deleted_count + 1))
            log_info "Deleted old backup: $(basename "$backup")"
        fi
    done < <(find "$BACKUP_DIR" -name "backup_*.tar.gz" -type f -mtime +$keep_days -print0 2>/dev/null)
    
    if [ $deleted_count -eq 0 ]; then
        log_info "No old backups to clean"
    else
        log_info "Cleaned $deleted_count old backup(s)"
    fi
}

# Verify backup integrity
verify_backup() {
    local backup_name="$1"
    
    if [ -z "$backup_name" ]; then
        log_error "Backup name is required"
        echo "Usage: $0 verify <backup_name>"
        list_backups
        return 1
    fi
    
    local backup_file="$BACKUP_DIR/backup_$backup_name.tar.gz"
    
    if [ ! -f "$backup_file" ]; then
        log_error "Backup file not found: $backup_file"
        return 1
    fi
    
    log_info "Verifying backup: $backup_name"
    
    # Test archive integrity
    if tar -tzf "$backup_file" >/dev/null 2>&1; then
        log_info "Backup archive integrity: OK"
    else
        log_error "Backup archive is corrupted"
        return 1
    fi
    
    # List contents
    log_info "Backup contents:"
    tar -tzf "$backup_file" | head -20
    
    local total_files=$(tar -tzf "$backup_file" | wc -l)
    log_info "Total files in backup: $total_files"
    
    log_info "Backup verification completed successfully"
}

# Show help
show_help() {
    echo "Web Invoice Processor Backup Management"
    echo ""
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  backup [name]     - Create a backup (optional custom name)"
    echo "  list              - List available backups"
    echo "  restore <name>    - Restore from backup"
    echo "  clean [days]      - Clean backups older than N days (default: 7)"
    echo "  verify <name>     - Verify backup integrity"
    echo "  help              - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 backup                    # Create backup with timestamp"
    echo "  $0 backup pre_upgrade        # Create backup with custom name"
    echo "  $0 restore 20231201_143022   # Restore from specific backup"
    echo "  $0 clean 30                  # Clean backups older than 30 days"
}

# Main function
main() {
    case "${1:-help}" in
        "backup")
            create_backup "$2"
            ;;
        "list")
            list_backups
            ;;
        "restore")
            restore_backup "$2"
            ;;
        "clean")
            clean_backups "$2"
            ;;
        "verify")
            verify_backup "$2"
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

# Run main function
main "$@"