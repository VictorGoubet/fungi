# Stage 1: Base stage for installing dependencies
FROM python:3.10-slim as base

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    redis-server \
    && rm -rf /var/lib/apt/lists/*

# Copy only the requirements file to leverage Docker cache
COPY server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Final stage for setting up the application environment
FROM base as final

# Define build arguments
ARG REDIS_HOST
ARG REDIS_PORT
ARG UVICORN_HOST
ARG UVICORN_PORT

# Set environment variables from the build arguments
ENV REDIS_HOST=${REDIS_HOST} \
    REDIS_PORT=${REDIS_PORT} \
    UVICORN_HOST=${UVICORN_HOST} \
    UVICORN_PORT=${UVICORN_PORT}

# Expose the port specified by UVICORN_PORT
EXPOSE ${UVICORN_PORT}

# Copy the node module and the rest of the server directory
COPY models/node.py ./models/node.py
COPY server/ .

# Copy the entrypoint script and ensure it is executable
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Command to run the application
CMD ["/entrypoint.sh"]
