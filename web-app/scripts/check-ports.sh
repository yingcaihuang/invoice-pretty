#!/bin/bash

# Port Check Script for HTTPS Deployment
# This script helps verify that required ports are accessible

set -e

echo "🔍 Port Accessibility Check"
echo "=========================="

# Load environment if available
if [ -f ".env.https" ]; then
    source .env.https
fi

# Get domain from user if not set
if [ -z "$DOMAIN" ]; then
    read -p "🌐 Enter your domain name: " DOMAIN
fi

if [ -z "$DOMAIN" ]; then
    echo "❌ Domain name is required"
    exit 1
fi

echo "🌐 Checking ports for domain: $DOMAIN"
echo ""

# Check DNS resolution
echo "📍 DNS Resolution Check:"
DOMAIN_IP=$(dig +short $DOMAIN | tail -n1)
if [ -z "$DOMAIN_IP" ]; then
    echo "❌ Domain $DOMAIN does not resolve to any IP"
    exit 1
else
    echo "✅ Domain resolves to: $DOMAIN_IP"
fi

# Get server IP
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s ipinfo.io/ip 2>/dev/null || echo "unknown")
echo "🖥️  Server IP appears to be: $SERVER_IP"

if [ "$DOMAIN_IP" != "$SERVER_IP" ]; then
    echo "⚠️  Warning: Domain IP ($DOMAIN_IP) != Server IP ($SERVER_IP)"
    echo "   Make sure your DNS points to this server"
fi

echo ""

# Check port 80 (HTTP)
echo "🔌 Port 80 (HTTP) Check:"
if curl -s -I --connect-timeout 5 http://$DOMAIN > /dev/null 2>&1; then
    HTTP_STATUS=$(curl -s -I http://$DOMAIN | head -n1)
    if echo "$HTTP_STATUS" | grep -q "301\|302"; then
        echo "✅ Port 80 accessible and redirecting to HTTPS"
    else
        echo "✅ Port 80 accessible (Status: $HTTP_STATUS)"
    fi
else
    echo "❌ Port 80 not accessible"
    echo "   Make sure port 80 is open in your firewall"
fi

# Check port 443 (HTTPS)
echo ""
echo "🔒 Port 443 (HTTPS) Check:"
if curl -s -I --connect-timeout 5 https://$DOMAIN > /dev/null 2>&1; then
    HTTPS_STATUS=$(curl -s -I https://$DOMAIN | head -n1)
    echo "✅ Port 443 accessible (Status: $HTTPS_STATUS)"
    
    # Check certificate
    echo ""
    echo "📜 SSL Certificate Check:"
    CERT_INFO=$(echo | openssl s_client -servername $DOMAIN -connect $DOMAIN:443 2>/dev/null | openssl x509 -noout -dates 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo "✅ SSL Certificate is valid"
        echo "$CERT_INFO"
    else
        echo "⚠️  SSL Certificate check failed (might be self-signed or invalid)"
    fi
else
    echo "❌ Port 443 not accessible"
    echo "   Possible causes:"
    echo "   - Port 443 blocked by firewall"
    echo "   - SSL certificate not yet issued"
    echo "   - Traefik not running"
fi

# Check if Traefik is running (if docker-compose is available)
echo ""
echo "🐳 Docker Service Check:"
if command -v docker-compose &> /dev/null; then
    if [ -f "docker-compose.https.yml" ]; then
        TRAEFIK_STATUS=$(docker-compose -f docker-compose.https.yml ps traefik 2>/dev/null | grep -c "Up" || echo "0")
        if [ "$TRAEFIK_STATUS" -gt 0 ]; then
            echo "✅ Traefik service is running"
        else
            echo "❌ Traefik service is not running"
            echo "   Run: docker-compose -f docker-compose.https.yml up -d"
        fi
    else
        echo "⚠️  docker-compose.https.yml not found"
    fi
else
    echo "⚠️  docker-compose not available"
fi

# Firewall check suggestions
echo ""
echo "🛡️  Firewall Configuration:"
echo "   Make sure these ports are open:"
echo "   - Port 80 (HTTP) - for ACME challenge and redirect"
echo "   - Port 443 (HTTPS) - for main application traffic"
echo ""
echo "   Common firewall commands:"
echo "   # UFW (Ubuntu)"
echo "   sudo ufw allow 80"
echo "   sudo ufw allow 443"
echo ""
echo "   # iptables"
echo "   sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT"
echo "   sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT"
echo ""
echo "   # firewalld (CentOS/RHEL)"
echo "   sudo firewall-cmd --permanent --add-port=80/tcp"
echo "   sudo firewall-cmd --permanent --add-port=443/tcp"
echo "   sudo firewall-cmd --reload"

echo ""
echo "🎯 Summary:"
if curl -s -I https://$DOMAIN > /dev/null 2>&1; then
    echo "✅ Your HTTPS setup appears to be working correctly!"
    echo "🌐 Access your application at: https://$DOMAIN"
else
    echo "❌ HTTPS is not working yet. Check the issues above."
    echo "💡 Common solutions:"
    echo "   1. Wait a few minutes for certificate issuance"
    echo "   2. Check firewall settings"
    echo "   3. Verify DNS configuration"
    echo "   4. Check Traefik logs: docker-compose -f docker-compose.https.yml logs traefik"
fi