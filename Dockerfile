# Use a slim Python image
FROM python:3.11-slim

# Prevent .pyc files and enable unbuffered logs (important for Cloud Run)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first (layer-cached unless requirements.txt changes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Cloud Run injects PORT at runtime; default to 8080 for local Docker testing
ENV PORT=8080

# Start the server — bind to $PORT, single worker suitable for Cloud Run
CMD uvicorn app:app --host 0.0.0.0 --port $PORT --workers 1
