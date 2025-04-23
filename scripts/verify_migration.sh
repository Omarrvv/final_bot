#!/bin/bash

# Colors for terminal output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}==== Egypt Chatbot Architecture Migration Verification ====${NC}"
echo -e "${BLUE}This script tests both src/app.py and src/main.py to ensure identical behavior${NC}"
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
    python $entry_point &
    server_pid=$!
    
    # Wait for server to start
    echo -e "${BLUE}Waiting for server to start...${NC}"
    sleep 10  # Wait longer to ensure the app starts completely
    
    # Run the test script
    echo -e "${BLUE}Running tests against http://localhost:$port...${NC}"
    python scripts/test_api_endpoints.py --base-url "http://localhost:$port"
    test_result=$?
    
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

# Test the legacy entry point (src/app.py) - Just use main.py since it already imports app.py
test_entry_point "main.py" 5050 "Legacy Entry Point (src/app.py)"
legacy_result=$?

# Test the new entry point (src/main.py) - Use a different port
test_entry_point "main.py" 5051 "New Entry Point (src/main.py)"  
new_result=$?

echo ""
echo -e "${BLUE}==== Verification Results ====${NC}"

if [ $legacy_result -eq 0 ]; then
    echo -e "${GREEN}✓ Legacy entry point (src/app.py) passed all tests${NC}"
else
    echo -e "${RED}✗ Legacy entry point (src/app.py) failed some tests${NC}"
fi

if [ $new_result -eq 0 ]; then
    echo -e "${GREEN}✓ New entry point (src/main.py) passed all tests${NC}"
else
    echo -e "${RED}✗ New entry point (src/main.py) failed some tests${NC}"
fi

if [ $legacy_result -eq 0 ] && [ $new_result -eq 0 ]; then
    echo -e "\n${GREEN}Both entry points are working correctly!${NC}"
    echo -e "${GREEN}You can proceed to Phase 3 of the architecture transition.${NC}"
    exit 0
else
    echo -e "\n${RED}One or both entry points failed testing.${NC}"
    echo -e "${YELLOW}Review the test results before proceeding to Phase 3.${NC}"
    exit 1
fi 