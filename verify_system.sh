#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo "====== Egypt Tourism Chatbot System Verification ======"

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}[ERROR] .env file not found. Please create it.${NC}"
    exit 1
fi

echo -e "${GREEN}[PASS] .env file exists${NC}"

# Check feature flags
echo "Checking feature flags..."
USE_NEW_KB=$(grep "USE_NEW_KB" .env | cut -d '=' -f2 | tr -d '[:space:]' | tr '[:upper:]' '[:lower:]')
USE_NEW_API=$(grep "USE_NEW_API" .env | cut -d '=' -f2 | tr -d '[:space:]' | tr '[:upper:]' '[:lower:]')
USE_REDIS=$(grep "USE_REDIS" .env | cut -d '=' -f2 | tr -d '[:space:]' | tr '[:upper:]' '[:lower:]')

if [ "$USE_NEW_KB" != "true" ]; then
    echo -e "${RED}[ERROR] USE_NEW_KB must be set to true in .env${NC}"
    exit 1
fi

if [ "$USE_NEW_API" != "true" ]; then
    echo -e "${RED}[ERROR] USE_NEW_API must be set to true in .env${NC}"
    exit 1
fi

if [ "$USE_REDIS" != "true" ]; then
    echo -e "${YELLOW}[WARNING] USE_REDIS is not set to true. Redis functionality will be limited.${NC}"
fi

echo -e "${GREEN}[PASS] Feature flags check passed${NC}"

# Check security settings
echo "Checking security settings..."
ALLOWED_ORIGINS=$(grep "ALLOWED_ORIGINS" .env | cut -d '=' -f2)
if [[ "$ALLOWED_ORIGINS" == *"*"* ]]; then
    echo -e "${RED}[ERROR] ALLOWED_ORIGINS contains wildcard '*'. This is a security risk.${NC}"
    exit 1
fi

echo -e "${GREEN}[PASS] Security settings check passed${NC}"

# Verify database connection and data
echo "Verifying knowledge base and database..."
python scripts/verify_knowledge_base.py
if [ $? -ne 0 ]; then
    echo -e "${RED}[ERROR] Knowledge base verification failed${NC}"
    exit 1
fi

echo -e "${GREEN}[PASS] Knowledge base verification passed${NC}"

# Verify Redis connection if enabled
if [ "$USE_REDIS" == "true" ]; then
    echo "Verifying Redis connection..."
    
    # Create a temporary Python script to test Redis
    cat > /tmp/test_redis.py << 'EOF'
import redis
import os
import sys
from dotenv import load_dotenv

load_dotenv()

def test_redis():
    redis_uri = os.getenv("REDIS_URI", "redis://localhost:6379")
    try:
        r = redis.from_url(redis_uri)
        # Test write
        r.set("test_key", "test_value")
        # Test read
        value = r.get("test_key")
        if value != b"test_value":
            print(f"[ERROR] Redis read/write test failed. Expected 'test_value', got '{value}'")
            return False
        # Test delete
        r.delete("test_key")
        print(f"[INFO] Successfully connected to Redis at {redis_uri}")
        return True
    except redis.exceptions.ConnectionError as e:
        print(f"[ERROR] Could not connect to Redis: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Redis error: {e}")
        return False

if __name__ == "__main__":
    success = test_redis()
    sys.exit(0 if success else 1)
EOF

    python /tmp/test_redis.py
    if [ $? -ne 0 ]; then
        echo -e "${RED}[ERROR] Redis connection verification failed${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}[PASS] Redis connection verification passed${NC}"
    rm /tmp/test_redis.py
fi

# Run unit tests
echo "Running unit tests..."
python -m pytest tests/unit -v
if [ $? -ne 0 ]; then
    echo -e "${RED}[ERROR] Unit tests failed${NC}"
    exit 1
fi

echo -e "${GREEN}[PASS] Unit tests passed${NC}"

# Run integration tests if requested
if [ "$1" == "--with-integration" ]; then
    echo "Running integration tests..."
    python -m pytest tests/integration -v
    if [ $? -ne 0 ]; then
        echo -e "${RED}[ERROR] Integration tests failed${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}[PASS] Integration tests passed${NC}"
fi

echo -e "${GREEN}====== All system verification checks passed! ======${NC}"
echo "You can now run the application with: python src/main.py"
exit 0 