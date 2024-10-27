# Get the path of the current script
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition

# Build the relative path to the parent of the 'server' directory, which is two levels up from the script directory
$parentPath = Join-Path $scriptPath -ChildPath "..\..\.."

# Now create the absolute path to the Dockerfile inside the 'server' directory
$dockerfilePath = Join-Path $parentPath -ChildPath "server\Dockerfile"

# Resolve the Dockerfile path to its absolute canonical form
$resolvedDockerfilePath = Resolve-Path -Path $dockerfilePath

# Ensure the Docker build context is correctly set as the parent of the 'server' directory
$dockerBuildContext = $parentPath

# Load .env file and set each line as an environment variable
if (Test-Path $parentPath\server\.env) {
    Get-Content $parentPath\server\.env | ForEach-Object {
        $line = $_.Trim()
        if ($line -ne "" -and $line -notmatch "^#") {
            $key, $value = $line -split '=', 2
            [Environment]::SetEnvironmentVariable($key, $value, "Process")
        }
    }
}

# Build the Docker image using the variables from the .env file and the resolved Dockerfile path
docker build `
    --file $resolvedDockerfilePath `
    --build-arg REDIS_HOST=$env:REDIS_HOST `
    --build-arg REDIS_PORT=$env:REDIS_PORT `
    --build-arg UVICORN_HOST=$env:UVICORN_HOST `
    --build-arg UVICORN_PORT=$env:UVICORN_PORT `
    -t fungi_server:latest `
    $dockerBuildContext

Write-Host "Build complete: fungi_server:latest"
