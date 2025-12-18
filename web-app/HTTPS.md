# HTTPS Deployment Guide

This guide explains how to deploy the Web Invoice Processor with automatic HTTPS certificates using Let's Encrypt and Traefik.

## 🚀 Quick Start

### Option 1: Interactive Setup (Recommended)

```bash
./setup-https.sh
```

This script will guide you through the configuration and automatically deploy with HTTPS.

### Option 2: Manual Setup

1. **Copy environment template:**
   ```bash
   cp .env.https.example .env.https
   ```

2. **Edit configuration:**
   ```bash
   nano .env.https
   ```
   
   Required settings:
   - `DOMAIN=your-domain.com`
   - `ACME_EMAIL=your-email@example.com`
   - `TRAEFIK_AUTH=admin:$2y$10$...` (generate with `./scripts/generate-auth.sh`)

3. **Deploy:**
   ```bash
   ./scripts/deploy-https.sh
   ```

## 🔧 Configuration

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DOMAIN` | Your domain name | `example.com` |
| `TRAEFIK_DOMAIN` | Traefik dashboard domain | `traefik.example.com` |
| `ACME_EMAIL` | Email for Let's Encrypt | `admin@example.com` |
| `TRAEFIK_AUTH` | Dashboard authentication | `admin:$2y$10$...` |

### Generate Authentication

```bash
./scripts/generate-auth.sh admin mypassword
```

This will output a `TRAEFIK_AUTH` string to add to your `.env.https` file.

## 🌐 DNS Configuration

Before deployment, ensure your domain points to your server:

```bash
# Check current DNS
dig +short your-domain.com

# Should return your server's IP address
curl ifconfig.me
```

Both commands should return the same IP address.

### Port Requirements

Traefik automatically handles the following ports:
- **Port 80** (HTTP): Automatically redirects to HTTPS
- **Port 443** (HTTPS): Main application traffic with SSL certificates

Make sure these ports are open in your firewall:
```bash
# Check if ports are accessible
curl -I http://your-domain.com    # Should redirect to HTTPS
curl -I https://your-domain.com   # Should return 200 OK
```

## 🔒 Certificate Management

### Automatic Renewal

Certificates are automatically renewed by Traefik 30 days before expiration. No manual intervention required.

### Manual Management

```bash
# Check certificate status
./scripts/manage-certs.sh status

# List all certificates
./scripts/manage-certs.sh list

# Force renewal (if needed)
./scripts/manage-certs.sh renew

# Backup certificates
./scripts/manage-certs.sh backup

# View Traefik logs
./scripts/manage-certs.sh logs

# Check port accessibility
./scripts/check-ports.sh
```

## 📊 Monitoring

### Service Status

```bash
# Check all services
docker-compose -f docker-compose.https.yml ps

# View logs
docker-compose -f docker-compose.https.yml logs -f

# Check specific service
docker-compose -f docker-compose.https.yml logs traefik
```

### Access Points

After deployment, you can access:

- **Application**: `https://your-domain.com`
- **API Health**: `https://your-domain.com/api/health`
- **Traefik Dashboard**: `https://traefik.your-domain.com`

## 🛠️ Troubleshooting

### Common Issues

#### 1. Certificate Not Issued

**Symptoms**: HTTPS not working, browser shows "not secure"

**Solutions**:
```bash
# Check Traefik logs
docker-compose -f docker-compose.https.yml logs traefik

# Verify DNS
dig +short your-domain.com

# Check if port 80/443 are accessible
curl -I http://your-domain.com
```

#### 2. Domain Not Accessible

**Symptoms**: "This site can't be reached"

**Solutions**:
- Verify DNS configuration
- Check firewall settings (ports 80, 443)
- Ensure domain points to correct IP

#### 3. Traefik Dashboard Not Accessible

**Symptoms**: 404 or authentication issues

**Solutions**:
```bash
# Check Traefik service
docker-compose -f docker-compose.https.yml ps traefik

# Verify authentication string
echo "TRAEFIK_AUTH=$TRAEFIK_AUTH"

# Regenerate auth if needed
./scripts/generate-auth.sh admin newpassword
```

### Testing with Staging

To test certificate issuance without hitting rate limits:

```bash
./scripts/manage-certs.sh test
```

This uses Let's Encrypt staging server (certificates won't be trusted by browsers but validates the process).

### Force Certificate Renewal

If certificates are not renewing automatically:

```bash
./scripts/manage-certs.sh renew
```

## 🔐 Security Features

The HTTPS deployment includes:

- **Automatic HTTPS**: All HTTP traffic redirected to HTTPS
- **Security Headers**: HSTS, XSS protection, content type sniffing protection
- **Certificate Pinning**: HTTP Strict Transport Security with preload
- **Dashboard Protection**: Basic authentication for Traefik dashboard
- **Network Isolation**: Services isolated in Docker networks

## 📈 Performance

### Optimizations Included

- **HTTP/2**: Enabled by default with HTTPS
- **Gzip Compression**: Static assets compressed
- **Caching**: Appropriate cache headers for static files
- **CDN Ready**: Headers configured for CDN integration

### Monitoring Performance

```bash
# Check response times
curl -w "@curl-format.txt" -o /dev/null -s https://your-domain.com

# Monitor resource usage
docker stats
```

## 🔄 Updates and Maintenance

### Updating the Application

```bash
# Stop services
docker-compose -f docker-compose.https.yml down

# Pull updates
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.https.yml build --no-cache
docker-compose -f docker-compose.https.yml --env-file .env.https up -d
```

### Backup Strategy

```bash
# Backup certificates
./scripts/manage-certs.sh backup

# Backup application data
docker run --rm -v web-app_storage_data:/data -v $(pwd)/backups:/backup alpine tar czf /backup/storage-$(date +%Y%m%d).tar.gz -C /data .

# Backup Redis data
docker-compose -f docker-compose.https.yml exec redis redis-cli BGSAVE
```

## 🆘 Support

### Log Analysis

```bash
# Application logs
docker-compose -f docker-compose.https.yml logs backend

# Certificate logs
docker-compose -f docker-compose.https.yml logs traefik | grep -i acme

# All logs with timestamps
docker-compose -f docker-compose.https.yml logs -t -f
```

### Health Checks

```bash
# Application health
curl https://your-domain.com/api/health

# Certificate validity
echo | openssl s_client -servername your-domain.com -connect your-domain.com:443 2>/dev/null | openssl x509 -noout -dates
```

### Getting Help

1. Check the logs first
2. Verify DNS configuration
3. Test with staging server
4. Check firewall settings
5. Review Traefik documentation: https://doc.traefik.io/traefik/

## 📚 Additional Resources

- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Traefik Documentation](https://doc.traefik.io/traefik/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [SSL Labs Test](https://www.ssllabs.com/ssltest/) - Test your HTTPS configuration