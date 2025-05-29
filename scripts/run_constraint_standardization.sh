#!/bin/bash
# Script to standardize foreign key constraints
# This script:
# 1. Runs the SQL migration to standardize foreign key constraints
# 2. Verifies the changes

set -e  # Exit immediately if a command exits with a non-zero status

# Configuration
DB_USER="postgres"
DB_PASSWORD="postgres"
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="egypt_chatbot"
MIGRATION_FILE="migrations/20250704_standardize_foreign_key_constraints.sql"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if required commands exist
if ! command_exists psql; then
    echo "Error: PostgreSQL client (psql) is required but not found"
    exit 1
fi

# Check if migration file exists
if [ ! -f "$MIGRATION_FILE" ]; then
    echo "Error: Migration file not found at $MIGRATION_FILE"
    exit 1
fi

echo "=== Starting Foreign Key Constraint Standardization Process ==="
echo "This script will:"
echo "1. Run the SQL migration to standardize foreign key constraints"
echo "2. Verify the changes"
echo ""

# Step 1: Run the SQL migration
echo "Step 1: Running SQL migration to standardize foreign key constraints..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f $MIGRATION_FILE

# Check if migration was successful
if [ $? -eq 0 ]; then
    echo "✅ SQL migration completed successfully"
else
    echo "❌ SQL migration failed"
    exit 1
fi

# Step 2: Verify the changes
echo ""
echo "Step 2: Verifying the changes..."

# Check the foreign key constraints
echo "Checking foreign key constraints..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
SELECT
    tc.table_name, 
    kcu.column_name, 
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name,
    rc.delete_rule,
    rc.update_rule
FROM 
    information_schema.table_constraints AS tc 
    JOIN information_schema.key_column_usage AS kcu
      ON tc.constraint_name = kcu.constraint_name
      AND tc.table_schema = kcu.table_schema
    JOIN information_schema.constraint_column_usage AS ccu
      ON ccu.constraint_name = tc.constraint_name
      AND ccu.table_schema = tc.table_schema
    JOIN information_schema.referential_constraints AS rc
      ON tc.constraint_name = rc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
AND tc.table_name IN ('tourism_faqs', 'destinations', 'transportation_routes', 'events_festivals', 'practical_info', 'tour_packages')
ORDER BY tc.table_name, kcu.column_name;
"

echo ""
echo "=== Foreign Key Constraint Standardization Process Completed Successfully ==="
echo ""
echo "The foreign key constraints have been standardized according to the following strategy:"
echo "1. For category references: ON DELETE CASCADE, ON UPDATE CASCADE"
echo "   - If a category is deleted or renamed, all associated records are updated accordingly"
echo ""
echo "2. For hierarchical references: ON DELETE RESTRICT, ON UPDATE CASCADE"
echo "   - Prevents deletion of parent records that have children"
echo "   - Allows updates to propagate to child records"
echo ""
echo "3. For entity references: ON DELETE RESTRICT, ON UPDATE CASCADE"
echo "   - Prevents accidental deletion of referenced entities"
echo "   - Allows updates to propagate to referencing records"
echo ""
echo "This standardization ensures consistent behavior across the database and prevents unexpected data loss."

exit 0
