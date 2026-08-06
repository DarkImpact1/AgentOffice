FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Copy all project files first
COPY . .

# Install Python dependencies (not editable for production)
RUN pip install --no-cache-dir .

# Install Playwright browsers
RUN playwright install chromium || true

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
