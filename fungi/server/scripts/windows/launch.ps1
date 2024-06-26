# Navigate to the script's directory and move to the parent directory of 'scripts'
cd $(Split-Path -Parent $MyInvocation.MyCommand.Definition)
cd ../..

# Load environment variables from .env file and extract UVICORN_PORT
$UVICORN_PORT = (Get-Content .env | Where-Object { $_ -match "^UVICORN_PORT=" }) -replace '.*=', ''

# Run the Docker container
docker run -p ${UVICORN_PORT}:${UVICORN_PORT} fungi:latest
