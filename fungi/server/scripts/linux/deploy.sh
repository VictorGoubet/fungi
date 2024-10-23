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

# Check if DOCKER_USERNAME is set
if [ -z "$DOCKER_USERNAME" ]; then
    echo "Error: DOCKER_USERNAME is not set in the .env file"
    exit 1
fi

# Tag the image with the version
docker tag fungi:latest $DOCKER_USERNAME/fungi:$IMAGE_VERSION

# Log in to Docker Hub
echo "Logging into Docker Hub..."
docker login --username $DOCKER_USERNAME

# Push the image to Docker Hub
docker push $DOCKER_USERNAME/fungi:$IMAGE_VERSION

echo "Deployment complete: $DOCKER_USERNAME/fungi:$IMAGE_VERSION"
