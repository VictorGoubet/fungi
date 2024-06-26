#!/bin/bash

# Navigate to the script's directory
cd "$(dirname "$0")"
# Move to the parent directory of 'scripts', which should be 'server'
cd ../..

# Load .env file and export each line as an environment variable
if [ -f .env ]; then
    export $(cat .env | sed 's/#.*//g' | xargs)
fi

# Build the Docker image using the variables from the .env file
docker build \
    --file server/Dockerfile \
    --build-arg REDIS_HOST=$REDIS_HOST \
    --build-arg REDIS_PORT=$REDIS_PORT \
    --build-arg UVICORN_HOST=$UVICORN_HOST \
    --build-arg UVICORN_PORT=$UVICORN_PORT \
    -t fungi:latest .

echo "Build complete: fungi:latest"
