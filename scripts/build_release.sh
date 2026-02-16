#!/bin/bash
set -e

# Configuration
IMAGE_NAME="prismid-app"
OUTPUT_DIR="release_output"
ARCHIVE_NAME="prismid_images.tar"

echo "============================================="
echo "  PRISMID Release Builder (Offline Docker)   "
echo "============================================="

# 1. Clean previous build
# Doing this BEFORE build to ensure context is clean
if [ -d "$OUTPUT_DIR" ]; then
    echo "Cleaning previous build..."
    rm -rf "$OUTPUT_DIR"
fi
mkdir -p "$OUTPUT_DIR"

# 2. Build Application Image
echo "Step 1/4: Building Application Image..."
# Use legacy builder if buildx is missing
# export DOCKER_BUILDKIT=1
docker build -t $IMAGE_NAME:latest .

# 3. Pull Dependencies
echo "Step 2/4: Pulling Service Dependencies..."
docker pull postgres:15-alpine
docker pull redis:7-alpine

# 4. Save Images to Archive
echo "Step 3/4: Saving Docker Images to $ARCHIVE_NAME..."
echo "        (This may take a few minutes depending on size)"
docker save $IMAGE_NAME:latest postgres:15-alpine redis:7-alpine -o "$OUTPUT_DIR/$ARCHIVE_NAME"

# 5. Prepare Output Directory
echo "Step 4/4: Finalizing Release Package..."
cp docker-compose.prod.yml "$OUTPUT_DIR/"

# Create credentials directory in output
mkdir -p "$OUTPUT_DIR/credentials"
# If you have default credentials (e.g. dummy service account) you want to ship:
# cp -r credentials/* "$OUTPUT_DIR/credentials/" 2>/dev/null || true
# For now, just ensuring the directory exists so the volume mount doesn't fail.

# Copy .env.example if it exists, otherwise create a minimal one
if [ -f ".env.example" ]; then
    cp .env.example "$OUTPUT_DIR/"
    # Force production values in the output file
    sed -i 's|DATABASE_URL=.*|DATABASE_URL=postgresql://prismid:prismid_secret@postgres:5432/prismid_db|g' "$OUTPUT_DIR/.env.example"
    sed -i 's|REDIS_URL=.*|REDIS_URL=redis://redis:6379/0|g' "$OUTPUT_DIR/.env.example"
    # Append APP_PORT if not present
    if ! grep -q "APP_PORT" "$OUTPUT_DIR/.env.example"; then
        echo "APP_PORT=8000" >> "$OUTPUT_DIR/.env.example"
    fi
else
    echo "Creating default .env.example..."
    cat <<EOT >> "$OUTPUT_DIR/.env.example"
POSTGRES_USER=prismid
POSTGRES_PASSWORD=prismid_secret
POSTGRES_DB=prismid_db
SECRET_KEY=change_this_generated_secret_key
APP_PORT=8000
# Docker Networking: Connect to service names, not localhost
DATABASE_URL=postgresql://prismid:prismid_secret@postgres:5432/prismid_db
REDIS_URL=redis://redis:6379/0
EOT
fi

# Create Windows Start Script
cat <<EOF > "$OUTPUT_DIR/start_app.bat"
@echo off
setlocal
TITLE PRISMID Launcher

echo ====================================================
echo      PRISMID - Identity Governance System
echo ====================================================

REM Check Docker
docker info >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Docker is NOT running.
    echo Please start Docker Desktop and try again.
    echo.
    pause
    exit /b 1
)

REM Load Images if archive exists
if exist $ARCHIVE_NAME (
    echo [INFO] Loading Docker images from archive...
    echo        This might take a minute...
    docker load -i $ARCHIVE_NAME
    IF %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to load images.
        pause
        exit /b 1
    )
    echo [OK] Images loaded.
)

REM Setup .env
if not exist .env (
    if exist .env.example (
        echo [INFO] Creating .env configuration...
        copy .env.example .env >nul
    )
)

REM Start Services
echo [INFO] Starting services...
docker-compose -f docker-compose.prod.yml up -d
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to start services.
    pause
    exit /b 1
)

echo.
echo ====================================================
echo [SUCCESS] Application is running!
echo Access it at: http://localhost
echo ====================================================
echo.
pause
EOF

echo "============================================="
echo "✅ Build Complete!"
echo "Release package available in: $OUTPUT_DIR/"
echo "-> Transfer this folder to your Windows machine."
echo "============================================="
