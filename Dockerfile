# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime (much smaller)
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copy only the installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy the application code
COPY src/ ./src/

# Copy the ChromaDB data
COPY data/chroma_db/ ./data/chroma_db/

# Set Python path
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Run the FastAPI server
CMD ["uvicorn", "src.server.bridge:app", "--host", "0.0.0.0", "--port", "8000"]
