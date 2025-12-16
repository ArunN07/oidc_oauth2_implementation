# Docker Setup Guide

Complete guide for running this OIDC/OAuth2 FastAPI application with Docker on **Mac, Windows, and Linux**.

## Quick Start

```bash
# Development mode (hot reload enabled)
make dev

# Production mode (optimized)
make prod

# Or use docker-compose directly
docker-compose up
```

Access: http://localhost:8001/docs

## Prerequisites

- Docker Desktop (Mac/Windows) or Docker Engine (Linux)
- Docker Compose v2.0+

## Usage

### Development Mode (Default)

Hot reload enabled - code changes auto-refresh in 1-2 seconds:

```bash
make dev
# or
docker-compose up
```

**Features:**
- ✅ Hot reload (`--reload` flag)
- ✅ Debug logging (`LOG_LEVEL=DEBUG`)
- ✅ Source code mounted (live updates)

### Production Mode

Optimized mode without hot reload:

```bash
make prod
# or
DOCKER_MODE=prod DEBUG=false LOG_LEVEL=WARNING docker-compose up -d
```

**Features:**
- ✅ Optimized performance
- ✅ Warning-level logging only
- ✅ No auto-restart overhead

## Configuration

The `docker-compose.yml` uses environment variables to switch between dev/prod modes.

### Option 1: Set in .env file

```bash
# Development (default)
DOCKER_MODE=dev
DEBUG=true
LOG_LEVEL=DEBUG

# Production
DOCKER_MODE=prod
DEBUG=false
LOG_LEVEL=WARNING

# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=arun
POSTGRES_DB=postgres
POSTGRES_PORT=5432

# Application
APP_PORT=8001
```

### Option 2: Command line

```bash
# Development
DOCKER_MODE=dev docker-compose up

# Production
DOCKER_MODE=prod docker-compose up -d
```

## Cross-Platform Support

### macOS (Intel & Apple Silicon)
```bash
make dev
```
Works on M1/M2/M3 Macs with `platform: linux/amd64` setting.

### Windows (PowerShell)
```powershell
make dev
# or
$env:DOCKER_MODE="dev"
docker-compose up
```

### Windows (CMD)
```cmd
set DOCKER_MODE=dev && docker-compose up
```

### Linux
```bash
DOCKER_MODE=dev docker-compose up
```

## Services

### Application (oidc_oauth2_app)
- **Port:** 8001
- **Image:** Built from Dockerfile (Python 3.12)
- **Features:** FastAPI, OAuth2/OIDC support, hot reload (dev)
- **Volumes:** `./src` mounted for live updates, `./logs` for logs

### Database (oidc_oauth2_db)
- **Port:** 5432
- **Image:** postgres:15-alpine
- **Credentials:** postgres/arun
- **Database:** postgres
- **Volume:** Persistent data storage

## Common Commands

### Using Makefile

```bash
make dev          # Start development mode
make prod         # Start production mode
make logs         # View all logs
make logs-app     # View app logs only
make logs-db      # View database logs
make shell        # Access app container
make shell-db     # Access database (psql)
make health       # Check health endpoint
make restart      # Restart services
make down         # Stop services
make clean-all    # Full cleanup (removes data)
```

### Using docker-compose

```bash
# Start
docker-compose up              # Foreground
docker-compose up -d           # Background

# Logs
docker-compose logs -f         # All logs
docker-compose logs -f app     # App only

# Container access
docker-compose exec app bash
docker-compose exec db psql -U postgres

# Operations
docker-compose restart app
docker-compose down
docker-compose down -v         # Remove volumes
```

## Development Workflow

### 1. Start Development

```bash
make dev
```

### 2. Edit Code

```bash
vim src/core/auth/oidc_client.py
# Save → Auto-reloads in 1-2 seconds!
```

### 3. View Logs

```bash
# In another terminal
make logs-app
```

You'll see:
```
INFO: Will watch for changes in these directories: ['/app']
INFO: Detected file change, reloading...
INFO: Application startup complete.
```

### 4. Test Changes

Open http://localhost:8001/docs and test immediately!

## URLs

- **Swagger UI:** http://localhost:8001/docs
- **ReDoc:** http://localhost:8001/redoc
- **Health Check:** http://localhost:8001/health
- **Root:** http://localhost:8001/

## Troubleshooting

### Hot Reload Not Working?

Check the mode:
```bash
docker-compose exec app env | grep DOCKER_MODE
```

Should show `DOCKER_MODE=dev`. If not:
```bash
docker-compose down
DOCKER_MODE=dev docker-compose up
```

### Port 8001 Already in Use?

```bash
# Mac/Linux
lsof -i :8001

# Windows
netstat -ano | findstr :8001

# Change port in .env
APP_PORT=8002
```

### Database Connection Failed?

```bash
# Check database status
docker-compose logs db

# Restart database
docker-compose restart db

# Reset database
make db-reset
```

### Source Changes Not Reflecting?

Ensure source is mounted:
```bash
docker-compose config | grep -A 5 "volumes:"
```

Should see: `./src:/app/src`

### Container Won't Start?

```bash
# View logs
docker-compose logs app

# Rebuild from scratch
docker-compose down
docker-compose build --no-cache
docker-compose up
```

## How It Works

The `docker-compose.yml` uses a shell command to detect the `DOCKER_MODE` environment variable:

```yaml
command: >
  sh -c "
  if [ \"$${DOCKER_MODE:-dev}\" = \"prod\" ]; then
    uvicorn src.fastapi.main:app --host 0.0.0.0 --port 8001
  else
    uvicorn src.fastapi.main:app --host 0.0.0.0 --port 8001 --reload
  fi
  "
```

- **Default:** `dev` mode (hot reload enabled)
- **Production:** Set `DOCKER_MODE=prod` (no reload)

## Performance

### Development Mode
- **Hot Reload:** ✅ Yes
- **Code Change Time:** ~1-2 seconds
- **Startup Time:** ~15 seconds
- **Resource Usage:** Medium

### Production Mode
- **Hot Reload:** ❌ No
- **Code Change Time:** Rebuild required
- **Startup Time:** ~10 seconds
- **Resource Usage:** Low

## Production Deployment Tips

1. **Set production mode:**
   ```bash
   DOCKER_MODE=prod
   DEBUG=false
   LOG_LEVEL=WARNING
   ```

2. **Use external database** instead of containerized PostgreSQL

3. **Remove source mounting** (optional):
   Edit docker-compose.yml and comment out:
   ```yaml
   # - type: bind
   #   source: ./src
   #   target: /app/src
   ```

4. **Use Docker secrets** for sensitive data

5. **Add reverse proxy** (nginx/traefik) with HTTPS

6. **Update OAuth redirect URIs** to production domain

## Environment Variables

### Docker Configuration
- `DOCKER_MODE` - Mode: `dev` (default) or `prod`
- `DEBUG` - Debug mode: `true` or `false`
- `LOG_LEVEL` - Log level: `DEBUG`, `INFO`, `WARNING`, `ERROR`

### Database
- `POSTGRES_USER` - Database user (default: `postgres`)
- `POSTGRES_PASSWORD` - Database password (default: `arun`)
- `POSTGRES_DB` - Database name (default: `postgres`)
- `POSTGRES_PORT` - Database port (default: `5432`)

### Application
- `APP_PORT` - Application port (default: `8001`)
- `BACKEND_DB_URL` - Auto-configured to use Docker service name

### Proxy (Optional - Comment out when not needed)
**Important:** Empty proxy variables cause errors. Comment them out if not using a proxy.

```bash
# Only uncomment if you need proxy:
# HTTP_PROXY=http://proxy.example.com:8080
# HTTPS_PROXY=http://proxy.example.com:8080
# NO_PROXY=localhost,127.0.0.1,db
```

### OAuth Providers
Configure in `.env` file:
- `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`
- `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID`
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`
- `AUTH0_DOMAIN`, `AUTH0_CLIENT_ID`, `AUTH0_CLIENT_SECRET`

## Summary

- ✅ **Single `docker-compose.yml`** - Works everywhere
- ✅ **Dev/Prod modes** - Switch via `DOCKER_MODE` variable
- ✅ **Hot reload** - Instant code changes in dev mode
- ✅ **Cross-platform** - Mac, Windows, Linux compatible
- ✅ **Simple commands** - `make dev` or `make prod`
- ✅ **Persistent data** - Database survives restarts

**Start developing:**
```bash
make dev
open http://localhost:8001/docs
```

