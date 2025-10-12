# =============================================================================
# Naboom Community Platform - Makefile
# =============================================================================
# This Makefile provides convenient commands for building, testing, and
# deploying the Naboom Community Platform
# =============================================================================

.PHONY: help build test deploy clean install dev prod staging

# Default target
.DEFAULT_GOAL := help

# Configuration
PROJECT_NAME = naboomcommunity
PYTHON = python3
PIP = pip
VENV_DIR = venv
STATIC_ROOT = collected-static
MEDIA_ROOT = media
LOG_DIR = /var/log/naboom

# Colors
RED = \033[0;31m
GREEN = \033[0;32m
YELLOW = \033[1;33m
BLUE = \033[0;34m
NC = \033[0m

# =============================================================================
# Help
# =============================================================================

help: ## Show this help message
	@echo "$(BLUE)Naboom Community Platform - Available Commands$(NC)"
	@echo "=================================================="
	@echo ""
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "$(YELLOW)Examples:$(NC)"
	@echo "  make dev          # Start development environment"
	@echo "  make build        # Build for production"
	@echo "  make test         # Run all tests"
	@echo "  make deploy       # Deploy to production"

# =============================================================================
# Environment Setup
# =============================================================================

install: ## Install all dependencies
	@echo "$(BLUE)Installing dependencies...$(NC)"
	$(PYTHON) -m venv $(VENV_DIR)
	. $(VENV_DIR)/bin/activate && $(PIP) install --upgrade pip setuptools wheel
	. $(VENV_DIR)/bin/activate && $(PIP) install -r requirements.txt
	@echo "$(GREEN)Dependencies installed$(NC)"

venv: ## Create virtual environment
	@echo "$(BLUE)Creating virtual environment...$(NC)"
	$(PYTHON) -m venv $(VENV_DIR)
	. $(VENV_DIR)/bin/activate && $(PIP) install --upgrade pip
	@echo "$(GREEN)Virtual environment created$(NC)"

# =============================================================================
# Development
# =============================================================================

dev: ## Start development server
	@echo "$(BLUE)Starting development server...$(NC)"
	. $(VENV_DIR)/bin/activate && $(PYTHON) manage.py runserver 0.0.0.0:8000

dev-migrate: ## Run migrations in development
	@echo "$(BLUE)Running migrations...$(NC)"
	. $(VENV_DIR)/bin/activate && $(PYTHON) manage.py migrate

dev-collectstatic: ## Collect static files in development
	@echo "$(BLUE)Collecting static files...$(NC)"
	. $(VENV_DIR)/bin/activate && $(PYTHON) manage.py collectstatic --noinput

dev-superuser: ## Create superuser
	@echo "$(BLUE)Creating superuser...$(NC)"
	. $(VENV_DIR)/bin/activate && $(PYTHON) manage.py createsuperuser

dev-shell: ## Open Django shell
	@echo "$(BLUE)Opening Django shell...$(NC)"
	. $(VENV_DIR)/bin/activate && $(PYTHON) manage.py shell

# =============================================================================
# Building
# =============================================================================

build: ## Build for production
	@echo "$(BLUE)Building for production...$(NC)"
	./build.sh production
	@echo "$(GREEN)Build completed$(NC)"

build-staging: ## Build for staging
	@echo "$(BLUE)Building for staging...$(NC)"
	./build.sh staging
	@echo "$(GREEN)Staging build completed$(NC)"

build-dev: ## Build for development
	@echo "$(BLUE)Building for development...$(NC)"
	./build.sh development
	@echo "$(GREEN)Development build completed$(NC)"

# =============================================================================
# Database Operations
# =============================================================================

migrate: ## Run database migrations
	@echo "$(BLUE)Running migrations...$(NC)"
	. $(VENV_DIR)/bin/activate && $(PYTHON) manage.py migrate
	@echo "$(GREEN)Migrations completed$(NC)"

makemigrations: ## Create new migrations
	@echo "$(BLUE)Creating migrations...$(NC)"
	. $(VENV_DIR)/bin/activate && $(PYTHON) manage.py makemigrations
	@echo "$(GREEN)Migrations created$(NC)"

migrate-check: ## Check migration status
	@echo "$(BLUE)Checking migration status...$(NC)"
	. $(VENV_DIR)/bin/activate && $(PYTHON) manage.py showmigrations

db-reset: ## Reset database (WARNING: Destructive)
	@echo "$(RED)WARNING: This will delete all data!$(NC)"
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ]
	. $(VENV_DIR)/bin/activate && $(PYTHON) manage.py flush --noinput
	. $(VENV_DIR)/bin/activate && $(PYTHON) manage.py migrate
	. $(VENV_DIR)/bin/activate && $(PYTHON) manage.py setup_community
	@echo "$(GREEN)Database reset completed$(NC)"

# =============================================================================
# Static Files
# =============================================================================

collectstatic: ## Collect static files
	@echo "$(BLUE)Collecting static files...$(NC)"
	. $(VENV_DIR)/bin/activate && $(PYTHON) manage.py collectstatic --noinput
	@echo "$(GREEN)Static files collected$(NC)"

collectstatic-clear: ## Clear and collect static files
	@echo "$(BLUE)Clearing and collecting static files...$(NC)"
	. $(VENV_DIR)/bin/activate && $(PYTHON) manage.py collectstatic --noinput --clear
	@echo "$(GREEN)Static files cleared and collected$(NC)"

# =============================================================================
# Wagtail Operations
# =============================================================================

wagtail-update-images: ## Update Wagtail image renditions
	@echo "$(BLUE)Updating image renditions...$(NC)"
	. $(VENV_DIR)/bin/activate && $(PYTHON) manage.py wagtail_update_image_renditions
	@echo "$(GREEN)Image renditions updated$(NC)"

wagtail-rebuild-index: ## Rebuild search index
	@echo "$(BLUE)Rebuilding search index...$(NC)"
	. $(VENV_DIR)/bin/activate && $(PYTHON) manage.py update_index
	@echo "$(GREEN)Search index rebuilt$(NC)"

wagtail-publish-scheduled: ## Publish scheduled content
	@echo "$(BLUE)Publishing scheduled content...$(NC)"
	. $(VENV_DIR)/bin/activate && $(PYTHON) manage.py publish_scheduled
	@echo "$(GREEN)Scheduled content published$(NC)"

wagtail-purge-revisions: ## Purge old revisions
	@echo "$(BLUE)Purging old revisions...$(NC)"
	. $(VENV_DIR)/bin/activate && $(PYTHON) manage.py purge_revisions --days=30 --keep-latest
	@echo "$(GREEN)Old revisions purged$(NC)"

# =============================================================================
# Testing
# =============================================================================

test: ## Run all tests
	@echo "$(BLUE)Running tests...$(NC)"
	. $(VENV_DIR)/bin/activate && $(PYTHON) manage.py test
	@echo "$(GREEN)Tests completed$(NC)"

test-coverage: ## Run tests with coverage
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	. $(VENV_DIR)/bin/activate && coverage run --source='.' manage.py test
	. $(VENV_DIR)/bin/activate && coverage report
	. $(VENV_DIR)/bin/activate && coverage html
	@echo "$(GREEN)Coverage report generated$(NC)"

test-specific: ## Run specific test (usage: make test-specific TEST=app.tests.TestClass.test_method)
	@echo "$(BLUE)Running specific test: $(TEST)$(NC)"
	. $(VENV_DIR)/bin/activate && $(PYTHON) manage.py test $(TEST)
	@echo "$(GREEN)Test completed$(NC)"

# =============================================================================
# Code Quality
# =============================================================================

lint: ## Run code linting
	@echo "$(BLUE)Running code linting...$(NC)"
	. $(VENV_DIR)/bin/activate && flake8 .
	. $(VENV_DIR)/bin/activate && black --check .
	. $(VENV_DIR)/bin/activate && isort --check-only .
	@echo "$(GREEN)Linting completed$(NC)"

format: ## Format code
	@echo "$(BLUE)Formatting code...$(NC)"
	. $(VENV_DIR)/bin/activate && black .
	. $(VENV_DIR)/bin/activate && isort .
	@echo "$(GREEN)Code formatted$(NC)"

check: ## Run Django checks
	@echo "$(BLUE)Running Django checks...$(NC)"
	. $(VENV_DIR)/bin/activate && $(PYTHON) manage.py check
	@echo "$(GREEN)Django checks completed$(NC)"

check-deploy: ## Run deployment checks
	@echo "$(BLUE)Running deployment checks...$(NC)"
	. $(VENV_DIR)/bin/activate && $(PYTHON) manage.py check --deploy
	@echo "$(GREEN)Deployment checks completed$(NC)"

# =============================================================================
# Deployment
# =============================================================================

deploy: ## Deploy to production
	@echo "$(BLUE)Deploying to production...$(NC)"
	./build.sh production
	@echo "$(GREEN)Deployment completed$(NC)"

deploy-staging: ## Deploy to staging
	@echo "$(BLUE)Deploying to staging...$(NC)"
	./build.sh staging
	@echo "$(GREEN)Staging deployment completed$(NC)"

restart: ## Restart all services
	@echo "$(BLUE)Restarting services...$(NC)"
	sudo systemctl restart gunicorn daphne celery nginx
	@echo "$(GREEN)Services restarted$(NC)"

status: ## Check service status
	@echo "$(BLUE)Checking service status...$(NC)"
	systemctl status gunicorn daphne celery nginx --no-pager

logs: ## View application logs
	@echo "$(BLUE)Viewing application logs...$(NC)"
	tail -f $(LOG_DIR)/django.log

# =============================================================================
# Maintenance
# =============================================================================

backup: ## Create database backup
	@echo "$(BLUE)Creating database backup...$(NC)"
	mkdir -p /var/backups/naboom
	pg_dump -h localhost -U naboomneighbornetdb_user naboomneighbornetdb > /var/backups/naboom/db_backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)Database backup created$(NC)"

clean: ## Clean up temporary files
	@echo "$(BLUE)Cleaning up...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.log" -delete
	rm -rf $(STATIC_ROOT)/*
	@echo "$(GREEN)Cleanup completed$(NC)"

clean-logs: ## Clean old log files
	@echo "$(BLUE)Cleaning old log files...$(NC)"
	find $(LOG_DIR) -name "*.log" -mtime +30 -delete
	@echo "$(GREEN)Log cleanup completed$(NC)"

# =============================================================================
# Monitoring
# =============================================================================

monitor: ## Monitor system resources
	@echo "$(BLUE)Monitoring system resources...$(NC)"
	htop

monitor-db: ## Monitor database connections
	@echo "$(BLUE)Monitoring database connections...$(NC)"
	. $(VENV_DIR)/bin/activate && $(PYTHON) manage.py dbshell

monitor-redis: ## Monitor Redis
	@echo "$(BLUE)Monitoring Redis...$(NC)"
	redis-cli monitor

# =============================================================================
# Quick Commands
# =============================================================================

quick-start: install dev-migrate dev-collectstatic dev-superuser ## Quick start setup
	@echo "$(GREEN)Quick start completed!$(NC)"
	@echo "$(YELLOW)Run 'make dev' to start the development server$(NC)"

quick-deploy: check-deploy build restart ## Quick production deployment
	@echo "$(GREEN)Quick deployment completed!$(NC)"

# =============================================================================
# Documentation
# =============================================================================

docs: ## Generate documentation
	@echo "$(BLUE)Generating documentation...$(NC)"
	. $(VENV_DIR)/bin/activate && sphinx-build -b html docs/ docs/_build/html/
	@echo "$(GREEN)Documentation generated$(NC)"

# =============================================================================
# Security
# =============================================================================

security-check: ## Run security checks
	@echo "$(BLUE)Running security checks...$(NC)"
	. $(VENV_DIR)/bin/activate && $(PYTHON) manage.py check --deploy --tag security
	. $(VENV_DIR)/bin/activate && safety check
	@echo "$(GREEN)Security checks completed$(NC)"

update-deps: ## Update dependencies
	@echo "$(BLUE)Updating dependencies...$(NC)"
	. $(VENV_DIR)/bin/activate && $(PIP) install --upgrade pip
	. $(VENV_DIR)/bin/activate && $(PIP) list --outdated
	@echo "$(YELLOW)Review outdated packages and update as needed$(NC)"
