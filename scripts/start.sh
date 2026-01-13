#!/bin/bash

# Start script for Japanese Anki Agent
# Starts both backend and frontend services

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PID_FILE="$PROJECT_ROOT/.pids"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Japanese Anki Agent...${NC}"

# Check if already running
if [ -f "$PID_FILE" ]; then
    echo -e "${YELLOW}Warning: PID file exists. Services might already be running.${NC}"
    echo -e "${YELLOW}Run ./scripts/stop.sh first or delete .pids file if stale.${NC}"
    exit 1
fi

# Create PID file
touch "$PID_FILE"

# Start Backend
echo -e "${GREEN}Starting backend server...${NC}"
cd "$PROJECT_ROOT/backend"

# Check if venv exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating Python virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate venv and install dependencies
source venv/bin/activate
pip install -q -r requirements.txt || {
    echo -e "${YELLOW}pip install failed, retrying with --trusted-host flags...${NC}"
    pip install -q --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
}

# Start uvicorn in background
uvicorn app.main:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!
echo "backend:$BACKEND_PID" >> "$PID_FILE"
echo -e "${GREEN}Backend started (PID: $BACKEND_PID) at http://localhost:8000${NC}"

# Start Frontend
echo -e "${GREEN}Starting frontend server...${NC}"
cd "$PROJECT_ROOT/frontend"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing npm dependencies...${NC}"
    npm install
fi

# Start Next.js in background
npm run dev &
FRONTEND_PID=$!
echo "frontend:$FRONTEND_PID" >> "$PID_FILE"
echo -e "${GREEN}Frontend started (PID: $FRONTEND_PID) at http://localhost:3000${NC}"

# Return to project root
cd "$PROJECT_ROOT"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Japanese Anki Agent is running!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "Backend:  ${YELLOW}http://localhost:8000${NC}"
echo -e "Frontend: ${YELLOW}http://localhost:3000${NC}"
echo -e "API Docs: ${YELLOW}http://localhost:8000/docs${NC}"
echo ""
echo -e "To stop: ${YELLOW}./scripts/stop.sh${NC}"
echo ""

# Wait for both processes
wait
