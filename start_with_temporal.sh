#!/bin/bash

# Startup script for running Django with Temporal worker
# This script starts the Temporal worker alongside the Django development server

set -e

echo "Starting Django application with Temporal worker..."

# Wait for Temporal server to be ready
echo "Waiting for Temporal server to be ready..."
while ! nc -z localhost 7233; do
  sleep 1
done
echo "Temporal server is ready!"

# Start the Temporal worker in the background
echo "Starting Temporal worker..."
python manage.py run_temporal_worker --temporal-address=temporal:7233 &
WORKER_PID=$!

# Function to cleanup background processes
cleanup() {
    echo "Stopping background processes..."
    if [ ! -z "$WORKER_PID" ]; then
        kill $WORKER_PID 2>/dev/null || true
    fi
    exit 0
}

# Set trap to cleanup on exit
trap cleanup EXIT INT TERM

# Start Django development server
echo "Starting Django development server..."
python manage.py runserver 0.0.0.0:8000

# Wait for worker to finish (should never happen in normal operation)
wait $WORKER_PID
