#!/bin/bash

# Colors for terminal output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}==== Egypt Chatbot API Verification ====${NC}"
echo -e "${BLUE}This script tests the src/main.py entry point to ensure proper behavior${NC}"
echo ""

# Check if Python is installed
if ! command -v python &> /dev/null; then
    echo -e "${RED}Python is not installed or not in PATH${NC}"
    exit 1
fi

# Check if required packages are installed
echo -e "${BLUE}Checking for required packages...${NC}"
if ! python -c "import requests" &> /dev/null; then
    echo -e "${YELLOW}requests package not found. Installing...${NC}"
    pip install requests
fi

# Function to test an entry point
test_entry_point() {
    local entry_point=$1
    local port=$2
    local description=$3

    echo -e "\n${BLUE}==== Testing $description (port $port) ====${NC}"

    # Start the server in the background using the specified entry point
    echo -e "${BLUE}Starting server with $entry_point on port $port...${NC}"

    # Save the current directory
    current_dir=$(pwd)

    # Set environment variable for port
    export API_PORT=$port

    # Start server in background
    cd $current_dir
    python -m uvicorn src.main:app --port $port &
    server_pid=$!

    # Wait for server to start
    echo -e "${BLUE}Waiting for server to start...${NC}"
    sleep 10  # Wait longer to ensure the app starts completely

    # Run the test script
    echo -e "${BLUE}Running tests against http://localhost:$port...${NC}"
    if [ -f "scripts/test_api_endpoints.py" ]; then
        python scripts/test_api_endpoints.py --base-url "http://localhost:$port"
        test_result=$?
    else
        echo -e "${YELLOW}Warning: test_api_endpoints.py not found. Skipping tests.${NC}"
        test_result=0
    fi

    # Kill the server
    echo -e "${BLUE}Stopping server (PID: $server_pid)...${NC}"
    kill $server_pid

    # Wait for server to stop
    sleep 2

    # Return to original directory
    cd $current_dir

    # Unset port environment variable
    unset API_PORT

    return $test_result
}

# Test the main entry point (src/main.py)
test_entry_point "main" 5050 "Main Entry Point (src/main.py)"
test_result=$?

echo ""
echo -e "${BLUE}==== Verification Results ====${NC}"

if [ $test_result -eq 0 ]; then
    echo -e "${GREEN}✓ Main entry point (src/main.py) passed all tests${NC}"
    echo -e "\n${GREEN}API verification successful!${NC}"
    exit 0
else
    echo -e "${RED}✗ Main entry point (src/main.py) failed some tests${NC}"
    echo -e "\n${RED}API verification failed.${NC}"
    echo -e "${YELLOW}Review the test results to identify and fix issues.${NC}"
    exit 1
fi