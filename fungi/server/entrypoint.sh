#!/bin/bash
# Start Redis server in the background
redis-server --daemonize yes

# Start the FastAPI application
uvicorn api:app --host $UVICORN_HOST --port $UVICORN_PORT --reload
