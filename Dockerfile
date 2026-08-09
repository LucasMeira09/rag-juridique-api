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

# Pre-download the FastEmbed model into build cache
ENV FASTEMBED_CACHE_PATH=/build/fastembed_cache
RUN python -c "from fastembed import TextEmbedding; TextEmbedding(model_name='sentence-transformers/all-MiniLM-L6-v2', threads=1, providers=['CPUExecutionProvider'])"

# Stage 2: Runtime (much smaller)
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FASTEMBED_CACHE_PATH=/app/fastembed_cache

WORKDIR /app

# Copy only the installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /build/fastembed_cache /app/fastembed_cache

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

