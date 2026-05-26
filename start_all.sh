#!/bin/bash

# Pathneo Services Startup Script

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=======================================${NC}"
echo -e "${BLUE}      Starting Pathneo Backend Services${NC}"
echo -e "${BLUE}=======================================${NC}"

# Check virtual environment
if [ ! -d ".venv" ]; then
    echo -e "${RED}Error: .venv directory not found. Please run this script from the project root.${NC}"
    exit 1
fi

PYTHON_BIN="./.venv/bin/python"

# Function to start a service
start_service() {
    local name=$1
    local port=$2
    local dir="services/$name"
    
    echo -e "${YELLOW}Starting $name on port $port...${NC}"
    
    if [ ! -d "$dir" ]; then
        echo -e "${RED}Error: Directory $dir does not exist.${NC}"
        return 1
    fi
    
    # Run uvicorn in background
    cd "$dir"
    ../../$PYTHON_BIN -m uvicorn app.main:app --port "$port" > "../../logs_${name}.log" 2>&1 &
    local pid=$!
    cd ../..
    
    echo -e "${GREEN}$name started with PID $pid. Logs redirecting to logs_${name}.log${NC}"
}

# Start all services
start_service "user_service" 8000
start_service "assessment_service" 8001
start_service "notification_service" 8002
start_service "ai_service" 8003
start_service "school_service" 8004

echo -e "${BLUE}=======================================${NC}"
echo -e "${GREEN}All services have been initiated.${NC}"
echo -e "You can monitor the logs with: ${YELLOW}tail -f logs_*.log${NC}"
echo -e "To stop all services, run: ${YELLOW}pkill -f uvicorn${NC}"
echo -e "${BLUE}=======================================${NC}"

# Health check
echo -e "${YELLOW}Waiting for services to spin up (5s)...${NC}"
sleep 5

echo -e "\n${BLUE}--- Health Status ---${NC}"
check_health() {
    local name=$1
    local port=$2
    if curl -s "http://localhost:${port}/" > /dev/null; then
        echo -e "$name (Port $port): ${GREEN}HEALTHY${NC}"
    else
        echo -e "$name (Port $port): ${RED}UNAVAILABLE${NC}"
    fi
}

check_health "User Service" 8000
check_health "Assessment Service" 8001
check_health "Notification Service" 8002
check_health "AI Service" 8003
check_health "School Service" 8004
echo -e "${BLUE}---------------------${NC}"
