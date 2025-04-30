#!/bin/bash
set -e

# Activate virtual environment if needed (uv handles this, but for robustness)
# source /app/.venv/bin/activate || true
 
# Run the client UI app
exec python -m fungi.client.app 