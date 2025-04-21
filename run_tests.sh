#!/bin/bash
# Script to run tests for Egypt Tourism Chatbot

set -e  # Exit on any error

# Ensure we're in the project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "=== Egypt Tourism Chatbot Test Runner ==="
echo ""

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "Error: pytest is not installed. Please install it with 'pip install pytest pytest-cov pytest-asyncio'."
    exit 1
fi

# Check if .env file exists, create test version if not
if [ ! -f ".env" ]; then
    echo "Creating test .env file..."
    cat > .env << EOF
ENV=test
FLASK_ENV=testing
FLASK_DEBUG=0
LOG_LEVEL=ERROR
DATABASE_URI=sqlite:///data/egypt_chatbot.db
VECTOR_DB_URI=file:///data/vector_db
SESSION_STORAGE_URI=file:///data/sessions
JWT_SECRET=test_secret_key_for_jwt_tokens_in_tests
REDIS_URL=redis://localhost:6379/0
API_HOST=localhost
API_PORT=5050
FRONTEND_URL=http://localhost:3000
ANTHROPIC_API_KEY=test_anthropic_key
WEATHER_API_KEY=test_weather_key 
TRANSLATION_API_KEY=test_translation_key
USE_NEW_KB=false
USE_NEW_API=false
USE_POSTGRES=false
USE_REDIS=false
USE_NEW_NLU=false
USE_NEW_DIALOG=false
USE_RAG=false
USE_SERVICE_HUB=false
EOF
    echo "Test .env file created."
fi

echo "Running tests..."
echo ""

# Get command line arguments
COVERAGE_FLAG=""
TEST_PATH="tests/"
HTML_REPORT=""

# Parse arguments
for arg in "$@"
do
    case $arg in
        --cov)
        COVERAGE_FLAG="--cov=src"
        shift
        ;;
        --html)
        HTML_REPORT="--cov-report=html"
        shift
        ;;
        *)
        # If not a flag, assume it's a test path
        if [[ $arg != --* ]]; then
            TEST_PATH="$arg"
        fi
        shift
        ;;
    esac
done

# Run the tests
PYTHONPATH=. pytest $COVERAGE_FLAG $HTML_REPORT -v $TEST_PATH

# Show coverage report location if generated
if [ -n "$HTML_REPORT" ]; then
    echo ""
    echo "HTML coverage report generated in htmlcov/ directory."
    echo "Open htmlcov/index.html in your browser to view it."
fi

echo ""
echo "=== Test run complete ===" 