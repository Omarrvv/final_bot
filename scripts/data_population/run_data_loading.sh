#!/bin/bash
# Script to run data loading and verification

# Set the working directory to the project root
cd "$(dirname "$0")/../.."

echo "=== Starting Data Loading Process ==="
echo "This script will load all JSON data from the data directory into the PostgreSQL database."
echo "Make sure the database is running and properly configured."
echo ""

# Check if PostgreSQL is configured
if [ -z "$POSTGRES_URI" ]; then
    echo "POSTGRES_URI environment variable is not set."
    echo "Please set it to the PostgreSQL connection string."
    echo "Example: export POSTGRES_URI=postgresql://postgres:postgres@localhost:5432/egypt_chatbot"
    exit 1
fi

# Run data loading script
echo "Running data loading script..."
python scripts/data_population/load_all_data.py

# Check if data loading was successful
if [ $? -ne 0 ]; then
    echo "Data loading failed. Please check the logs for errors."
    exit 1
fi

echo ""
echo "=== Data Loading Completed ==="
echo ""

# Run data verification script
echo "=== Starting Data Verification Process ==="
echo "This script will verify that data has been correctly loaded into the PostgreSQL database."
echo ""

echo "Running data verification script..."
python scripts/data_population/verify_data_loading.py

# Check if data verification was successful
if [ $? -ne 0 ]; then
    echo "Data verification failed. Please check the logs for errors."
    exit 1
fi

echo ""
echo "=== Data Verification Completed ==="
echo ""
echo "Data loading and verification process completed successfully."
