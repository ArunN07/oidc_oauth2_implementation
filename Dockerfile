FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies (cross-platform)
RUN apt-get update && apt-get install -y \
    curl \
    bash \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry==1.8.3

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Install dependencies (no venv in container)
RUN poetry config virtualenvs.create false && \
    poetry install --only main --no-interaction --no-ansi

# Copy application code
COPY src/ ./src/

# Create logs directory
RUN mkdir -p logs

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Default command (can be overridden by docker-compose)
# Production mode by default in Dockerfile
CMD ["uvicorn", "src.fastapi.main:app", "--host", "0.0.0.0", "--port", "8001"]
