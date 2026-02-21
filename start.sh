#!/bin/bash

# News Agent Digest - Quick Start Script
# Usage: ./start.sh

set -e

echo "🚀 Starting News Agent Digest..."
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "❌ Error: Must run from project root directory"
    exit 1
fi

# Function to cleanup processes on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down..."
    kill $(jobs -p) 2>/dev/null || true
    exit 0
}
trap cleanup INT TERM

# Start Backend
echo -e "${BLUE}▶ Starting Backend (FastAPI)...${NC}"
cd backend
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}  Creating virtual environment...${NC}"
    python -m venv .venv
fi
source .venv/bin/activate
pip install -q -r requirements-dev.txt
python -c "import app" 2>/dev/null || {
    echo -e "${YELLOW}  Installing dependencies...${NC}"
    pip install -q -r requirements-dev.txt
}
cd ..

# Start backend in background
(cd backend && source .venv/bin/activate && uvicorn app.main:app --port 8000 --log-level warning) &
BACKEND_PID=$!
echo -e "${GREEN}  ✓ Backend started (PID: $BACKEND_PID)${NC}"

# Wait for backend to be ready
echo -e "${BLUE}  Waiting for backend...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}  ✓ Backend ready${NC}"
        break
    fi
    sleep 0.5
done

# Start Frontend
echo ""
echo -e "${BLUE}▶ Starting Frontend (React + Vite)...${NC}"
cd frontend
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}  Installing npm dependencies...${NC}"
    npm install
fi
cd ..

# Start frontend in background
(cd frontend && npm run dev -- --port 5173) &
FRONTEND_PID=$!
echo -e "${GREEN}  ✓ Frontend started (PID: $FRONTEND_PID)${NC}"

# Wait for frontend
echo -e "${BLUE}  Waiting for frontend...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:5173 > /dev/null 2>&1; then
        echo -e "${GREEN}  ✓ Frontend ready${NC}"
        break
    fi
    sleep 0.5
done

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  🎉 News Agent Digest is running!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "  ${BLUE}📱 Web App:${NC}    http://localhost:5173"
echo -e "  ${BLUE}🔌 API:${NC}        http://localhost:8000"
echo -e "  ${BLUE}📚 API Docs:${NC}   http://localhost:8000/docs"
echo ""
echo -e "  ${YELLOW}Press Ctrl+C to stop${NC}"
echo ""

# Keep script running
wait
