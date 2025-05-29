#!/bin/bash
# Script to generate missing embeddings in the database

# Set up error handling
set -e

# Load environment variables
if [ -f .env ]; then
  source .env
fi

echo "Starting missing embeddings generation process..."

# Make the Python script executable
chmod +x scripts/generate_missing_embeddings.py

# First, run in dry-run mode to identify missing embeddings
echo "Identifying missing embeddings (dry run)..."
python3 scripts/generate_missing_embeddings.py --dry-run

# Ask for confirmation before proceeding
read -p "Do you want to proceed with generating and updating embeddings? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "Operation cancelled."
  exit 0
fi

# Run the Python script to generate and update embeddings
echo "Generating and updating embeddings..."
python3 scripts/generate_missing_embeddings.py

# Check if the script executed successfully
if [ $? -eq 0 ]; then
  echo "Embedding generation completed successfully!"
else
  echo "Embedding generation failed. Check the logs for details."
  exit 1
fi

# Run a simple validation query to verify all embeddings are present
echo "Running validation query..."

# Connect to PostgreSQL and run validation query
PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER -d $POSTGRES_DB -c "
-- Check for missing embeddings in all tables
SELECT table_name, 
       COUNT(*) as total_records,
       COUNT(*) FILTER (WHERE embedding IS NULL) as missing_embeddings,
       ROUND(100.0 * COUNT(*) FILTER (WHERE embedding IS NOT NULL) / COUNT(*), 2) as coverage_percentage
FROM (
    SELECT 'attractions' as table_name, embedding FROM attractions
    UNION ALL
    SELECT 'accommodations' as table_name, embedding FROM accommodations
    UNION ALL
    SELECT 'cities' as table_name, embedding FROM cities
    UNION ALL
    SELECT 'restaurants' as table_name, embedding FROM restaurants
    UNION ALL
    SELECT 'destinations' as table_name, embedding FROM destinations
    UNION ALL
    SELECT 'tourism_faqs' as table_name, embedding FROM tourism_faqs
    UNION ALL
    SELECT 'practical_info' as table_name, embedding FROM practical_info
    UNION ALL
    SELECT 'tour_packages' as table_name, embedding FROM tour_packages
    UNION ALL
    SELECT 'events_festivals' as table_name, embedding FROM events_festivals
    UNION ALL
    SELECT 'itineraries' as table_name, embedding FROM itineraries
) as all_tables
GROUP BY table_name
ORDER BY missing_embeddings DESC;
"

echo "Embedding generation process completed."
