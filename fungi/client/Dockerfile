# Use Python 3.10 as the base image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

COPY . .
COPY ../../pyproject.toml ./

RUN pip install uv && \
    uv pip install --system --extra client && \
    uv pip install --system .

# Expose port 8080
EXPOSE 8080

ENTRYPOINT ["/app/entrypoint.sh"]
