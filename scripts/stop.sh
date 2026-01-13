#!/bin/bash

# Stop script for Japanese Anki Agent
# Stops both backend and frontend services

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PID_FILE="$PROJECT_ROOT/.pids"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Stopping Japanese Anki Agent...${NC}"

# Function to kill process and its children
kill_process_tree() {
    local pid=$1
    local name=$2

    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        echo -e "Stopping $name (PID: $pid)..."
        # Kill the process group
        kill -TERM -"$pid" 2>/dev/null || kill -TERM "$pid" 2>/dev/null

        # Wait a moment for graceful shutdown
        sleep 1

        # Force kill if still running
        if kill -0 "$pid" 2>/dev/null; then
            echo -e "${YELLOW}Force killing $name...${NC}"
            kill -9 -"$pid" 2>/dev/null || kill -9 "$pid" 2>/dev/null
        fi

        echo -e "${GREEN}$name stopped.${NC}"
    else
        echo -e "${YELLOW}$name not running (PID: $pid).${NC}"
    fi
}

# Check if PID file exists
if [ -f "$PID_FILE" ]; then
    # Read and kill each process
    while IFS=: read -r name pid; do
        kill_process_tree "$pid" "$name"
    done < "$PID_FILE"

    # Remove PID file
    rm -f "$PID_FILE"
    echo -e "${GREEN}PID file removed.${NC}"
else
    echo -e "${YELLOW}No PID file found. Trying to find processes by port...${NC}"

    # Try to find and kill by port
    # Backend on port 8000
    BACKEND_PID=$(lsof -ti:8000 2>/dev/null)
    if [ -n "$BACKEND_PID" ]; then
        echo -e "Found backend on port 8000 (PID: $BACKEND_PID)"
        kill -TERM "$BACKEND_PID" 2>/dev/null
        echo -e "${GREEN}Backend stopped.${NC}"
    fi

    # Frontend on port 3000
    FRONTEND_PID=$(lsof -ti:3000 2>/dev/null)
    if [ -n "$FRONTEND_PID" ]; then
        echo -e "Found frontend on port 3000 (PID: $FRONTEND_PID)"
        kill -TERM "$FRONTEND_PID" 2>/dev/null
        echo -e "${GREEN}Frontend stopped.${NC}"
    fi
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Japanese Anki Agent stopped.${NC}"
echo -e "${GREEN}========================================${NC}"
