# Get the script's directory and move to the parent directory of 'scripts'
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$parentDir = Split-Path -Parent (Split-Path -Parent $scriptDir)

# Load environment variables from .env file
if (Test-Path "$parentDir\.env") {
    Get-Content "$parentDir\.env" | ForEach-Object {
        if ($_ -match '^(.+)=(.+)$') {
            $key = $matches[1]
            $value = $matches[2]
            Set-Item -Path "Env:$key" -Value $value
        }
    }
} else {
    Write-Host "Error: .env file not found"
    exit 1
}

# Prompt the user for the image version tag
$IMAGE_VERSION = Read-Host "Please enter the image version tag"

# Check if DOCKER_USERNAME is set
if (-not $env:DOCKER_USERNAME) {
    Write-Host "Error: DOCKER_USERNAME is not set in the .env file"
    exit 1
}

# Tag the image with the version
docker tag fungi_server:latest $env:DOCKER_USERNAME/fungi_server:$IMAGE_VERSION

# Log in to Docker Hub
Write-Host "Logging into Docker Hub..."
docker login --username $env:DOCKER_USERNAME

# Push the image to Docker Hub
docker push $env:DOCKER_USERNAME/fungi_server:$IMAGE_VERSION

Write-Host "Deployment complete: $env:DOCKER_USERNAME/fungi_server:$IMAGE_VERSION"
