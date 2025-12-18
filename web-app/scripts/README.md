# Web Invoice Processor - Production Scripts

This directory contains production deployment and management scripts for the Web Invoice Processor.

## Scripts Overview

### Deployment Scripts

#### `deploy.sh`
Main production deployment script with comprehensive error handling and rollback capabilities.

**Usage:**
```bash
./scripts/deploy.sh [command]
```

**Commands:**
- `deploy` - Full deployment (default)
- `status` - Show service status
- `logs` - Show service logs
- `stop` - Stop all services
- `restart` - Restart all services
- `backup` - Create backup before deployment
- `help` - Show help

**Features:**
- Prerequisites checking
- Configuration validation
- Automatic backup before deployment
- Health checks after deployment
- Rollback on failure
- Service status monitoring

#### `start.sh`, `start-dev.sh`
Container startup scripts for production and development environments.

**Features:**
- Environment validation
- Redis connectivity checks
- Storage directory creation
- Graceful error handling

#### `start-celery-worker.sh`, `start-celery-beat.sh`
Celery service startup scripts with proper configuration.

### Backup and Restore

#### `backup.sh`
Comprehensive backup and restore system for application data.

**Usage:**
```bash
./scripts/backup.sh <command> [options]
```

**Commands:**
- `backup [name]` - Create backup (optional custom name)
- `list` - List available backups
- `restore <name>` - Restore from backup
- `clean [days]` - Clean old backups (default: 7 days)
- `verify <name>` - Verify backup integrity

**Features:**
- Compressed backups with metadata
- Automatic cleanup of old backups
- Backup verification
- Service-aware restore (stops/starts services)

### Monitoring and Maintenance

#### `monitor.sh`
Real-time monitoring and health checking system.

**Usage:**
```bash
./scripts/monitor.sh <command> [options]
```

**Commands:**
- `status` - Show current system status
- `monitor [interval]` - Continuous monitoring (default: 30s)
- `alerts` - Check for alerts and issues
- `logs [service] [lines]` - Show logs
- `restart-unhealthy` - Restart unhealthy services

**Features:**
- Service health monitoring
- Resource usage tracking
- API health checks
- Redis connectivity monitoring
- Storage usage monitoring
- Automatic service restart
- Email alerts (configurable)

#### `setup-logging.sh`
Logging infrastructure setup and management.

**Features:**
- Log directory structure creation
- Log rotation configuration
- Log monitoring tools
- Error pattern detection
- Log aggregation utilities

### Configuration and Validation

#### `validate-config.py`
Configuration validation script that checks all environment variables and system requirements.

**Features:**
- Environment variable validation
- Storage directory checks
- Redis connectivity testing
- Configuration compliance verification

## Environment Variables

The scripts support the following environment variables:

### Required
- `REDIS_URL` - Redis connection URL
- `STORAGE_PATH` - Base storage path

### Optional
- `PORT` - Server port (default: 8000)
- `DEBUG` - Debug mode (default: false)
- `MAX_FILE_SIZE` - Maximum file size (default: 50MB)
- `CLEANUP_INTERVAL` - Cleanup interval in hours (default: 24)
- `MAX_CONCURRENT_TASKS` - Max concurrent tasks (default: 4)

## Directory Structure

After running the setup scripts, the following directory structure will be created:

```
web-app/
├── scripts/           # Production scripts
├── logs/             # Application logs
│   ├── web/          # Web service logs
│   ├── celery/       # Celery worker logs
│   ├── redis/        # Redis logs
│   └── aggregated/   # Aggregated log files
├── backups/          # Backup files
├── storage/          # Application storage
│   ├── uploads/      # Uploaded files
│   ├── outputs/      # Processed files
│   └── temp/         # Temporary files
└── .env              # Environment configuration
```

## Quick Start

1. **Initial Setup:**
   ```bash
   # Copy environment template
   cp .env.example .env
   
   # Edit configuration
   nano .env
   
   # Setup logging infrastructure
   ./scripts/setup-logging.sh
   
   # Validate configuration
   ./scripts/validate-config.py
   ```

2. **Deploy Application:**
   ```bash
   # Full deployment
   ./scripts/deploy.sh
   
   # Check status
   ./scripts/deploy.sh status
   ```

3. **Monitor System:**
   ```bash
   # Show current status
   ./scripts/monitor.sh status
   
   # Start continuous monitoring
   ./scripts/monitor.sh monitor
   
   # Check for issues
   ./scripts/monitor.sh alerts
   ```

4. **Backup Management:**
   ```bash
   # Create backup
   ./scripts/backup.sh backup
   
   # List backups
   ./scripts/backup.sh list
   
   # Restore from backup
   ./scripts/backup.sh restore <backup_name>
   ```

## Production Checklist

Before deploying to production:

- [ ] Configure environment variables in `.env`
- [ ] Set up log rotation with cron
- [ ] Configure email alerts in `monitor.sh`
- [ ] Test backup and restore procedures
- [ ] Verify all health checks pass
- [ ] Set up monitoring dashboards
- [ ] Configure firewall rules
- [ ] Set up SSL/TLS certificates (if using reverse proxy)

## Troubleshooting

### Common Issues

1. **Services not starting:**
   - Check environment variables: `./scripts/validate-config.py`
   - Verify Redis connectivity
   - Check storage permissions

2. **Health checks failing:**
   - Check service logs: `./scripts/monitor.sh logs`
   - Verify API endpoints are accessible
   - Check Redis connection

3. **High resource usage:**
   - Monitor resource usage: `./scripts/monitor.sh status`
   - Check for memory leaks in logs
   - Adjust `MAX_CONCURRENT_TASKS` if needed

4. **Backup/restore issues:**
   - Verify backup integrity: `./scripts/backup.sh verify <name>`
   - Check storage permissions
   - Ensure sufficient disk space

### Log Analysis

Use the logging tools to analyze issues:

```bash
# Check recent errors
./logs/monitor-logs.sh errors

# Aggregate logs by date
./logs/aggregate-logs.sh date 2023-12-01

# Check log file sizes
./logs/monitor-logs.sh sizes
```

## Security Considerations

- Store sensitive environment variables securely
- Regularly rotate backup encryption keys
- Monitor log files for security events
- Keep Docker images updated
- Use non-root users in containers
- Implement proper network security

## Maintenance Schedule

Recommended maintenance tasks:

- **Daily:** Check system status and alerts
- **Weekly:** Review logs for errors and performance issues
- **Monthly:** Clean old backups and logs
- **Quarterly:** Update Docker images and dependencies
- **Annually:** Review and update security configurations

## Support

For issues with the production scripts:

1. Check the logs: `./scripts/monitor.sh logs`
2. Validate configuration: `./scripts/validate-config.py`
3. Review system status: `./scripts/monitor.sh status`
4. Check backup integrity: `./scripts/backup.sh verify <latest>`

For application-specific issues, refer to the main application documentation.