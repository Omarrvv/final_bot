#!/bin/bash
# Script to enrich tourism FAQs
# This script:
# 1. Runs the SQL migration to add more FAQs
# 2. Generates embeddings for the new FAQs
# 3. Verifies the results

set -e  # Exit immediately if a command exits with a non-zero status

# Configuration
DB_USER="postgres"
DB_PASSWORD="postgres"
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="egypt_chatbot"
MIGRATION_FILE="migrations/20250701_add_tourism_faqs.sql"
EMBEDDING_SCRIPT="scripts/generate_faq_embeddings.py"

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

echo "=== Starting FAQ Enrichment Process ==="
echo "This script will:"
echo "1. Run the SQL migration to add more FAQs"
echo "2. Generate embeddings for the new FAQs"
echo "3. Verify the results"
echo ""

# Step 1: Run the SQL migration
echo "Step 1: Running SQL migration to add more FAQs..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f $MIGRATION_FILE

# Check if migration was successful
if [ $? -eq 0 ]; then
    echo "✅ SQL migration completed successfully"
else
    echo "❌ SQL migration failed"
    exit 1
fi

# Step 2: Generate embeddings for the new FAQs
echo ""
echo "Step 2: Generating embeddings for the new FAQs..."
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

# Count total FAQs
TOTAL_FAQS=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM tourism_faqs;" | tr -d ' ')

# Count FAQs with embeddings
FAQS_WITH_EMBEDDINGS=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM tourism_faqs WHERE embedding IS NOT NULL;" | tr -d ' ')

# Calculate percentage
PERCENTAGE=$(awk "BEGIN { printf \"%.2f\", ($FAQS_WITH_EMBEDDINGS / $TOTAL_FAQS) * 100 }")

echo "Total FAQs: $TOTAL_FAQS"
echo "FAQs with embeddings: $FAQS_WITH_EMBEDDINGS"
echo "Coverage: $PERCENTAGE%"

if [ "$TOTAL_FAQS" -eq "$FAQS_WITH_EMBEDDINGS" ]; then
    echo "✅ All FAQs have embeddings"
else
    echo "❌ Some FAQs are missing embeddings"
    exit 1
fi

echo ""
echo "=== FAQ Enrichment Process Completed Successfully ==="
echo "The tourism_faqs table now has $TOTAL_FAQS records with embeddings."
echo ""
echo "Next steps:"
echo "1. Enrich tour_packages data"
echo "2. Enrich events_festivals data"
echo "3. Create schema documentation"

exit 0
