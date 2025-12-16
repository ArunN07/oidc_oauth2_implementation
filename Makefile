.PHONY: help build up down restart logs logs-app logs-db shell shell-db clean clean-all ps health test dev prod

# Default target
help:
	@echo "Available commands:"
	@echo ""
	@echo "Development:"
	@echo "  make dev        - Start in development mode (hot reload)"
	@echo "  make prod       - Start in production mode (optimized)"
	@echo ""
	@echo "Basic Operations:"
	@echo "  make build      - Build Docker images"
	@echo "  make up         - Start services in foreground (dev mode)"
	@echo "  make up-d       - Start services in background (dev mode)"
	@echo "  make down       - Stop and remove containers"
	@echo "  make restart    - Restart all services"
	@echo ""
	@echo "Monitoring:"
	@echo "  make logs       - Follow all logs"
	@echo "  make logs-app   - Follow app logs"
	@echo "  make logs-db    - Follow database logs"
	@echo "  make ps         - Show running containers"
	@echo "  make health     - Check service health"
	@echo ""
	@echo "Container Access:"
	@echo "  make shell      - Access app container shell"
	@echo "  make shell-db   - Access database shell"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean      - Stop and remove containers (keep volumes)"
	@echo "  make clean-all  - Stop and remove containers and volumes"
	@echo ""
	@echo "Testing:"
	@echo "  make test       - Run tests in container"

# Build Docker images
build:
	docker-compose build

# Development mode (hot reload enabled)
dev:
	DOCKER_MODE=dev docker-compose up --build

# Production mode (optimized, no reload)
prod:
	DOCKER_MODE=prod DEBUG=false LOG_LEVEL=WARNING docker-compose up --build -d

# Start services
up:
	docker-compose up

up-d:
	docker-compose up -d

# Stop services
down:
	docker-compose down

stop:
	docker-compose stop

# Restart services
restart:
	docker-compose restart

restart-app:
	docker-compose restart app

restart-db:
	docker-compose restart db

# View logs
logs:
	docker-compose logs -f

logs-app:
	docker-compose logs -f app

logs-db:
	docker-compose logs -f db

# Access containers
shell:
	docker-compose exec app bash

shell-db:
	docker-compose exec db psql -U postgres -d postgres

# Show container status
ps:
	docker-compose ps

# Health check
health:
	@echo "Checking health..."
	@curl -f http://localhost:8001/health || echo "Service not responding"

# Clean up
clean:
	docker-compose down

clean-all:
	docker-compose down -v
	rm -rf logs/*


# Run tests
test:
	docker-compose exec app pytest

# Database operations
db-reset:
	docker-compose down -v
	docker-compose up -d db
	@echo "Waiting for database to be ready..."
	@sleep 5
	docker-compose up -d app

# Show environment
env:
	docker-compose exec app env | grep -E '(GITHUB|AZURE|GOOGLE|AUTH0|BACKEND)' | sort

