#!/bin/bash
# Script to enrich tour packages
# This script:
# 1. Runs the SQL migration to add more tour packages
# 2. Generates embeddings for the new tour packages
# 3. Verifies the results

set -e  # Exit immediately if a command exits with a non-zero status

# Configuration
DB_USER="postgres"
DB_PASSWORD="postgres"
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="egypt_chatbot"
MIGRATION_FILE="migrations/20250702_add_tour_packages.sql"
EMBEDDING_SCRIPT="scripts/generate_tour_package_embeddings.py"

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

# Check if migration file exists
if [ ! -f "$MIGRATION_FILE" ]; then
    echo "Error: Migration file not found at $MIGRATION_FILE"
    exit 1
fi

# Check if embedding script exists
if [ ! -f "$EMBEDDING_SCRIPT" ]; then
    echo "Error: Embedding script not found at $EMBEDDING_SCRIPT"
    exit 1
fi

echo "=== Starting Tour Packages Enrichment Process ==="
echo "This script will:"
echo "1. Run the SQL migration to add more tour packages"
echo "2. Generate embeddings for the new tour packages"
echo "3. Verify the results"
echo ""

# Step 1: Run the SQL migration
echo "Step 1: Running SQL migration to add more tour packages..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f $MIGRATION_FILE

# Check if migration was successful
if [ $? -eq 0 ]; then
    echo "✅ SQL migration completed successfully"
else
    echo "❌ SQL migration failed"
    exit 1
fi

# Step 2: Generate embeddings for the new tour packages
echo ""
echo "Step 2: Generating embeddings for the new tour packages..."
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

# Count total tour packages
TOTAL_PACKAGES=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM tour_packages;" | tr -d ' ')

# Count tour packages with embeddings
PACKAGES_WITH_EMBEDDINGS=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM tour_packages WHERE embedding IS NOT NULL;" | tr -d ' ')

# Calculate percentage
PERCENTAGE=$(awk "BEGIN { printf \"%.2f\", ($PACKAGES_WITH_EMBEDDINGS / $TOTAL_PACKAGES) * 100 }")

echo "Total tour packages: $TOTAL_PACKAGES"
echo "Tour packages with embeddings: $PACKAGES_WITH_EMBEDDINGS"
echo "Coverage: $PERCENTAGE%"

if [ "$TOTAL_PACKAGES" -eq "$PACKAGES_WITH_EMBEDDINGS" ]; then
    echo "✅ All tour packages have embeddings"
else
    echo "❌ Some tour packages are missing embeddings"
    exit 1
fi

echo ""
echo "=== Tour Packages Enrichment Process Completed Successfully ==="
echo "The tour_packages table now has $TOTAL_PACKAGES records with embeddings."
echo ""
echo "Next steps:"
echo "1. Enrich events_festivals data"
echo "2. Create schema documentation"

exit 0
