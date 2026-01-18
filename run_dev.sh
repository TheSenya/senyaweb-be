#!/bin/bash
# Run the Backend Natively (No Docker)
# -----------------------------------------------------------------------------
# This script is for running the backend directly on your machine.
# Useful for faster debugging or if you don't want to use Docker.

# 0. Load Environment Variables
# We use 'set -o allexport' to automatically export all variables defined in the files
set -o allexport

# Load Production Base (if exists)
if [ -f .env ]; then
    echo "Loading .env..."
    source .env
fi

# Load Local Overrides (if exists)
if [ -f .env.local ]; then
    echo "Loading .env.local overrides..."
    source .env.local
fi

set +o allexport

echo "---------------------------------------------------"
echo "Starting Backend Natively..."
echo "Environment: $ENV"
echo "CORS Origins: $CORS_ORIGINS"
echo "---------------------------------------------------"

# 2. Activate Virtual Environment (if it exists)
if [ -d ".venv" ]; then
    echo "Activating virtual environment (.venv)..."
    source .venv/bin/activate
else
    echo "Warning: No .venv found. Running with system python."
    echo "If this fails, create a venv: 'python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt'"
fi

# 3. Run Uvicorn
# --reload: Auto-restart on code changes
# --host 0.0.0.0: Listen on all interfaces (optional locally, but good for testing)
# --port 8000: Default port
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
