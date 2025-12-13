#!/usr/bin/env bash
# Run the FastAPI application - Works on Windows (Git Bash), Mac, Linux
# Usage: ./scripts/run.sh [--reload]

PORT=${PORT:-8001}
HOST=${HOST:-127.0.0.1}

if [ "$1" == "--reload" ]; then
    echo "🚀 Starting development server with auto-reload..."
    poetry run uvicorn src.fastapi.main:app --reload --host $HOST --port $PORT
else
    echo "🚀 Starting server..."
    poetry run uvicorn src.fastapi.main:app --host $HOST --port $PORT
fi

