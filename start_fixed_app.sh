#!/bin/bash

# Set colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=========================================="
echo -e "  Starting Egypt Tourism Chatbot  "
echo -e "==========================================${NC}"

# Get the absolute path to the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Set PYTHONPATH to include the project root
export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH}"

# Activate conda environment if available
if command -v conda &>/dev/null; then
    echo -e "${GREEN}Activating conda environment 'egypt-tourism1'...${NC}"
    # Try to activate the environment
    source "$(conda info --base)/etc/profile.d/conda.sh"
    if ! conda activate egypt-tourism1; then
        echo -e "${RED}Failed to activate conda environment 'egypt-tourism1'${NC}"
        echo -e "${RED}Creating environment from environment.yml...${NC}"
        if [ -f "environment.yml" ]; then
            conda env create -f environment.yml
            conda activate egypt-tourism1
        else
            echo -e "${RED}environment.yml not found. Please create the conda environment manually.${NC}"
            exit 1
        fi
    fi
fi

# Make sure we have the required packages
echo -e "${GREEN}Installing required packages...${NC}"
pip install -r requirements.txt

# Update environment variables
echo -e "${GREEN}Setting environment variables...${NC}"
export USE_NEW_KB=true
export USE_NEW_API=true
export USE_POSTGRES=false
export DATABASE_URI="sqlite:///./data/egypt_chatbot.db"

# Run the FastAPI server
echo -e "${GREEN}Starting FastAPI server...${NC}"
echo -e "${GREEN}PYTHONPATH: ${PYTHONPATH}${NC}"
echo -e "${GREEN}Current directory: $(pwd)${NC}"

# Using uvicorn to run the FastAPI app
python -m uvicorn src.main:app --host 0.0.0.0 --port 5050 --reload 