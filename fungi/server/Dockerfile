# Use the official Python image from the Docker Hub
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the working directory contents into the container
COPY . .

# Command to run the uvicorn server
CMD ["uvicorn", "fungi.server.api:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
