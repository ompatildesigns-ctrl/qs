#!/bin/bash
# Startup script for Quantum Sprout backend

# Set default port if not provided
PORT=${PORT:-8001}

# Start uvicorn server
exec uvicorn server:app --host 0.0.0.0 --port $PORT

