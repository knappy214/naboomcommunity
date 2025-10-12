#!/bin/bash

# =============================================================================
# Naboom Community Platform - Quick Build Script
# =============================================================================
# Fast build command for development and testing
# =============================================================================

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🚀 Naboom Community Platform - Quick Build${NC}"
echo "=============================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/upgrade dependencies
echo -e "${BLUE}Installing dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# Run migrations
echo -e "${BLUE}Running migrations...${NC}"
python manage.py migrate

# Collect static files
echo -e "${BLUE}Collecting static files...${NC}"
python manage.py collectstatic --noinput

# Create superuser if doesn't exist
echo -e "${BLUE}Checking superuser...${NC}"
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
echo -e "${BLUE}Setting up community structure...${NC}"
python manage.py setup_community || echo "Community setup command not found"

# Run checks
echo -e "${BLUE}Running system checks...${NC}"
python manage.py check

echo -e "${GREEN}✅ Quick build completed!${NC}"
echo ""
echo "Next steps:"
echo "  - Start dev server: make dev"
echo "  - Admin access: http://localhost:8000/admin/"
echo "  - Username: admin"
echo "  - Password: admin123"
