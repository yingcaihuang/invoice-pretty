# Production Deployment Guide

This guide explains how to deploy the Web Invoice Processor in production using Docker Compose.

## Prerequisites

- Docker and Docker Compose installed
- At least 2GB RAM available
- 10GB+ disk space for file storage

## Quick Start

### HTTP Deployment (Basic)

1. **Clone and navigate to the project:**
   ```bash
   git clone <repository-url>
   cd web-app
   ```

2. **Create environment file:**
   ```bash
   cp .env.example .env
   ```

3. **Edit environment variables:**
   ```bash
   nano .env
   ```

4. **Start the application:**
   ```bash
   docker-compose up -d
   ```

### HTTPS Deployment (Recommended)

1. **Clone and navigate to the project:**
   ```bash
   git clone <repository-url>
   cd web-app
   ```

2. **Run the HTTPS deployment script:**
   ```bash
   ./scripts/deploy-https.sh
   ```

3. **Follow the prompts to configure:**
   - Your domain name
   - Email for Let's Encrypt
   - Traefik dashboard password

4. **Access your application:**
   - Application: `https://your-domain.com`
   - Traefik Dashboard: `https://traefik.your-domain.com`

The HTTPS deployment includes:
- ✅ Automatic SSL certificate generation via Let's Encrypt
- ✅ Automatic certificate renewal
- ✅ HTTP to HTTPS redirect
- ✅ Security headers
- ✅ Traefik reverse proxy with dashboard

## Service Architecture

The production deployment includes:

- **Frontend**: React app served by Nginx on port 3000
- **Backend**: FastAPI application on port 8000
- **Redis**: Data storage and task queue
- **Celery Worker**: Background PDF processing
- **Celery Beat**: Scheduled cleanup tasks

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BACKEND_PORT` | 8000 | Backend API port |
| `FRONTEND_PORT` | 3000 | Frontend web port |
| `REDIS_PORT` | 6379 | Redis port |
| `DEBUG` | false | Enable debug mode |
| `MAX_FILE_SIZE` | 52428800 | Max upload size (50MB) |
| `CLEANUP_INTERVAL` | 24 | File cleanup interval (hours) |
| `MAX_CONCURRENT_TASKS` | 4 | Concurrent processing tasks |
| `REACT_APP_API_URL` | http://localhost:8000 | Backend URL for frontend |

### Reverse Proxy Setup

For production, it's recommended to use a reverse proxy like Nginx:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Monitoring

### Health Checks

All services include health checks:
- Backend: `http://localhost:8000/health`
- Frontend: `http://localhost:3000`
- Redis: Built-in ping check

### Logs

View service logs:
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f celery-worker
```

### Storage Usage

Monitor storage usage:
```bash
# Check storage usage via API
curl http://localhost:8000/api/cleanup/storage/usage

# Check Docker volumes
docker volume ls
docker system df
```

## HTTPS Certificate Management

### Automatic Renewal

Certificates are automatically renewed by Traefik. No manual intervention required.

### Manual Certificate Management

```bash
# Check certificate status
./scripts/manage-certs.sh status

# List all certificates
./scripts/manage-certs.sh list

# Force certificate renewal
./scripts/manage-certs.sh renew

# Backup certificates
./scripts/manage-certs.sh backup

# Restore certificates
./scripts/manage-certs.sh restore

# View Traefik logs
./scripts/manage-certs.sh logs

# Test with staging server
./scripts/manage-certs.sh test
```

### Troubleshooting HTTPS

1. **Certificate not issued:**
   ```bash
   # Check Traefik logs
   docker-compose -f docker-compose.https.yml logs traefik
   
   # Verify DNS points to server
   dig +short your-domain.com
   ```

2. **Force certificate renewal:**
   ```bash
   ./scripts/manage-certs.sh renew
   ```

3. **Test with staging server:**
   ```bash
   ./scripts/manage-certs.sh test
   ```

## Maintenance

### Updates

**For HTTP deployment:**
```bash
docker-compose down
git pull origin main
docker-compose build --no-cache
docker-compose up -d
```

**For HTTPS deployment:**
```bash
docker-compose -f docker-compose.https.yml down
git pull origin main
docker-compose -f docker-compose.https.yml build --no-cache
docker-compose -f docker-compose.https.yml --env-file .env.https up -d
```

### Backup

1. **Backup Redis data:**
   ```bash
   docker-compose exec redis redis-cli BGSAVE
   docker cp $(docker-compose ps -q redis):/data/dump.rdb ./backup/
   ```

2. **Backup storage files:**
   ```bash
   docker run --rm -v web-app_storage_data:/data -v $(pwd)/backup:/backup alpine tar czf /backup/storage-$(date +%Y%m%d).tar.gz -C /data .
   ```

### Cleanup

1. **Manual cleanup:**
   ```bash
   # Trigger file cleanup
   curl -X POST http://localhost:8000/api/cleanup/files

   # Check cleanup status
   curl http://localhost:8000/api/cleanup/status
   ```

2. **Docker cleanup:**
   ```bash
   # Remove unused images
   docker image prune -f

   # Remove unused volumes
   docker volume prune -f
   ```

## Security

### Recommendations

1. **Use HTTPS in production**
2. **Set up firewall rules**
3. **Regular security updates**
4. **Monitor access logs**
5. **Use strong passwords for Redis if exposed**

### File Security

- Files are automatically deleted after 24 hours
- Session-based access control prevents cross-user access
- No permanent file storage

## Troubleshooting

### Common Issues

1. **Services not starting:**
   ```bash
   docker-compose logs
   ```

2. **Out of disk space:**
   ```bash
   df -h
   docker system prune -f
   ```

3. **High memory usage:**
   ```bash
   docker stats
   # Reduce MAX_CONCURRENT_TASKS
   ```

4. **Redis connection issues:**
   ```bash
   docker-compose exec redis redis-cli ping
   ```

### Performance Tuning

1. **Increase concurrent tasks** (if you have more CPU/RAM):
   ```bash
   MAX_CONCURRENT_TASKS=8
   ```

2. **Adjust cleanup interval** (for more/less storage usage):
   ```bash
   CLEANUP_INTERVAL=12  # Clean every 12 hours
   ```

3. **Monitor resource usage:**
   ```bash
   docker stats
   ```

## Support

For issues and questions:
1. Check the logs first
2. Review this documentation
3. Check the health endpoints
4. Monitor resource usage

The application includes comprehensive logging and monitoring to help diagnose issues quickly.