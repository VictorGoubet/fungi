# Get the script's directory and move to the parent directory of 'scripts'
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$parentDir = Split-Path -Parent $scriptDir

# Prompt the user for the image version tag
$IMAGE_VERSION = Read-Host "Please enter the image version tag"
$DOCKER_USERNAME = "victorgoubet"

# Tag the image with the version
docker tag fungi:latest $DOCKER_USERNAME/fungi:$IMAGE_VERSION

# Log in to Docker Hub
Write-Host "Logging into Docker Hub..."
docker login --username $DOCKER_USERNAME

# Push the image to Docker Hub
docker push $DOCKER_USERNAME/fungi:$IMAGE_VERSION

Write-Host "Deployment complete: $DOCKER_USERNAME/fungi:$IMAGE_VERSION"
