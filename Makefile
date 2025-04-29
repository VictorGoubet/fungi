# Makefile for Fungi P2P Project

# Load environment variables from .env if it exists
ifneq (,$(wildcard .env))
	include .env
	export
endif

# Docker image name
SERVER_IMAGE ?= fungi_server
SERVER_DOCKERFILE = fungi/server/Dockerfile
SERVER_REQUIREMENTS = fungi/server/requirements.txt

# Client Docker image name
CLIENT_IMAGE ?= fungi_client
CLIENT_DOCKERFILE = fungi/client/Dockerfile

# Default Docker username and image version
DOCKER_USERNAME ?= victorgoubet
IMAGE_VERSION ?= latest

# Build the server Docker image
build-server:
	docker build -f $(SERVER_DOCKERFILE) -t $(SERVER_IMAGE):latest .

# Push the server image to Docker Hub
push-server:
	docker tag $(SERVER_IMAGE):latest $(DOCKER_USERNAME)/$(SERVER_IMAGE):$(IMAGE_VERSION)
	docker push $(DOCKER_USERNAME)/$(SERVER_IMAGE):$(IMAGE_VERSION)

# Run the server image from Docker Hub
run-server:
	docker run -p $${UVICORN_PORT:-8000}:$${UVICORN_PORT:-8000} --env-file .env $(DOCKER_USERNAME)/$(SERVER_IMAGE):$(IMAGE_VERSION)

# Run the server in development mode (local code, auto-reload)
dev-server:
	uv run uvicorn fungi.server.api:app --host $${UVICORN_HOST:-0.0.0.0} --port $${UVICORN_PORT:-8000} --reload --env-file .env

# Set up the Python environment and install all dependencies using uv
setup:
	uv venv .venv
	uv sync --all-groups --extra client --extra server
	@if [ ! -f .env ]; then cp .env_example .env; fi

# Clean the environment: remove .venv and .env if they exist
clean:
	rm -rf .venv venv uv.lock
	@if [ -f .env ]; then rm .env; fi

# Format and lint all files using ruff
format:
	uv run ruff format .
	uv run ruff check . --fix

# Build the client Docker image
build-client:
	docker build -f $(CLIENT_DOCKERFILE) -t $(CLIENT_IMAGE):latest .

# Push the client image to Docker Hub
push-client:
	docker tag $(CLIENT_IMAGE):latest $(DOCKER_USERNAME)/$(CLIENT_IMAGE):$(IMAGE_VERSION)
	docker push $(DOCKER_USERNAME)/$(CLIENT_IMAGE):$(IMAGE_VERSION)

# Run the client image from Docker Hub
run-client:
	docker run -p $${GRADIO_PORT:-8080}:$${GRADIO_PORT:-8080} --env-file .env $(DOCKER_USERNAME)/$(CLIENT_IMAGE):$(IMAGE_VERSION)

# Run the client in development mode (local code, auto-reload)
dev-client:
	uv run python -m fungi.client.app --env-file .env

# Show this help message
help:
	@echo "\n💡 Available make commands:\n"; \
	awk '/^[a-zA-Z0-9_\-]+:/ { \
		header = match(prev, /^#/) ? substr(prev, 3) : ""; \
		printf "  \033[1;32m%-20s\033[0m %s\n", substr($$1, 1, length($$1)-1), header; \
	} { prev = $$0 }' $(MAKEFILE_LIST); \
	echo "\nUse \"make <target>\" to run a command." 