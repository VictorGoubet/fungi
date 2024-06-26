# Navigate to the script's directory and move to the parent directory of 'scripts'
cd $(Split-Path -Parent $MyInvocation.MyCommand.Definition)
cd ../..

$IMAGE_VERSION = "v1"
$DOCKER_USERNAME = "victorgoubet"

# Tag the image with the version
docker tag fungi:latest $DOCKER_USERNAME/fungi:$IMAGE_VERSION

# Log in to Docker Hub
Write-Host "Logging into Docker Hub..."
docker login --username $DOCKER_USERNAME

# Push the image to Docker Hub
docker push $DOCKER_USERNAME/fungi:$IMAGE_VERSION

Write-Host "Deployment complete: $DOCKER_USERNAME/fungi:$IMAGE_VERSION"
