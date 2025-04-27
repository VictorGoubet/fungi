#!/bin/bash

# Start the FastAPI application
uvicorn api:app --host $UVICORN_HOST --port $UVICORN_PORT --reload
