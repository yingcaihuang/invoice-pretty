#!/bin/bash

# HTTPS Deployment Script for Web Invoice Processor
# This script helps deploy the application with automatic HTTPS certificates

set -e

echo "🚀 Web Invoice Processor HTTPS Deployment"
echo "=========================================="

# Check if Docker and Docker Compose are installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if .env.https file exists
if [ ! -f ".env.https" ]; then
    echo "⚠️  .env.https file not found. Creating from example..."
    cp .env.https.example .env.https
    echo "📝 Please edit .env.https file with your domain and email:"
    echo "   - DOMAIN=your-domain.com"
    echo "   - ACME_EMAIL=your-email@example.com"
    echo "   - TRAEFIK_AUTH=admin:\$\$2y\$\$10\$\$..."
    echo ""
    echo "💡 Use './scripts/generate-auth.sh admin password' to generate TRAEFIK_AUTH"
    echo ""
    read -p "Press Enter after editing .env.https file..."
fi

# Load environment variables
source .env.https

# Validate required variables
if [ -z "$DOMAIN" ] || [ "$DOMAIN" = "your-domain.com" ]; then
    echo "❌ Please set DOMAIN in .env.https file"
    exit 1
fi

if [ -z "$ACME_EMAIL" ] || [ "$ACME_EMAIL" = "your-email@example.com" ]; then
    echo "❌ Please set ACME_EMAIL in .env.https file"
    exit 1
fi

if [ -z "$TRAEFIK_AUTH" ] || [[ "$TRAEFIK_AUTH" == *"your-password"* ]]; then
    echo "❌ Please set TRAEFIK_AUTH in .env.https file"
    echo "💡 Use './scripts/generate-auth.sh admin password' to generate it"
    exit 1
fi

echo "✅ Configuration validated"
echo "🌐 Domain: $DOMAIN"
echo "📧 ACME Email: $ACME_EMAIL"
echo "🔒 Traefik Dashboard: https://$TRAEFIK_DOMAIN"

# Check if domain points to this server
echo ""
echo "🔍 Checking DNS configuration..."
DOMAIN_IP=$(dig +short $DOMAIN | tail -n1)
SERVER_IP=$(curl -s ifconfig.me || curl -s ipinfo.io/ip || echo "unknown")

if [ "$DOMAIN_IP" != "$SERVER_IP" ]; then
    echo "⚠️  Warning: Domain $DOMAIN resolves to $DOMAIN_IP"
    echo "   Server IP appears to be: $SERVER_IP"
    echo "   Make sure your domain points to this server for ACME to work"
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✅ DNS configuration looks correct"
fi

# Create Docker network if it doesn't exist
echo ""
echo "🔧 Setting up Docker networks..."
docker network create web 2>/dev/null || echo "Network 'web' already exists"

# Stop existing services
echo ""
echo "🛑 Stopping existing services..."
docker-compose -f docker-compose.yml down 2>/dev/null || true
docker-compose -f docker-compose.dev.yml down 2>/dev/null || true

# Build and start HTTPS services
echo ""
echo "🏗️  Building and starting HTTPS services..."
docker-compose -f docker-compose.https.yml --env-file .env.https up -d --build

# Wait for services to be ready
echo ""
echo "⏳ Waiting for services to start..."
sleep 10

# Check service status
echo ""
echo "📊 Service Status:"
docker-compose -f docker-compose.https.yml ps

# Check if Traefik is getting certificates
echo ""
echo "🔒 Checking HTTPS certificate status..."
sleep 5

if curl -s -k https://$DOMAIN/health > /dev/null; then
    echo "✅ HTTPS is working! Certificate obtained successfully."
else
    echo "⚠️  HTTPS not yet available. This is normal for first deployment."
    echo "   Let's Encrypt may take a few minutes to issue certificates."
fi

echo ""
echo "🎉 Deployment completed!"

# Run port check
echo ""
echo "🔍 Running port accessibility check..."
./scripts/check-ports.sh

echo ""
echo "📋 Access Information:"
echo "   🌐 Application: https://$DOMAIN"
echo "   📊 Traefik Dashboard: https://$TRAEFIK_DOMAIN"
echo "   🔍 API Health: https://$DOMAIN/api/health"
echo ""
echo "📝 Useful Commands:"
echo "   📊 View logs: docker-compose -f docker-compose.https.yml logs -f"
echo "   🔄 Restart: docker-compose -f docker-compose.https.yml restart"
echo "   🛑 Stop: docker-compose -f docker-compose.https.yml down"
echo "   🔒 Check certificates: docker-compose -f docker-compose.https.yml exec traefik cat /letsencrypt/acme.json"
echo ""
echo "⚠️  Note: If HTTPS is not working immediately, wait a few minutes for"
echo "   Let's Encrypt to issue certificates. Check logs if issues persist."