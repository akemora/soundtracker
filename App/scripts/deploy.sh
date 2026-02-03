#!/bin/bash
# SOUNDTRACKER Deploy Script
# Usage: ./scripts/deploy.sh [environment]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-production}
PROJECT_DIR=$(dirname "$(dirname "$(realpath "$0")")")

echo -e "${GREEN}=== SOUNDTRACKER Deploy Script ===${NC}"
echo -e "Environment: ${YELLOW}$ENVIRONMENT${NC}"
echo -e "Project directory: $PROJECT_DIR"
echo ""

# Navigate to project directory
cd "$PROJECT_DIR"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo -e "${GREEN}Checking prerequisites...${NC}"

if ! command_exists docker; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    exit 1
fi

if ! command_exists docker-compose && ! docker compose version >/dev/null 2>&1; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    exit 1
fi

# Use docker compose (v2) or docker-compose (v1)
if docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

echo -e "${GREEN}Using: $COMPOSE_CMD${NC}"
echo ""

# Pull latest changes (if git repo)
if [ -d ".git" ]; then
    echo -e "${GREEN}Pulling latest changes...${NC}"
    git pull origin main || echo -e "${YELLOW}Warning: Could not pull latest changes${NC}"
    echo ""
fi

# Stop existing containers
echo -e "${GREEN}Stopping existing containers...${NC}"
$COMPOSE_CMD down --remove-orphans || true
echo ""

# Build images
echo -e "${GREEN}Building Docker images...${NC}"
$COMPOSE_CMD build --no-cache
echo ""

# Start services
echo -e "${GREEN}Starting services...${NC}"
$COMPOSE_CMD up -d
echo ""

# Wait for services to be healthy
echo -e "${GREEN}Waiting for services to be healthy...${NC}"
sleep 10

# Check service status
echo -e "${GREEN}Checking service status...${NC}"
$COMPOSE_CMD ps

# Health check
echo ""
echo -e "${GREEN}Running health checks...${NC}"

# Backend health check
if curl -s http://localhost:8000/health >/dev/null; then
    echo -e "${GREEN}✓ Backend is healthy${NC}"
else
    echo -e "${RED}✗ Backend health check failed${NC}"
fi

# Frontend health check
if curl -s http://localhost:3000 >/dev/null; then
    echo -e "${GREEN}✓ Frontend is healthy${NC}"
else
    echo -e "${RED}✗ Frontend health check failed${NC}"
fi

echo ""
echo -e "${GREEN}=== Deploy Complete ===${NC}"
echo -e "Backend:  ${YELLOW}http://localhost:8000${NC}"
echo -e "Frontend: ${YELLOW}http://localhost:3000${NC}"
echo -e "API Docs: ${YELLOW}http://localhost:8000/docs${NC}"
