#!/bin/bash

# Navigate to the script's directory and move to the parent directory of 'scripts'
cd "$(dirname "$0")"
cd ../..

IMAGE_VERSION="v1"
DOCKER_USERNAME="victorgoubet"

# Tag the image with the version
docker tag fungi:latest ${DOCKER_USERNAME}/fungi:${IMAGE_VERSION}

# Log in to Docker Hub
echo "Logging into Docker Hub..."
docker login --username ${DOCKER_USERNAME}

# Push the image to Docker Hub
docker push ${DOCKER_USERNAME}/fungi:${IMAGE_VERSION}

echo "Deployment complete: ${DOCKER_USERNAME}/fungi:${IMAGE_VERSION}"
