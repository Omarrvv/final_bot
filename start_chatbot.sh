#!/bin/bash
# Script to start both the Flask backend and React frontend

# Colors for terminal output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Egypt Tourism Chatbot Starter ===${NC}"
echo -e "${YELLOW}This script will start the backend server.${NC}"

# Activate Conda Environment (handle potential errors)
echo -e "${YELLOW}Activating conda environment...${NC}"
source $(conda info --base)/etc/profile.d/conda.sh
if ! conda activate egypt-tourism1; then
    echo -e "${RED}Error: Failed to activate conda environment 'egypt-tourism1'.${NC}"
    echo -e "${RED}Please ensure the environment exists and conda is initialized.${NC}"
    # Consider exiting here: exit 1
fi
echo -e "${GREEN}Using conda environment: $(conda info --envs | grep \* | awk '{print $1}')${NC}"

# Add project root to PYTHONPATH if needed (adjust if uvicorn handles it)
export PYTHONPATH=".:$PYTHONPATH"
echo -e "${GREEN}PYTHONPATH set to: $PYTHONPATH${NC}"

# Start Backend (FastAPI with Uvicorn)
echo -e "${YELLOW}Starting FastAPI backend with Uvicorn on port 5050...${NC}"
# Run Uvicorn directly - removed nohup for clearer foreground execution
# Add --log-config configs/log_conf.yaml if you have a logging config file
# Removed --reload for consistency with production command
uvicorn src.main:app --host 0.0.0.0 --port 5050 &
BACKEND_PID=$!
echo -e "${GREEN}Backend started with PID: $BACKEND_PID${NC}"

# Optional: Wait a bit for the backend to potentially initialize
echo -e "${YELLOW}Waiting a few seconds for backend...${NC}"
sleep 5

echo -e "${GREEN}Backend should be running on http://localhost:5050${NC}"
echo -e "${GREEN}Access the API documentation at http://localhost:5050/docs${NC}"
echo -e "${GREEN}To stop the backend, use 'kill $BACKEND_PID'${NC}"

# Keep the script running if needed, or exit
# wait $BACKEND_PID # This would keep the script attached to the background process

# --- Removed Frontend Starting Section --- 
# echo "Starting React frontend..."
# # Check if node_modules exists
# if [ -d "react-frontend/node_modules" ]; then
#   echo "Frontend dependencies already installed."
# else
#   echo "Installing frontend dependencies..."
#   (cd react-frontend && npm install)
# fi
# 
# echo "Starting React development server..."
# # Use nohup to run in background and redirect output
# nohup bash -c 'cd react-frontend && npm start' > react_frontend.log 2>&1 &
# FRONTEND_PID=$!
# echo "Frontend dev server started with PID: $FRONTEND_PID on http://localhost:3000"

echo -e "${GREEN}Script finished. Backend is running in the background.${NC}"
