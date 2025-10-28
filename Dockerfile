# Multi-stage Docker build for JCW Cost Estimator

# Backend Stage
FROM python:3.11-slim as backend

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run FastAPI server on Cloud Run's PORT
CMD ["sh", "-c", "uvicorn web.backend.app_comprehensive:app --host 0.0.0.0 --port ${PORT:-8000}"]
