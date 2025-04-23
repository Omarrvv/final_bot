#!/bin/bash

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Print header
echo -e "${BLUE}========================================"
echo -e "  Egypt Tourism Chatbot - Automated KB Fix  "
echo -e "========================================${NC}"

# Step 1: Check for .env file
echo -e "\n${GREEN}Step 1: Checking for .env file...${NC}"
if [ -f .env ]; then
    echo "Found existing .env file"
else
    echo "Creating .env file from .env.example"
    cp .env.example .env || cp src/.env.example .env || echo "No .env.example found"
fi

# Step 2: Set up environment variables
echo -e "\n${GREEN}Step 2: Setting up environment variables...${NC}"
# Always use SQLite in this automated version
echo "Using SQLite database"

# Update .env file with required settings
sed -i.bak 's/USE_NEW_KB=.*/USE_NEW_KB=true/' .env
sed -i.bak 's/USE_NEW_API=.*/USE_NEW_API=true/' .env
sed -i.bak 's/USE_POSTGRES=.*/USE_POSTGRES=false/' .env
sed -i.bak 's#DATABASE_URI=.*#DATABASE_URI=sqlite:///./data/egypt_chatbot.db#' .env

echo "Environment variables updated"

# Step 3: Initialize database
echo -e "\n${GREEN}Step 3: Initializing database...${NC}"
python scripts/initialize_database.py || python init_db.py

if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Database initialization failed${NC}"
    exit 1
fi

echo "Database initialized successfully"

# Step 4: Fix database connector methods
echo -e "\n${GREEN}Step 4: Fixing database connector methods...${NC}"
python fix_db_connector.py

if [ $? -ne 0 ]; then
    echo -e "${YELLOW}Warning: Database connector fix completed with some errors${NC}"
else
    echo "Database connector fixed successfully"
fi

# Step 5: Test Knowledge Base connection
echo -e "\n${GREEN}Step 5: Testing Knowledge Base connection...${NC}"
python test_kb_connection.py

if [ $? -ne 0 ]; then
    echo -e "${YELLOW}Warning: Knowledge Base connection test had issues${NC}"
else
    echo "Knowledge Base connection tested successfully"
fi

# Step 6: Run functionality test
echo -e "\n${GREEN}Step 6: Running functionality test...${NC}"
echo "Testing chatbot response..."
RESPONSE=$(curl -s "http://localhost:5050/api/health" | grep -i "success")

if [ -z "$RESPONSE" ]; then
    echo -e "${YELLOW}Warning: API health check failed or API not running${NC}"
    echo "Make sure the API is running on port 5050 before proceeding"
else
    echo "API health check passed successfully"
fi

# Step 7: Completion
echo -e "\n${BLUE}=========================================="
echo -e "  Knowledge Base Fix Complete  "
echo -e "==========================================${NC}"

echo "Next Steps:"
echo "1. Run 'python src/main.py' to start the FastAPI server"
echo "2. Access the API at http://localhost:5050/api/chat"
echo "3. Verify responses include data from the Knowledge Base"

echo -e "\n${GREEN}KB fix process completed!${NC}" 