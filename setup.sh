#!/bin/bash
# AI Observability Platform - Local Setup (No Docker)
set -e

echo "=== AI Observability Platform Setup ==="
echo ""

# 1. Copy env file
if [ ! -f .env ]; then
    cp .env.example .env
    echo "[OK] Created .env file"
fi

# 2. Check PostgreSQL
if command -v psql &> /dev/null; then
    echo "[OK] PostgreSQL CLI found"
else
    echo "[!] psql not found. Install PostgreSQL first:"
    echo "    macOS:  brew install postgresql@16 && brew services start postgresql@16"
    echo "    Linux:  sudo apt install postgresql"
    exit 1
fi

# 3. Create database and user
echo ""
echo "Setting up PostgreSQL database..."
psql postgres -c "CREATE USER aiobserve WITH PASSWORD 'aiobserve';" 2>/dev/null || echo "  User 'aiobserve' already exists"
psql postgres -c "CREATE DATABASE aiobserve OWNER aiobserve;" 2>/dev/null || echo "  Database 'aiobserve' already exists"
psql postgres -c "GRANT ALL PRIVILEGES ON DATABASE aiobserve TO aiobserve;" 2>/dev/null
echo "[OK] PostgreSQL database ready"

# 4. Setup backend Python environment
echo ""
echo "Setting up backend..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt -q
cd ..
echo "[OK] Backend dependencies installed"

# 5. Setup dashboard
echo ""
echo "Setting up dashboard..."
cd dashboard
npm install --silent 2>/dev/null || npm install
cd ..
echo "[OK] Dashboard dependencies installed"

echo ""
echo "=== Setup Complete ==="
echo ""
echo "To run the platform, open TWO terminals:"
echo ""
echo "  Terminal 1 (Backend API + background workers):"
echo "    cd backend"
echo "    source venv/bin/activate"
echo "    uvicorn app.main:app --reload --port 8000"
echo ""
echo "  Terminal 2 (Dashboard):"
echo "    cd dashboard"
echo "    npm run dev"
echo ""
echo "Then open: http://localhost:5173"
echo ""
echo "Quick start:"
echo "  1. Go to Settings page"
echo "  2. Create a project"
echo "  3. Generate an API key"
echo "  4. Set the API key in the dashboard"
echo "  5. Generate sample data:"
echo "     cd sample_app && pip install httpx && python generate_traffic.py"
