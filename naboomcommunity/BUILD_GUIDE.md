# 🚀 Naboom Community Platform - Build Guide

## Overview

This guide provides comprehensive build commands for the Naboom Community Platform using Django 5.2 + Wagtail 7.1.1, optimized for production deployment without Docker.

## Quick Start

### 1. **Fast Development Build**
```bash
# Quick setup for development
./quick-build.sh

# Start development server
make dev
```

### 2. **Production Build**
```bash
# Full production build
./build.sh production

# Or using Makefile
make build
```

## Build Commands Reference

### **Main Build Scripts**

| Command | Purpose | Environment |
|---------|---------|-------------|
| `./quick-build.sh` | Fast development setup | Development |
| `./build.sh production` | Full production build | Production |
| `./build.sh staging` | Staging environment build | Staging |
| `./build.sh development` | Development environment build | Development |

### **Makefile Commands**

#### **Environment Setup**
```bash
make install          # Install all dependencies
make venv             # Create virtual environment
make dev              # Start development server
```

#### **Building**
```bash
make build            # Build for production
make build-staging    # Build for staging
make build-dev        # Build for development
```

#### **Database Operations**
```bash
make migrate          # Run database migrations
make makemigrations   # Create new migrations
make migrate-check    # Check migration status
make db-reset         # Reset database (WARNING: Destructive)
```

#### **Static Files**
```bash
make collectstatic        # Collect static files
make collectstatic-clear  # Clear and collect static files
```

#### **Wagtail Operations**
```bash
make wagtail-update-images    # Update image renditions
make wagtail-rebuild-index    # Rebuild search index
make wagtail-publish-scheduled # Publish scheduled content
make wagtail-purge-revisions  # Purge old revisions
```

#### **Testing & Quality**
```bash
make test             # Run all tests
make test-coverage    # Run tests with coverage
make lint             # Run code linting
make format           # Format code
make check            # Run Django checks
make check-deploy     # Run deployment checks
```

#### **Deployment**
```bash
make deploy           # Deploy to production
make deploy-staging   # Deploy to staging
make restart          # Restart all services
make status           # Check service status
make logs             # View application logs
```

#### **Maintenance**
```bash
make backup           # Create database backup
make clean            # Clean up temporary files
make clean-logs       # Clean old log files
make security-check   # Run security checks
```

## Build Process Details

### **1. Pre-build Checks**
- ✅ Verify required commands (python3, pip, node, npm)
- ✅ Check project directory structure
- ✅ Create/verify virtual environment
- ✅ Validate environment variables

### **2. Environment Setup**
- ✅ Create necessary directories
- ✅ Set proper permissions
- ✅ Configure environment variables
- ✅ Activate virtual environment

### **3. Python Dependencies**
- ✅ Upgrade pip, setuptools, wheel
- ✅ Install requirements from requirements.txt
- ✅ Install production-specific packages
- ✅ Verify package versions

### **4. Database Operations**
- ✅ Run Django system checks
- ✅ Execute database migrations
- ✅ Create superuser if needed
- ✅ Setup community structure
- ✅ Update search index

### **5. Static Files Collection**
- ✅ Clear existing static files
- ✅ Collect all static files
- ✅ Compress CSS and JS files
- ✅ Set proper permissions
- ✅ Optimize file structure

### **6. Wagtail Operations**
- ✅ Update image renditions
- ✅ Rebuild references index
- ✅ Publish scheduled content
- ✅ Purge old revisions

### **7. Performance Optimization**
- ✅ Clear all caches
- ✅ Warm up cache with common queries
- ✅ Optimize static file serving
- ✅ Configure compression

### **8. Security & Validation**
- ✅ Run Django security checks
- ✅ Validate configuration settings
- ✅ Check for common security issues
- ✅ Verify secret keys and allowed hosts

### **9. Service Management**
- ✅ Restart Gunicorn (HTTP server)
- ✅ Restart Daphne (WebSocket server)
- ✅ Restart Celery (Background tasks)
- ✅ Reload Nginx (Web server)

### **10. Backup & Cleanup**
- ✅ Create database backup
- ✅ Clean up old backups
- ✅ Remove old log files
- ✅ Optimize disk usage

## Environment-Specific Builds

### **Production Build**
```bash
./build.sh production
```
- Full security checks
- Production-optimized settings
- Service restart
- Database backup
- Performance optimization

### **Staging Build**
```bash
./build.sh staging
```
- Staging environment settings
- Limited security checks
- No service restart
- Development-friendly logging

### **Development Build**
```bash
./build.sh development
```
- Debug mode enabled
- Development settings
- Verbose logging
- Hot reloading support

## Service Configuration

### **Required Services**
- **Gunicorn**: ASGI server for Django HTTP
- **Daphne**: ASGI server for WebSocket connections
- **Celery**: Background task processing
- **Nginx**: Web server and reverse proxy
- **PostgreSQL**: Primary database
- **Redis**: Caching and message broker

### **Service Management**
```bash
# Check service status
make status

# Restart all services
make restart

# View logs
make logs

# Monitor resources
make monitor
```

## Performance Optimizations

### **Database**
- Connection pooling enabled
- Query optimization
- Index optimization
- Migration efficiency

### **Caching**
- Redis-based caching
- Static file caching
- API response caching
- Session caching

### **Static Files**
- Gzip compression
- Brotli compression
- CDN-ready structure
- Optimized file serving

### **HTTP/3 Support**
- QUIC protocol enabled
- Server push optimization
- Mobile network optimization
- Connection multiplexing

## Monitoring & Maintenance

### **Log Files**
- Application logs: `/var/log/naboom/django.log`
- Error logs: `/var/log/naboom/error.log`
- Access logs: `/var/log/nginx/access.log`

### **Backups**
- Database backups: `/var/backups/naboom/`
- Retention: 7 days
- Automatic cleanup

### **Health Checks**
```bash
# Check application health
curl -f http://localhost:8000/health/

# Check database connectivity
python manage.py dbshell

# Check Redis connectivity
redis-cli ping
```

## Troubleshooting

### **Common Issues**

1. **Build Fails on Dependencies**
   ```bash
   # Clear pip cache
   pip cache purge
   
   # Reinstall dependencies
   pip install --no-cache-dir -r requirements.txt
   ```

2. **Database Migration Errors**
   ```bash
   # Check migration status
   make migrate-check
   
   # Reset migrations if needed
   make db-reset
   ```

3. **Static Files Not Found**
   ```bash
   # Recollect static files
   make collectstatic-clear
   
   # Check permissions
   ls -la collected-static/
   ```

4. **Service Won't Start**
   ```bash
   # Check service status
   make status
   
   # View service logs
   journalctl -u gunicorn -f
   ```

### **Debug Commands**
```bash
# Django shell
make dev-shell

# Database shell
make monitor-db

# Redis monitor
make monitor-redis

# System resources
make monitor
```

## Security Considerations

### **Production Checklist**
- ✅ DEBUG = False
- ✅ SECRET_KEY properly configured
- ✅ ALLOWED_HOSTS configured
- ✅ HTTPS enabled
- ✅ Security headers configured
- ✅ Database credentials secured
- ✅ Static files served by web server

### **Security Commands**
```bash
# Run security checks
make security-check

# Check for vulnerabilities
make update-deps
```

## Best Practices

1. **Always run tests before deployment**
2. **Create backups before major changes**
3. **Use staging environment for testing**
4. **Monitor logs after deployment**
5. **Keep dependencies updated**
6. **Regular security audits**
7. **Performance monitoring**

## Support

For issues or questions:
- Check logs: `make logs`
- Run diagnostics: `make check-deploy`
- Review this guide
- Check Django documentation
- Check Wagtail documentation

---

**Last Updated**: $(date)
**Version**: 1.0.0
**Django**: 5.2.7
**Wagtail**: 7.1.1
