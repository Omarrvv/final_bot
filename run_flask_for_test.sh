#!/bin/bash
# Script to start the Flask backend for KB integration testing

# Colors for terminal output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Egypt Tourism Chatbot - Flask Server Starter ===${NC}"
echo -e "${YELLOW}This script will start the Flask backend server for KB integration testing.${NC}"

# Activate Conda Environment (handle potential errors)
echo -e "${YELLOW}Activating conda environment...${NC}"
source $(conda info --base)/etc/profile.d/conda.sh
if ! conda activate egypt-tourism1; then
    echo -e "${RED}Error: Failed to activate conda environment 'egypt-tourism1'.${NC}"
    echo -e "${RED}Please ensure the environment exists and conda is initialized.${NC}"
    exit 1
fi
echo -e "${GREEN}Using conda environment: $(conda info --envs | grep \* | awk '{print $1}')${NC}"

# Add project root to PYTHONPATH
export PYTHONPATH=".:$PYTHONPATH"
echo -e "${GREEN}PYTHONPATH set to: $PYTHONPATH${NC}"

# Make sure USE_NEW_KB is enabled
echo -e "${YELLOW}Checking USE_NEW_KB setting in .env...${NC}"
if grep -q "USE_NEW_KB=true" .env; then
    echo -e "${GREEN}USE_NEW_KB is enabled. Will use SQLite Knowledge Base.${NC}"
else
    echo -e "${RED}Warning: USE_NEW_KB is not enabled in .env. Tests may fail.${NC}"
    echo -e "${YELLOW}Please set USE_NEW_KB=true in your .env file.${NC}"
    echo -e "${YELLOW}Press Enter to continue anyway or Ctrl+C to cancel...${NC}"
    read
fi

# Start the Flask backend
echo -e "${YELLOW}Starting Flask backend on port 5001...${NC}"
python -m flask --app src.app:create_app run --host 0.0.0.0 --port 5001

echo -e "${GREEN}Backend stopped.${NC}" 