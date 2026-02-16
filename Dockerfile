# Stage 1: Build Frontend
FROM node:20 as frontend-build

WORKDIR /app/frontend

COPY frontend/package.json .
COPY frontend/package-lock.json .

RUN npm ci

COPY frontend/ .
RUN npm run build

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy built frontend assets to FastAPI static directory
# main.py serves static files from /app/app/static
COPY --from=frontend-build /app/frontend/dist /app/app/static

# Create export directory
RUN mkdir -p /app/exports

EXPOSE 8000

# Start script: Run migrations -> Seed DB -> Start App
CMD ["sh", "-c", "alembic upgrade head && python scripts/seed.py && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
