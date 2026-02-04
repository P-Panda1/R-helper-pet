# Dockerfile for Qdrant (optional - for containerized deployment)
# Note: Qdrant should be run separately, this is just for reference

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p models cache logs

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run application
CMD ["python", "main.py"]

