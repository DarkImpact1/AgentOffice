FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Copy all project files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Create data directory
RUN mkdir -p /app/data

# Expose port (Railway uses PORT env variable)
EXPOSE 8000

# Use shell form to allow environment variable substitution
CMD uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}
