# Use official Python runtime as base image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY src/ /app/src/
COPY frontend/ /app/frontend/
COPY weights/ /app/weights/
COPY .env /app/.env

# Create data directories
RUN mkdir -p /app/data/temp /app/data/raw

# Expose ports for both backend and frontend
EXPOSE 8000
EXPOSE 8501

# Default command (overridden by docker-compose)
CMD ["uvicorn", "src.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
