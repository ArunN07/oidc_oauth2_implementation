#!/bin/bash
# Docker setup and verification script

set -e

echo "🐳 OIDC/OAuth2 Docker Setup"
echo "=============================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi
echo -e "${GREEN}✓ Docker is installed${NC}"

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed${NC}"
    echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi
echo -e "${GREEN}✓ Docker Compose is installed${NC}"

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker daemon is not running${NC}"
    echo "Please start Docker"
    exit 1
fi
echo -e "${GREEN}✓ Docker daemon is running${NC}"

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}❌ .env file not found${NC}"
    echo "Please create .env file with your configuration"
    exit 1
fi
echo -e "${GREEN}✓ .env file exists${NC}"

# Check if ports are available
echo ""
echo "Checking port availability..."
if lsof -Pi :8001 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${YELLOW}⚠️  Port 8001 is already in use${NC}"
    echo "Please stop the service using port 8001 or modify docker-compose.yml"
    lsof -Pi :8001 -sTCP:LISTEN
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✓ Port 8001 is available${NC}"
fi

if lsof -Pi :5432 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${YELLOW}⚠️  Port 5432 is already in use${NC}"
    echo "This might conflict with the PostgreSQL container"
    lsof -Pi :5432 -sTCP:LISTEN
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✓ Port 5432 is available${NC}"
fi

echo ""
echo "=============================="
echo -e "${GREEN}All checks passed!${NC}"
echo ""
echo "You can now start the services with:"
echo "  docker-compose up --build"
echo ""
echo "Or use the Makefile commands:"
echo "  make build    # Build images"
echo "  make up-d     # Start in background"
echo "  make logs     # View logs"
echo "  make health   # Check health"
echo "  make help     # See all commands"
echo ""
echo "Once started, access the application at:"
echo "  - API Docs: http://localhost:8001/docs"
echo "  - Health: http://localhost:8001/health"
echo ""

# Offer to start services
read -p "Would you like to start the services now? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Building and starting services..."
    docker-compose up --build -d

    echo ""
    echo "Waiting for services to be ready..."
    sleep 5

    echo ""
    echo "Checking service health..."
    if curl -f http://localhost:8001/health 2>/dev/null; then
        echo -e "${GREEN}✓ Application is healthy!${NC}"
        echo ""
        echo "Access the application at: http://localhost:8001/docs"
    else
        echo -e "${YELLOW}⚠️  Application is not responding yet${NC}"
        echo "Check logs with: docker-compose logs -f app"
    fi
fi

