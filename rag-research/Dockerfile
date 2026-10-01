FROM python:3.12-slim

WORKDIR /app

# Copy requirements first for Docker layer caching — only reinstalls deps when requirements.txt changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code separately so code changes don't bust the pip cache
COPY api/ ./api/
COPY src/ ./src/

EXPOSE 8000

# Use shell form so $PORT is expanded at runtime (Railway/Render/Cloud Run inject PORT automatically)
CMD uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2