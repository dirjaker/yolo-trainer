#!/usr/bin/env bash
# YOLO Trainer - Environment Setup Script
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "=== YOLO Trainer Setup ==="
echo "Project root: $PROJECT_ROOT"

# ---- Create directories ----
echo "Creating project directories..."
mkdir -p "$PROJECT_ROOT"/{uploads,models,runs,logs,datasets}
mkdir -p "$PROJECT_ROOT"/uploads/{images,weights}
mkdir -p "$PROJECT_ROOT"/models/{exported,checkpoints}

# ---- Python virtual environments ----
echo "Setting up backend Python environment..."
if [ ! -d "$PROJECT_ROOT/backend/venv" ]; then
    python3 -m venv "$PROJECT_ROOT/backend/venv"
fi
source "$PROJECT_ROOT/backend/venv/bin/activate"
pip install --upgrade pip
pip install -r "$PROJECT_ROOT/backend/requirements.txt"
deactivate

echo "Setting up worker Python environment..."
if [ ! -d "$PROJECT_ROOT/worker/venv" ]; then
    python3 -m venv "$PROJECT_ROOT/worker/venv"
fi
source "$PROJECT_ROOT/worker/venv/bin/activate"
pip install --upgrade pip
pip install -r "$PROJECT_ROOT/worker/requirements.txt"
deactivate

# ---- Frontend ----
echo "Installing frontend dependencies..."
cd "$PROJECT_ROOT/frontend"
if command -v npm &>/dev/null; then
    npm install
elif command -v pnpm &>/dev/null; then
    pnpm install
else
    echo "WARNING: npm/pnpm not found, skipping frontend install"
fi

# ---- Environment file ----
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo "Creating default .env file..."
    cat > "$PROJECT_ROOT/.env" <<'EOF'
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/yolo_trainer

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# MinIO / S3
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=yolo-trainer
MINIO_SECURE=false

# Auth
SECRET_KEY=change-me-in-production-use-openssl-rand-hex-32
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# App
APP_NAME=YOLO Trainer
APP_PORT=10003
DEBUG=true
EOF
    echo "Created .env - please review and update secrets!"
else
    echo ".env already exists, skipping"
fi

# ---- Alembic init (if needed) ----
if [ ! -d "$PROJECT_ROOT/backend/alembic" ]; then
    echo "Initializing Alembic migrations..."
    cd "$PROJECT_ROOT/backend"
    source venv/bin/activate
    alembic init alembic 2>/dev/null || true
    deactivate
fi

echo ""
echo "=== Setup complete ==="
echo ""
echo "Next steps:"
echo "  1. Start PostgreSQL, Redis, and MinIO services"
echo "  2. Review and update .env with your credentials"
echo "  3. Run migrations:  cd backend && source venv/bin/activate && alembic upgrade head"
echo "  4. Start backend:   cd backend && uvicorn app.main:app --reload --port 10003"
echo "  5. Start worker:    cd worker && source venv/bin/activate && celery -A tasks worker --loglevel=info"
echo "  6. Start frontend:  cd frontend && npm run dev"
