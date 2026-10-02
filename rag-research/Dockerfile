FROM python:3.12-slim

WORKDIR /app

# Copy requirements first for Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only the source directories needed at runtime
COPY api/ ./api/
COPY src/ ./src/

EXPOSE 8000

# JSON array + sh -c so $PORT is expanded at runtime
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2"]