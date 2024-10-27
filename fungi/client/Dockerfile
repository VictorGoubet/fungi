# Use Python 3.10 as the base image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Install Fungi
RUN pip install https://github.com/VictorGoubet/fungi/archive/refs/tags/v1.tar.gz

# Expose port 8080
EXPOSE 8080

# Set the command to run launch-fungi
CMD ["launch-fungi"]
