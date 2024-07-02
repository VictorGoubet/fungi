#!/bin/bash

# Get the path of the current script
scriptPath="$(dirname "$(realpath "$0")")"

# Calculate the parent directory of 'scripts', which is up two levels
serverPath="$(realpath "$scriptPath/../..")"

# Construct the path to the .env file
envPath="$serverPath/.env"

# Check if the .env file exists
if [ ! -f "$envPath" ]; then
    echo "Missing .env file, cannot set environment variables."
    exit 1
fi

# Load the UVICORN_PORT from the .env file
UVICORN_PORT=$(grep -E "^UVICORN_PORT=" "$envPath" | cut -d '=' -f2)

# Check if UVICORN_PORT was successfully loaded
if [ -z "$UVICORN_PORT" ]; then
    echo "UVICORN_PORT not found in .env file."
    exit 1
fi

# Run the Docker container
docker run -p "${UVICORN_PORT}:${UVICORN_PORT}" fungi:latest
