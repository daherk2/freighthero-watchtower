#!/bin/bash
set -e

echo "=== Starting FreightHero Backend ==="
echo "Environment: $RAILWAY_ENVIRONMENT"
echo "Service: $RAILWAY_SERVICE_NAME"

# Check environment variables
echo "Checking environment variables..."
if [ -z "$DATABASE_URL" ]; then
    echo "ERROR: DATABASE_URL not set!"
    exit 1
fi
echo "DATABASE_URL: OK"

if [ -z "$REDIS_URL" ]; then
    echo "ERROR: REDIS_URL not set!"
    exit 1
fi
echo "REDIS_URL: OK"

if [ -z "$OPENAI_API_KEY" ]; then
    echo "ERROR: OPENAI_API_KEY not set!"
    exit 1
fi
echo "OPENAI_API_KEY: OK"

echo "Starting uvicorn..."
exec python -m uvicorn src.interfaces.app:app --host 0.0.0.0 --port 8000
