#!/bin/bash

# Get the path of the current script
scriptPath=$(dirname "$0")

# Build the relative path to the parent of the 'server' directory, which is two levels up from the script directory
parentPath=$(realpath "$scriptPath/../../..")

# Now create the absolute path to the Dockerfile inside the 'server' directory
dockerfilePath="$parentPath/server/Dockerfile"

# Write the path to check
echo "The Dockerfile path is: $dockerfilePath"

# Ensure the Docker build context is correctly set as the parent of the 'server' directory
dockerBuildContext="$parentPath"

# Load .env file and set each line as an environment variable
if [ -f "$parentPath/.env" ]; then
    while IFS='=' read -r key value
    do
        if [[ ! $key =~ ^#.* ]] && [ -n "$key" ]; then
            export "$key=$value"
        fi
    done < "$parentPath/.env"
fi

# Build the Docker image using the variables from the .env file and the resolved Dockerfile path
docker build \
    --file "$dockerfilePath" \
    --build-arg REDIS_HOST="$REDIS_HOST" \
    --build-arg REDIS_PORT="$REDIS_PORT" \
    --build-arg UVICORN_HOST="$UVICORN_HOST" \
    --build-arg UVICORN_PORT="$UVICORN_PORT" \
    -t fungi:latest \
    "$dockerBuildContext"

echo "Build complete: fungi:latest"
