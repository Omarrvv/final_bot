#!/bin/bash
# Script to enrich events and festivals
# This script:
# 1. Runs the SQL migrations to add more events and festivals
# 2. Generates embeddings for the new events
# 3. Verifies the results

set -e  # Exit immediately if a command exits with a non-zero status

# Configuration
DB_USER="postgres"
DB_PASSWORD="postgres"
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="egypt_chatbot"
MIGRATION_FILE1="migrations/20250703_add_events_festivals_part1.sql"
MIGRATION_FILE2="migrations/20250703_add_events_festivals_part2.sql"
EMBEDDING_SCRIPT="scripts/generate_events_embeddings.py"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if required commands exist
if ! command_exists psql; then
    echo "Error: PostgreSQL client (psql) is required but not found"
    exit 1
fi

if ! command_exists python3; then
    echo "Error: Python 3 is required but not found"
    exit 1
fi

# Check if migration files exist
if [ ! -f "$MIGRATION_FILE1" ]; then
    echo "Error: Migration file not found at $MIGRATION_FILE1"
    exit 1
fi

if [ ! -f "$MIGRATION_FILE2" ]; then
    echo "Error: Migration file not found at $MIGRATION_FILE2"
    exit 1
fi

# Check if embedding script exists
if [ ! -f "$EMBEDDING_SCRIPT" ]; then
    echo "Error: Embedding script not found at $EMBEDDING_SCRIPT"
    exit 1
fi

echo "=== Starting Events and Festivals Enrichment Process ==="
echo "This script will:"
echo "1. Run the SQL migrations to add more events and festivals"
echo "2. Generate embeddings for the new events"
echo "3. Verify the results"
echo ""

# Step 1: Run the SQL migrations
echo "Step 1: Running SQL migrations to add more events and festivals..."
echo "Running part 1..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f $MIGRATION_FILE1

# Check if migration was successful
if [ $? -eq 0 ]; then
    echo "✅ SQL migration part 1 completed successfully"
else
    echo "❌ SQL migration part 1 failed"
    exit 1
fi

echo "Running part 2..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f $MIGRATION_FILE2

# Check if migration was successful
if [ $? -eq 0 ]; then
    echo "✅ SQL migration part 2 completed successfully"
else
    echo "❌ SQL migration part 2 failed"
    exit 1
fi

# Step 2: Generate embeddings for the new events
echo ""
echo "Step 2: Generating embeddings for the new events..."
python3 $EMBEDDING_SCRIPT

# Check if embedding generation was successful
if [ $? -eq 0 ]; then
    echo "✅ Embedding generation completed successfully"
else
    echo "❌ Embedding generation failed"
    exit 1
fi

# Step 3: Verify the results
echo ""
echo "Step 3: Verifying the results..."

# Count total events
TOTAL_EVENTS=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM events_festivals;" | tr -d ' ')

# Count events with embeddings
EVENTS_WITH_EMBEDDINGS=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM events_festivals WHERE embedding IS NOT NULL;" | tr -d ' ')

# Calculate percentage
PERCENTAGE=$(awk "BEGIN { printf \"%.2f\", ($EVENTS_WITH_EMBEDDINGS / $TOTAL_EVENTS) * 100 }")

echo "Total events and festivals: $TOTAL_EVENTS"
echo "Events and festivals with embeddings: $EVENTS_WITH_EMBEDDINGS"
echo "Coverage: $PERCENTAGE%"

if [ "$TOTAL_EVENTS" -eq "$EVENTS_WITH_EMBEDDINGS" ]; then
    echo "✅ All events and festivals have embeddings"
else
    echo "❌ Some events and festivals are missing embeddings"
    exit 1
fi

echo ""
echo "=== Events and Festivals Enrichment Process Completed Successfully ==="
echo "The events_festivals table now has $TOTAL_EVENTS records with embeddings."
echo ""
echo "Next step: Create schema documentation"

exit 0
