#!/bin/bash

# Egypt Tourism Chatbot: Knowledge Base Connection Fix Script
# This script fixes the connection between the KnowledgeBase component and the database
# It handles both SQLite and PostgreSQL options based on the USE_POSTGRES flag

# Set up terminal colors for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Egypt Tourism Chatbot - KB Connection Fix  ${NC}"
echo -e "${BLUE}========================================${NC}"

# Step 1: Check for .env file and create if missing
echo -e "\n${YELLOW}Step 1: Checking for .env file...${NC}"
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file from .env.example...${NC}"
    cp .env.example .env
    echo -e "${GREEN}Created .env file${NC}"
else
    echo -e "${GREEN}Found existing .env file${NC}"
fi

# Step 2: Set necessary environment variables
echo -e "\n${YELLOW}Step 2: Setting up environment variables...${NC}"

# Check if PostgreSQL should be used
read -p "Do you want to use PostgreSQL instead of SQLite? (y/n): " use_postgres
if [[ $use_postgres == "y" || $use_postgres == "Y" ]]; then
    USE_POSTGRES="true"
    echo -e "${YELLOW}Using PostgreSQL database${NC}"
    
    # Get PostgreSQL connection details
    read -p "Enter PostgreSQL username (default: postgres): " pg_user
    pg_user=${pg_user:-postgres}
    
    read -p "Enter PostgreSQL host (default: localhost): " pg_host
    pg_host=${pg_host:-localhost}
    
    read -p "Enter PostgreSQL port (default: 5432): " pg_port
    pg_port=${pg_port:-5432}
    
    read -p "Enter PostgreSQL database name (default: egypt_chatbot): " pg_db
    pg_db=${pg_db:-egypt_chatbot}
    
    # Create PostgreSQL URI
    POSTGRES_URI="postgresql://${pg_user}@${pg_host}:${pg_port}/${pg_db}"
    DATABASE_URI=$POSTGRES_URI
    
    echo -e "${GREEN}PostgreSQL URI: ${POSTGRES_URI}${NC}"
else
    USE_POSTGRES="false"
    DATABASE_URI="sqlite:///./data/egypt_chatbot.db"
    echo -e "${YELLOW}Using SQLite database: ${DATABASE_URI}${NC}"
fi

# Update .env file with critical environment variables
echo -e "${YELLOW}Updating environment variables in .env file...${NC}"

# Function to update environment variable in .env file
update_env_var() {
    local var_name=$1
    local var_value=$2
    
    if grep -q "^${var_name}=" .env; then
        # Variable exists, update it
        sed -i.bak "s|^${var_name}=.*|${var_name}=${var_value}|" .env
    else
        # Variable doesn't exist, add it
        echo "${var_name}=${var_value}" >> .env
    fi
}

# Update critical environment variables
update_env_var "USE_NEW_KB" "true"
update_env_var "USE_NEW_API" "true"
update_env_var "USE_POSTGRES" "${USE_POSTGRES}"
update_env_var "DATABASE_URI" "${DATABASE_URI}"

if [[ $USE_POSTGRES == "true" ]]; then
    update_env_var "POSTGRES_URI" "${POSTGRES_URI}"
fi

echo -e "${GREEN}Updated environment variables in .env file${NC}"

# Export variables for current shell session
export USE_NEW_KB=true
export USE_NEW_API=true
export USE_POSTGRES=$USE_POSTGRES
export DATABASE_URI=$DATABASE_URI

if [[ $USE_POSTGRES == "true" ]]; then
    export POSTGRES_URI=$POSTGRES_URI
fi

# Step 3: Initialize and verify the database
echo -e "\n${YELLOW}Step 3: Initializing and verifying the database...${NC}"

# Create data directory if it doesn't exist
mkdir -p data

echo -e "${YELLOW}Running database initialization script...${NC}"
if python init_db.py; then
    echo -e "${GREEN}Database initialization successful${NC}"
else
    echo -e "${RED}Database initialization failed${NC}"
    exit 1
fi

# Step 4: Test Knowledge Base connection
echo -e "\n${YELLOW}Step 4: Testing Knowledge Base connection...${NC}"

if [[ $USE_POSTGRES == "true" ]]; then
    echo -e "${YELLOW}Verifying PostgreSQL connection...${NC}"
    if python verify_postgres_db.py; then
        echo -e "${GREEN}PostgreSQL connection verified successfully${NC}"
    else
        echo -e "${RED}PostgreSQL connection verification failed${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}Verifying SQLite connection...${NC}"
    if python verify_kb_connection.py; then
        echo -e "${GREEN}SQLite connection verified successfully${NC}"
    else
        echo -e "${RED}SQLite connection verification failed${NC}"
        exit 1
    fi
fi

# Step 5: Test end-to-end functionality
echo -e "\n${YELLOW}Step 5: Testing end-to-end functionality...${NC}"

echo -e "${YELLOW}Processing a test message through the chatbot...${NC}"
python - << EOF
import os
import sys
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Add project root to Python path
sys.path.append('.')

# Import necessary modules
try:
    from src.utils.factory import component_factory
    
    # Initialize component factory
    logger.info("Initializing component factory...")
    component_factory.initialize()
    
    # Create chatbot instance
    logger.info("Creating chatbot instance...")
    chatbot = component_factory.create_chatbot()
    
    # Test with a simple prompt
    logger.info("Testing chatbot with a simple query...")
    test_message = "Tell me about the Pyramids of Giza"
    test_session_id = "test-session-123"
    
    # Process the message
    response = chatbot.process_message(test_message, test_session_id)
    
    # Check if response contains meaningful content
    if response and len(response.response) > 30:  # Arbitrary length check
        logger.info("Test successful! Chatbot responded with:")
        logger.info(f"Response: {response.response[:100]}...")
        print("\n\033[0;32mTest successful! Knowledge Base is properly connected.\033[0m")
        sys.exit(0)
    else:
        logger.error("Test failed: Response is empty or too short")
        logger.error(f"Response: {response}")
        print("\n\033[0;31mTest failed. Knowledge Base may not be properly connected.\033[0m")
        sys.exit(1)
        
except Exception as e:
    logger.error(f"Error testing chatbot: {str(e)}", exc_info=True)
    print(f"\n\033[0;31mTest failed with error: {str(e)}\033[0m")
    sys.exit(1)
EOF

# Check if the test was successful
if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}=================================================${NC}"
    echo -e "${GREEN}Knowledge Base is now properly connected to the ${USE_POSTGRES == 'true' && 'PostgreSQL' || 'SQLite'} database!${NC}"
    echo -e "${GREEN}=================================================${NC}"
    echo -e "\nYou can now run the application with:"
    echo -e "${BLUE}python src/main.py${NC}"
else
    echo -e "\n${RED}=================================================${NC}"
    echo -e "${RED}Knowledge Base connection fix was not fully successful.${NC}"
    echo -e "${RED}=================================================${NC}"
    echo -e "\nPlease check the logs for more details."
    exit 1
fi 