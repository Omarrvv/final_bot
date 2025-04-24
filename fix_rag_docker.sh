#!/bin/bash
set -e

# Enable RAG in container environment
echo "Checking for RAG flag in container..."
grep -q "USE_RAG" /app/.env || echo "USE_RAG=true" >> /app/.env
sed -i 's/USE_RAG=false/USE_RAG=true/g' /app/.env

# Check if it was updated
echo "Current RAG setting in container:"
grep "USE_RAG" /app/.env

# Also fix PostgreSQL query syntax - look for the '$not' operator
echo "Fixing MongoDB-style operators in database queries..."
find /app -name "*.py" -type f -exec grep -l "\$not" {} \; | while read file; do
    echo "Found MongoDB operator in $file, patching..."
    # Create backup
    cp "$file" "$file.bak"
    # Replace MongoDB operators with PostgreSQL syntax
    sed -i 's/"\$not"/\"NOT\"/g' "$file"
    sed -i "s/'\$not'/'NOT'/g" "$file"
    echo "Patched $file"
done

# Verify Knowledge Base has proper implementation
echo "Checking Knowledge Base implementation..."
KB_FILES=$(find /app -name "*knowledge_base*.py" -type f)
for file in $KB_FILES; do
    echo "Examining $file..."
    grep -q "class BaseKnowledgeItem" "$file" && echo "Found BaseKnowledgeItem class in $file"
done

# List database tables to check data
echo "Checking database tables..."
PGPASSWORD=$DB_PASSWORD psql -h db_postgres -U $DB_USERNAME -d $DB_NAME -c "\dt"

# Check if attractions table has data
echo "Checking attractions data..."
PGPASSWORD=$DB_PASSWORD psql -h db_postgres -U $DB_USERNAME -d $DB_NAME -c "SELECT COUNT(*) FROM attractions;"

echo "Fix script completed in container"
