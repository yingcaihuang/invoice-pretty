#!/bin/bash

# Quick HTTPS Setup Script for Web Invoice Processor
# This script provides an interactive setup for HTTPS deployment

set -e

echo "🔒 Web Invoice Processor HTTPS Setup"
echo "===================================="
echo ""

# Check prerequisites
echo "🔍 Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    echo "   Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"

# Interactive configuration
echo ""
echo "📝 Configuration Setup"
echo "====================="

read -p "🌐 Enter your domain name (e.g., example.com): " DOMAIN
if [ -z "$DOMAIN" ]; then
    echo "❌ Domain name is required"
    exit 1
fi

read -p "📧 Enter your email for Let's Encrypt: " EMAIL
if [ -z "$EMAIL" ]; then
    echo "❌ Email is required for Let's Encrypt"
    exit 1
fi

read -p "🔐 Enter username for Traefik dashboard (default: admin): " USERNAME
USERNAME=${USERNAME:-admin}

read -s -p "🔑 Enter password for Traefik dashboard: " PASSWORD
echo
if [ -z "$PASSWORD" ]; then
    echo "❌ Password is required"
    exit 1
fi

read -p "📊 Enter Traefik dashboard subdomain (default: traefik.$DOMAIN): " TRAEFIK_DOMAIN
TRAEFIK_DOMAIN=${TRAEFIK_DOMAIN:-traefik.$DOMAIN}

# Generate authentication string
echo ""
echo "🔧 Generating configuration..."

# Check if htpasswd is available, install if needed
if ! command -v htpasswd &> /dev/null; then
    echo "📦 Installing htpasswd..."
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v apt-get &> /dev/null; then
            sudo apt-get update && sudo apt-get install -y apache2-utils
        elif command -v yum &> /dev/null; then
            sudo yum install -y httpd-tools
        elif command -v dnf &> /dev/null; then
            sudo dnf install -y httpd-tools
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        if command -v brew &> /dev/null; then
            brew install httpd
        fi
    fi
fi

AUTH_STRING=$(echo $(htpasswd -nb $USERNAME $PASSWORD) | sed -e s/\\$/\\$\\$/g)

# Create .env.https file
cat > .env.https << EOF
# HTTPS Production Environment Variables for Web Invoice Processor

# Domain Configuration
DOMAIN=$DOMAIN
TRAEFIK_DOMAIN=$TRAEFIK_DOMAIN

# ACME/Let's Encrypt Configuration
ACME_EMAIL=$EMAIL
ACME_CA_SERVER=https://acme-v02.api.letsencrypt.org/directory

# Traefik Dashboard Authentication
TRAEFIK_AUTH=$AUTH_STRING

# Application Configuration
DEBUG=false
MAX_FILE_SIZE=52428800
CLEANUP_INTERVAL=24
MAX_CONCURRENT_TASKS=4

# Logging
TRAEFIK_LOG_LEVEL=INFO
EOF

echo "✅ Configuration file created: .env.https"

# DNS Check
echo ""
echo "🔍 Checking DNS configuration..."
DOMAIN_IP=$(dig +short $DOMAIN | tail -n1)
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s ipinfo.io/ip 2>/dev/null || echo "unknown")

if [ -z "$DOMAIN_IP" ]; then
    echo "⚠️  Warning: Domain $DOMAIN does not resolve to any IP"
    echo "   Please configure your DNS to point to this server: $SERVER_IP"
elif [ "$DOMAIN_IP" != "$SERVER_IP" ]; then
    echo "⚠️  Warning: Domain $DOMAIN resolves to $DOMAIN_IP"
    echo "   Server IP appears to be: $SERVER_IP"
    echo "   Please update your DNS to point to this server"
else
    echo "✅ DNS configuration looks correct"
fi

# Final confirmation
echo ""
echo "📋 Configuration Summary:"
echo "   🌐 Domain: $DOMAIN"
echo "   📊 Traefik Dashboard: $TRAEFIK_DOMAIN"
echo "   📧 Let's Encrypt Email: $EMAIL"
echo "   👤 Dashboard User: $USERNAME"
echo ""

read -p "🚀 Deploy now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "🚀 Starting deployment..."
    ./scripts/deploy-https.sh
else
    echo ""
    echo "✅ Configuration saved to .env.https"
    echo "🚀 Run './scripts/deploy-https.sh' when ready to deploy"
    echo ""
    echo "📚 Useful commands:"
    echo "   ./scripts/deploy-https.sh     - Deploy with HTTPS"
    echo "   ./scripts/manage-certs.sh     - Manage certificates"
    echo "   docker-compose -f docker-compose.https.yml logs -f  - View logs"
fi