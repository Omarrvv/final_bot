#!/bin/bash
# Master script to run all enrichment processes
# This script:
# 1. Runs the FAQ enrichment process
# 2. Runs the tour packages enrichment process
# 3. Runs the events and festivals enrichment process
# 4. Verifies the overall results

set -e  # Exit immediately if a command exits with a non-zero status

# Configuration
DB_USER="postgres"
DB_PASSWORD="postgres"
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="egypt_chatbot"
FAQ_SCRIPT="scripts/run_faq_enrichment.sh"
TOUR_PACKAGES_SCRIPT="scripts/run_tour_packages_enrichment.sh"
EVENTS_SCRIPT="scripts/run_events_enrichment.sh"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if required commands exist
if ! command_exists psql; then
    echo "Error: PostgreSQL client (psql) is required but not found"
    exit 1
fi

# Check if scripts exist
if [ ! -f "$FAQ_SCRIPT" ]; then
    echo "Error: FAQ enrichment script not found at $FAQ_SCRIPT"
    exit 1
fi

if [ ! -f "$TOUR_PACKAGES_SCRIPT" ]; then
    echo "Error: Tour packages enrichment script not found at $TOUR_PACKAGES_SCRIPT"
    exit 1
fi

if [ ! -f "$EVENTS_SCRIPT" ]; then
    echo "Error: Events enrichment script not found at $EVENTS_SCRIPT"
    exit 1
fi

# Make scripts executable
chmod +x $FAQ_SCRIPT
chmod +x $TOUR_PACKAGES_SCRIPT
chmod +x $EVENTS_SCRIPT

echo "=== Starting Complete Database Enrichment Process ==="
echo "This script will:"
echo "1. Run the FAQ enrichment process"
echo "2. Run the tour packages enrichment process"
echo "3. Run the events and festivals enrichment process"
echo "4. Verify the overall results"
echo ""

# Step 1: Run the FAQ enrichment process
echo "Step 1: Running FAQ enrichment process..."
./$FAQ_SCRIPT

# Check if the process was successful
if [ $? -eq 0 ]; then
    echo "✅ FAQ enrichment completed successfully"
else
    echo "❌ FAQ enrichment failed"
    exit 1
fi

# Step 2: Run the tour packages enrichment process
echo ""
echo "Step 2: Running tour packages enrichment process..."
./$TOUR_PACKAGES_SCRIPT

# Check if the process was successful
if [ $? -eq 0 ]; then
    echo "✅ Tour packages enrichment completed successfully"
else
    echo "❌ Tour packages enrichment failed"
    exit 1
fi

# Step 3: Run the events and festivals enrichment process
echo ""
echo "Step 3: Running events and festivals enrichment process..."
./$EVENTS_SCRIPT

# Check if the process was successful
if [ $? -eq 0 ]; then
    echo "✅ Events and festivals enrichment completed successfully"
else
    echo "❌ Events and festivals enrichment failed"
    exit 1
fi

# Step 4: Verify the overall results
echo ""
echo "Step 4: Verifying the overall results..."

# Count total records in each table
TOTAL_FAQS=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM tourism_faqs;" | tr -d ' ')
TOTAL_TOUR_PACKAGES=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM tour_packages;" | tr -d ' ')
TOTAL_EVENTS=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM events_festivals;" | tr -d ' ')

# Count records with embeddings in each table
FAQS_WITH_EMBEDDINGS=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM tourism_faqs WHERE embedding IS NOT NULL;" | tr -d ' ')
TOUR_PACKAGES_WITH_EMBEDDINGS=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM tour_packages WHERE embedding IS NOT NULL;" | tr -d ' ')
EVENTS_WITH_EMBEDDINGS=$(PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c "SELECT COUNT(*) FROM events_festivals WHERE embedding IS NOT NULL;" | tr -d ' ')

# Calculate percentages
FAQ_PERCENTAGE=$(awk "BEGIN { printf \"%.2f\", ($FAQS_WITH_EMBEDDINGS / $TOTAL_FAQS) * 100 }")
TOUR_PACKAGES_PERCENTAGE=$(awk "BEGIN { printf \"%.2f\", ($TOUR_PACKAGES_WITH_EMBEDDINGS / $TOTAL_TOUR_PACKAGES) * 100 }")
EVENTS_PERCENTAGE=$(awk "BEGIN { printf \"%.2f\", ($EVENTS_WITH_EMBEDDINGS / $TOTAL_EVENTS) * 100 }")

echo "Tourism FAQs: $FAQS_WITH_EMBEDDINGS/$TOTAL_FAQS ($FAQ_PERCENTAGE%)"
echo "Tour Packages: $TOUR_PACKAGES_WITH_EMBEDDINGS/$TOTAL_TOUR_PACKAGES ($TOUR_PACKAGES_PERCENTAGE%)"
echo "Events and Festivals: $EVENTS_WITH_EMBEDDINGS/$TOTAL_EVENTS ($EVENTS_PERCENTAGE%)"

# Check if all records have embeddings
if [ "$TOTAL_FAQS" -eq "$FAQS_WITH_EMBEDDINGS" ] && [ "$TOTAL_TOUR_PACKAGES" -eq "$TOUR_PACKAGES_WITH_EMBEDDINGS" ] && [ "$TOTAL_EVENTS" -eq "$EVENTS_WITH_EMBEDDINGS" ]; then
    echo "✅ All records have embeddings"
else
    echo "❌ Some records are missing embeddings"
    exit 1
fi

echo ""
echo "=== Complete Database Enrichment Process Completed Successfully ==="
echo "The database now has:"
echo "- $TOTAL_FAQS tourism FAQs"
echo "- $TOTAL_TOUR_PACKAGES tour packages"
echo "- $TOTAL_EVENTS events and festivals"
echo ""
echo "All records have embeddings for vector search."
echo ""
echo "The schema documentation has been created at docs/database_schema.md"
echo ""
echo "The Egypt Tourism Chatbot database is now ready for comprehensive tourism queries."

exit 0
