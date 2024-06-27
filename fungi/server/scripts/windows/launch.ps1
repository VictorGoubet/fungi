# Get the path of the current script
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition

# Calculate the parent directory of 'scripts', which is up two levels
$serverPath = Join-Path $scriptPath -ChildPath "..\.."

# Resolve the absolute path to ensure it is correct
$serverPath = Resolve-Path -Path $serverPath

# Construct the path to the .env file
$envPath = Join-Path -Path $serverPath -ChildPath ".env"

# Check if the .env file exists
if (-Not (Test-Path -Path $envPath)) {
    Write-Host "Missing .env file, cannot set environment variables."
    exit
}

# Load the UVICORN_PORT from the .env file
$UVICORN_PORT = (Get-Content -Path $envPath | Where-Object { $_ -match "^UVICORN_PORT=" }) -replace '.*=', ''

# Check if UVICORN_PORT was successfully loaded
if (-Not $UVICORN_PORT) {
    Write-Host "UVICORN_PORT not found in .env file."
    exit
}

# Run the Docker container
docker run -p ${UVICORN_PORT}:${UVICORN_PORT} fungi:latest
