#!/bin/bash

# Certificate Management Script for Web Invoice Processor
# This script helps manage Let's Encrypt certificates

set -e

COMPOSE_FILE="docker-compose.https.yml"
ENV_FILE=".env.https"

# Load environment variables if file exists
if [ -f "$ENV_FILE" ]; then
    source $ENV_FILE
fi

show_help() {
    echo "Certificate Management for Web Invoice Processor"
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  status      Show certificate status"
    echo "  list        List all certificates"
    echo "  renew       Force certificate renewal"
    echo "  backup      Backup certificates"
    echo "  restore     Restore certificates from backup"
    echo "  logs        Show Traefik logs"
    echo "  test        Test certificate with staging server"
    echo "  help        Show this help message"
}

check_setup() {
    if [ ! -f "$COMPOSE_FILE" ]; then
        echo "❌ $COMPOSE_FILE not found"
        exit 1
    fi
    
    if [ ! -f "$ENV_FILE" ]; then
        echo "❌ $ENV_FILE not found. Run deploy-https.sh first."
        exit 1
    fi
}

show_status() {
    echo "🔒 Certificate Status for $DOMAIN"
    echo "=================================="
    
    # Check if Traefik is running
    if ! docker-compose -f $COMPOSE_FILE ps traefik | grep -q "Up"; then
        echo "❌ Traefik is not running"
        return 1
    fi
    
    # Check certificate file
    if docker-compose -f $COMPOSE_FILE exec traefik test -f /letsencrypt/acme.json; then
        echo "✅ Certificate file exists"
        
        # Show certificate details
        echo ""
        echo "📋 Certificate Details:"
        docker-compose -f $COMPOSE_FILE exec traefik cat /letsencrypt/acme.json | \
            jq -r '.letsencrypt.Certificates[]? | "Domain: \(.domain.main) | Expires: \(.certificate | @base64d | split("\n")[0])"' 2>/dev/null || \
            echo "Certificate data found but unable to parse details"
    else
        echo "❌ No certificate file found"
    fi
    
    # Test HTTPS connection
    echo ""
    echo "🌐 Testing HTTPS Connection:"
    if curl -s -I https://$DOMAIN | head -n1 | grep -q "200 OK"; then
        echo "✅ HTTPS is working"
        
        # Show certificate info
        echo ""
        echo "📜 Certificate Info:"
        echo | openssl s_client -servername $DOMAIN -connect $DOMAIN:443 2>/dev/null | \
            openssl x509 -noout -dates -subject -issuer 2>/dev/null || \
            echo "Unable to retrieve certificate details"
    else
        echo "❌ HTTPS connection failed"
    fi
}

list_certificates() {
    echo "📋 All Certificates"
    echo "==================="
    
    if docker-compose -f $COMPOSE_FILE exec traefik test -f /letsencrypt/acme.json; then
        docker-compose -f $COMPOSE_FILE exec traefik cat /letsencrypt/acme.json | \
            jq -r '.letsencrypt.Certificates[]? | "Domain: \(.domain.main)\nSAN: \(.domain.sans // [])\nExpires: \(.certificate | @base64d | split("\n")[0])\n"' 2>/dev/null || \
            echo "Certificate file exists but unable to parse"
    else
        echo "❌ No certificates found"
    fi
}

force_renew() {
    echo "🔄 Forcing Certificate Renewal"
    echo "=============================="
    
    echo "⚠️  This will restart Traefik and may cause brief downtime"
    read -p "Continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
    
    # Remove existing certificates
    echo "🗑️  Removing existing certificates..."
    docker-compose -f $COMPOSE_FILE exec traefik rm -f /letsencrypt/acme.json
    
    # Restart Traefik
    echo "🔄 Restarting Traefik..."
    docker-compose -f $COMPOSE_FILE restart traefik
    
    # Wait for renewal
    echo "⏳ Waiting for certificate renewal..."
    sleep 30
    
    show_status
}

backup_certificates() {
    echo "💾 Backing up Certificates"
    echo "=========================="
    
    BACKUP_DIR="./backups/certificates"
    BACKUP_FILE="$BACKUP_DIR/acme-$(date +%Y%m%d-%H%M%S).json"
    
    mkdir -p $BACKUP_DIR
    
    if docker-compose -f $COMPOSE_FILE exec traefik test -f /letsencrypt/acme.json; then
        docker-compose -f $COMPOSE_FILE exec traefik cat /letsencrypt/acme.json > $BACKUP_FILE
        echo "✅ Certificates backed up to: $BACKUP_FILE"
    else
        echo "❌ No certificates to backup"
        exit 1
    fi
}

restore_certificates() {
    echo "📥 Restoring Certificates"
    echo "========================"
    
    BACKUP_DIR="./backups/certificates"
    
    if [ ! -d "$BACKUP_DIR" ]; then
        echo "❌ No backup directory found"
        exit 1
    fi
    
    echo "Available backups:"
    ls -la $BACKUP_DIR/*.json 2>/dev/null || {
        echo "❌ No backup files found"
        exit 1
    }
    
    echo ""
    read -p "Enter backup filename: " BACKUP_FILE
    
    if [ ! -f "$BACKUP_DIR/$BACKUP_FILE" ]; then
        echo "❌ Backup file not found"
        exit 1
    fi
    
    echo "⚠️  This will replace current certificates"
    read -p "Continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
    
    # Copy backup to container
    docker-compose -f $COMPOSE_FILE exec -T traefik sh -c 'cat > /letsencrypt/acme.json' < "$BACKUP_DIR/$BACKUP_FILE"
    docker-compose -f $COMPOSE_FILE exec traefik chmod 600 /letsencrypt/acme.json
    
    # Restart Traefik
    docker-compose -f $COMPOSE_FILE restart traefik
    
    echo "✅ Certificates restored and Traefik restarted"
}

show_logs() {
    echo "📋 Traefik Logs"
    echo "==============="
    docker-compose -f $COMPOSE_FILE logs -f traefik
}

test_staging() {
    echo "🧪 Testing with Let's Encrypt Staging"
    echo "====================================="
    
    echo "This will use Let's Encrypt staging server for testing"
    echo "Staging certificates are not trusted by browsers but help test the process"
    echo ""
    read -p "Continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
    
    # Update environment to use staging
    export ACME_CA_SERVER="https://acme-staging-v02.api.letsencrypt.org/directory"
    
    # Remove existing certificates
    docker-compose -f $COMPOSE_FILE exec traefik rm -f /letsencrypt/acme.json
    
    # Restart with staging server
    docker-compose -f $COMPOSE_FILE --env-file $ENV_FILE up -d traefik
    
    echo "⏳ Waiting for staging certificate..."
    sleep 30
    
    show_status
    
    echo ""
    echo "⚠️  Remember to switch back to production server in $ENV_FILE:"
    echo "   ACME_CA_SERVER=https://acme-v02.api.letsencrypt.org/directory"
}

# Main script
case "${1:-help}" in
    status)
        check_setup
        show_status
        ;;
    list)
        check_setup
        list_certificates
        ;;
    renew)
        check_setup
        force_renew
        ;;
    backup)
        check_setup
        backup_certificates
        ;;
    restore)
        check_setup
        restore_certificates
        ;;
    logs)
        check_setup
        show_logs
        ;;
    test)
        check_setup
        test_staging
        ;;
    help|*)
        show_help
        ;;
esac