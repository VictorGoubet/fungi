#!/bin/bash

# Navigate to the script's directory and move to the parent directory of 'scripts'
cd "$(dirname "$0")"
cd ../..

# Check if .env file exists and load it
if [ ! -f .env ]; then
    echo "Missing .env file, cannot set environment variables."
    exit 1
fi

# Extract UVICORN_PORT from .env to use in port mapping
UVICORN_PORT=$(grep UVICORN_PORT .env | cut -d '=' -f2)

# Run the Docker container
docker run -p ${UVICORN_PORT}:${UVICORN_PORT} fungi:latest
