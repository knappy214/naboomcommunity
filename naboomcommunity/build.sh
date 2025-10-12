#!/bin/bash

# =============================================================================
# Naboom Community Platform - Production Build Script
# =============================================================================
# This script handles the complete build and deployment process for the
# Naboom Community Platform using Django 5.2 + Wagtail 7.1.1
# =============================================================================

set -e  # Exit on any error
set -u  # Exit on undefined variables

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="naboomcommunity"
PROJECT_DIR="/var/www/naboomcommunity/naboomcommunity"
VENV_DIR="/var/www/naboomcommunity/naboomcommunity/venv"
STATIC_ROOT="/var/www/naboomcommunity/naboomcommunity/collected-static"
MEDIA_ROOT="/var/www/naboomcommunity/naboomcommunity/media"
LOG_DIR="/var/log/naboom"
BACKUP_DIR="/var/backups/naboom"
PYTHON_VERSION="3.12.3"
PYTHONPATH="/var/www/naboomcommunity/naboomcommunity/venv/bin/python3.12"

# Environment detection
ENVIRONMENT=${1:-production}
DJANGO_SETTINGS_MODULE="naboomcommunity.settings.${ENVIRONMENT}"

# =============================================================================
# Utility Functions
# =============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "Required command '$1' not found. Please install it first."
        exit 1
    fi
}

# =============================================================================
# Pre-build Checks
# =============================================================================

pre_build_checks() {
    log_info "Running pre-build checks..."
    
    # Check required commands
    check_command "python3"
    check_command "pip"
    check_command "node"
    check_command "npm"
    
    # Check if we're in the right directory
    if [ ! -f "manage.py" ]; then
        log_error "manage.py not found. Please run this script from the project root."
        exit 1
    fi
    
    # Check if virtual environment exists
    if [ ! -d "$VENV_DIR" ]; then
        log_warning "Virtual environment not found. Creating one..."
        python3 -m venv "$VENV_DIR"
    fi
    
    # Activate virtual environment
    source "$VENV_DIR/bin/activate"
    
    log_success "Pre-build checks completed"
}

# =============================================================================
# Environment Setup
# =============================================================================

setup_environment() {
    log_info "Setting up environment for $ENVIRONMENT..."
    
    # Create necessary directories
    mkdir -p "$STATIC_ROOT"
    mkdir -p "$MEDIA_ROOT"
    mkdir -p "$LOG_DIR"
    mkdir -p "$BACKUP_DIR"
    
    # Set proper permissions
    chmod 755 "$STATIC_ROOT"
    chmod 755 "$MEDIA_ROOT"
    chmod 755 "$LOG_DIR"
    chmod 755 "$BACKUP_DIR"
    
    # Set environment variables
    export DJANGO_SETTINGS_MODULE="$DJANGO_SETTINGS_MODULE"
    export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"
    
    log_success "Environment setup completed"
}

# =============================================================================
# Python Dependencies
# =============================================================================

install_python_deps() {
    log_info "Installing Python dependencies..."
    
    # Upgrade pip
    pip install --upgrade pip setuptools wheel
    
    # Install requirements
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    elif [ -f "requirements/production.txt" ]; then
        pip install -r requirements/production.txt
    else
        log_warning "No requirements file found. Installing basic dependencies..."
        pip install django==5.2 wagtail==7.1.1
    fi
    
    # Install additional production dependencies
    pip install gunicorn psycopg2-binary redis celery django-redis \
                django-storages boto3 pillow django-cors-headers \
                channels channels-redis django-environ
    
    log_success "Python dependencies installed"
}

# =============================================================================
# Database Operations
# =============================================================================

setup_database() {
    log_info "Setting up database..."
    
    # Run database checks
    python manage.py check --deploy
    
    # Run migrations
    log_info "Running database migrations..."
    python manage.py migrate --noinput
    
    # Create superuser if it doesn't exist
    log_info "Checking for superuser..."
    python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@naboomcommunity.co.za', 'admin123')
    print('Superuser created')
else:
    print('Superuser already exists')
"
    
    # Setup community structure
    log_info "Setting up community structure..."
    python manage.py setup_community || log_warning "Community setup command not found or failed"
    
    # Update search index
    log_info "Updating search index..."
    python manage.py update_index || log_warning "Search index update failed"
    
    log_success "Database setup completed"
}

# =============================================================================
# Static Files Collection
# =============================================================================

collect_static_files() {
    log_info "Collecting static files..."
    
    # Clear existing static files
    if [ -d "$STATIC_ROOT" ]; then
        rm -rf "$STATIC_ROOT"/*
    fi
    
    # Collect static files
    python manage.py collectstatic --noinput --clear
    
    # Optimize static files
    log_info "Optimizing static files..."
    
    # Compress CSS and JS files
    find "$STATIC_ROOT" -name "*.css" -exec gzip -k {} \;
    find "$STATIC_ROOT" -name "*.js" -exec gzip -k {} \;
    
    # Set proper permissions
    chmod -R 644 "$STATIC_ROOT"
    find "$STATIC_ROOT" -type d -exec chmod 755 {} \;
    
    log_success "Static files collected and optimized"
}

# =============================================================================
# Wagtail Specific Operations
# =============================================================================

wagtail_operations() {
    log_info "Running Wagtail-specific operations..."
    
    # Update image renditions
    log_info "Updating image renditions..."
    python manage.py wagtail_update_image_renditions || log_warning "Image renditions update failed"
    
    # Rebuild references index
    log_info "Rebuilding references index..."
    python manage.py rebuild_references_index || log_warning "References index rebuild failed"
    
    # Publish scheduled content
    log_info "Publishing scheduled content..."
    python manage.py publish_scheduled || log_warning "Scheduled content publish failed"
    
    # Purge old revisions (keep last 10)
    log_info "Purging old revisions..."
    python manage.py purge_revisions --days=30 || log_warning "Revision purge failed"
    
    log_success "Wagtail operations completed"
}

# =============================================================================
# Frontend Build (if applicable)
# =============================================================================

build_frontend() {
    log_info "Building frontend assets..."
    
    # Check if package.json exists
    if [ -f "package.json" ]; then
        # Install Node.js dependencies
        npm ci --production
        
        # Build frontend assets
        if [ -f "webpack.config.js" ] || [ -f "vite.config.js" ]; then
            npm run build
        fi
        
        log_success "Frontend assets built"
    else
        log_info "No frontend build required"
    fi
}

# =============================================================================
# Cache and Performance
# =============================================================================

optimize_performance() {
    log_info "Optimizing performance..."
    
    # Clear all caches
    python manage.py shell -c "
from django.core.cache import cache
cache.clear()
print('Cache cleared')
"
    
    # Warm up cache with common queries
    log_info "Warming up cache..."
    python manage.py shell -c "
from django.contrib.auth import get_user_model
from home.models import UserGroup
User = get_user_model()

# Warm up common queries
User.objects.count()
UserGroup.objects.count()
print('Cache warmed up')
"
    
    log_success "Performance optimization completed"
}

# =============================================================================
# Security and Validation
# =============================================================================

security_checks() {
    log_info "Running security checks..."
    
    # Run Django security checks
    python manage.py check --deploy --tag security
    
    # Check for common security issues
    python manage.py shell -c "
from django.conf import settings
import os

# Check for debug mode
if settings.DEBUG:
    print('WARNING: DEBUG mode is enabled in production!')

# Check for secret key
if not settings.SECRET_KEY or settings.SECRET_KEY == 'your-secret-key-here':
    print('WARNING: SECRET_KEY is not properly configured!')

# Check for allowed hosts
if not settings.ALLOWED_HOSTS or '*' in settings.ALLOWED_HOSTS:
    print('WARNING: ALLOWED_HOSTS is not properly configured!')

print('Security checks completed')
"
    
    log_success "Security checks completed"
}

# =============================================================================
# Service Management
# =============================================================================

restart_services() {
    log_info "Restarting services..."
    
    # Restart Gunicorn
    if systemctl is-active --quiet gunicorn; then
        systemctl restart gunicorn
        log_success "Gunicorn restarted"
    fi
    
    # Restart Daphne (WebSocket server)
    if systemctl is-active --quiet daphne; then
        systemctl restart daphne
        log_success "Daphne restarted"
    fi
    
    # Restart Celery
    if systemctl is-active --quiet celery; then
        systemctl restart celery
        log_success "Celery restarted"
    fi
    
    # Reload Nginx
    if systemctl is-active --quiet nginx; then
        nginx -t && systemctl reload nginx
        log_success "Nginx reloaded"
    fi
}

# =============================================================================
# Backup and Cleanup
# =============================================================================

backup_and_cleanup() {
    log_info "Creating backup and cleaning up..."
    
    # Create database backup
    BACKUP_FILE="$BACKUP_DIR/db_backup_$(date +%Y%m%d_%H%M%S).sql"
    pg_dump -h localhost -U naboomneighbornetdb_user naboomneighbornetdb > "$BACKUP_FILE"
    log_success "Database backup created: $BACKUP_FILE"
    
    # Clean up old backups (keep last 7 days)
    find "$BACKUP_DIR" -name "db_backup_*.sql" -mtime +7 -delete
    
    # Clean up old log files
    find "$LOG_DIR" -name "*.log" -mtime +30 -delete
    
    log_success "Backup and cleanup completed"
}

# =============================================================================
# Main Build Process
# =============================================================================

main() {
    log_info "Starting Naboom Community Platform build process..."
    log_info "Environment: $ENVIRONMENT"
    log_info "Project Directory: $PROJECT_DIR"
    
    # Change to project directory
    cd "$PROJECT_DIR"
    
    # Run build steps
    pre_build_checks
    setup_environment
    install_python_deps
    setup_database
    collect_static_files
    wagtail_operations
    build_frontend
    optimize_performance
    security_checks
    backup_and_cleanup
    restart_services
    
    log_success "Build process completed successfully!"
    log_info "Application is ready for production use."
    
    # Display useful information
    echo ""
    log_info "Useful commands:"
    echo "  - View logs: tail -f $LOG_DIR/django.log"
    echo "  - Check status: systemctl status gunicorn daphne celery nginx"
    echo "  - Admin access: https://naboomneighbornet.net.za/admin/"
    echo "  - API docs: https://naboomneighbornet.net.za/api/docs/"
    echo ""
}

# =============================================================================
# Script Execution
# =============================================================================

# Show usage if help requested
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
    echo "Usage: $0 [environment]"
    echo ""
    echo "Environments:"
    echo "  production  - Production build (default)"
    echo "  staging     - Staging build"
    echo "  development - Development build"
    echo ""
    echo "Examples:"
    echo "  $0                    # Production build"
    echo "  $0 staging           # Staging build"
    echo "  $0 development       # Development build"
    echo ""
    exit 0
fi

# Run main function
main "$@"
