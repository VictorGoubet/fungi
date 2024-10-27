#!/bin/bash

# Get the script's directory and move to the parent directory of 'scripts'
scriptDir="$(dirname "$(realpath "$0")")"
parentDir="$(realpath "$scriptDir/../..")"

# Load environment variables from .env file
if [ -f "$parentDir/.env" ]; then
    export $(grep -v '^#' "$parentDir/.env" | xargs)
else
    echo "Error: .env file not found"
    exit 1
fi

# Prompt the user for the image version tag
read -p "Please enter the image version tag: " IMAGE_VERSION

# Check if DOCKER_USERNAME and DOCKER_PASSWORD are set
if [ -z "$DOCKER_USERNAME" ] || [ -z "$DOCKER_PASSWORD" ]; then
    echo "Error: DOCKER_USERNAME or DOCKER_PASSWORD is not set in the .env file"
    exit 1
fi

# Tag the image with the version
docker tag fungi_server:latest $DOCKER_USERNAME/fungi_server:$IMAGE_VERSION

# Log in to Docker Hub
echo "Logging into Docker Hub..."
echo "$DOCKER_PASSWORD" | docker login --username $DOCKER_USERNAME --password-stdin

# Push the image to Docker Hub
docker push $DOCKER_USERNAME/fungi_server:$IMAGE_VERSION

echo "Deployment complete: $DOCKER_USERNAME/fungi_server:$IMAGE_VERSION"
