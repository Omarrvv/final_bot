#!/bin/bash

# Set up any required environment variables
export TESTING=true
export DATABASE_URI="sqlite:///.:memory:"

# Create the integration tests directory if it doesn't exist
mkdir -p tests/integration

# Run unit tests for DatabaseManager cities methods
echo "Running unit tests for DatabaseManager city methods..."
python -m pytest tests/unit/knowledge/test_database_manager_cities.py -v

# Run unit tests for KnowledgeBase search_records
echo "Running unit tests for KnowledgeBase search_records..."
python -m pytest tests/unit/knowledge/test_kb_search_records.py -v

# Run integration tests
echo "Running integration tests for city functionality..."
python -m pytest tests/integration/test_kb_cities_integration.py -v

# Output results summary
echo "All tests completed." 