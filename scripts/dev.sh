#!/bin/bash

# Development script for Japanese Anki Agent
# Starts services in foreground with log output interleaved

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Cleanup function
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down...${NC}"

    # Kill all background jobs
    jobs -p | xargs -r kill 2>/dev/null

    # Kill by port as backup
    lsof -ti:8000 2>/dev/null | xargs -r kill 2>/dev/null
    lsof -ti:3000 2>/dev/null | xargs -r kill 2>/dev/null

    echo -e "${GREEN}Stopped.${NC}"
    exit 0
}

# Set up trap for cleanup on Ctrl+C
trap cleanup SIGINT SIGTERM

echo -e "${GREEN}Starting Japanese Anki Agent (Development Mode)...${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop both services${NC}"
echo ""

# Start Backend
echo -e "${BLUE}[Backend]${NC} Setting up..."
cd "$PROJECT_ROOT/backend"

# Check if venv exists
if [ ! -d "venv" ]; then
    echo -e "${BLUE}[Backend]${NC} Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate venv and install dependencies
source venv/bin/activate
pip install -q -r requirements.txt || {
    echo -e "${BLUE}[Backend]${NC} pip install failed, retrying with --trusted-host flags..."
    pip install -q --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
}

# Start uvicorn with reload in background
echo -e "${BLUE}[Backend]${NC} Starting on http://localhost:8000"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload 2>&1 | sed "s/^/[Backend] /" &

# Start Frontend
echo -e "${GREEN}[Frontend]${NC} Setting up..."
cd "$PROJECT_ROOT/frontend"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${GREEN}[Frontend]${NC} Installing npm dependencies..."
    npm install
fi

# Start Next.js dev server in background
echo -e "${GREEN}[Frontend]${NC} Starting on http://localhost:3000"
npm run dev 2>&1 | sed "s/^/[Frontend] /" &

# Return to project root
cd "$PROJECT_ROOT"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Development servers starting...${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "Backend:  ${YELLOW}http://localhost:8000${NC}"
echo -e "Frontend: ${YELLOW}http://localhost:3000${NC}"
echo -e "API Docs: ${YELLOW}http://localhost:8000/docs${NC}"
echo ""

# Wait for all background jobs
wait
