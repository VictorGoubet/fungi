# Stage 1: Base stage for installing dependencies
FROM python:3.10-slim as base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv (fast dependency manager)
RUN curl -Ls https://astral.sh/uv/install.sh | sh

# Copy dependency files first for better caching
COPY ../../pyproject.toml ./
# If you use a lockfile, uncomment the next line:
# COPY ../../uv.lock ./

# Install only the server dependencies
RUN uv pip install ".[server]"

# Stage 2: Final stage for setting up the application environment
FROM base as final

ARG UVICORN_HOST
ARG UVICORN_PORT

ENV UVICORN_HOST=${UVICORN_HOST}
ENV UVICORN_PORT=${UVICORN_PORT}

EXPOSE ${UVICORN_PORT}

# Copy the node model and the rest of the server directory
COPY ../../models/node.py ./node.py
COPY . .

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

CMD ["/entrypoint.sh"]
