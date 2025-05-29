#!/usr/bin/env python
"""
Review Foreign Key Constraints

This script:
1. Examines all foreign key constraints in the database
2. Analyzes their ON DELETE and ON UPDATE actions
3. Recommends changes based on business requirements
"""

import os
import sys
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from tabulate import tabulate

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('foreign_keys_review.log')
    ]
)
logger = logging.getLogger(__name__)

# Database connection parameters
DB_NAME = os.environ.get("DB_NAME", "egypt_chatbot")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "postgres")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")

def get_postgres_uri():
    """Get PostgreSQL connection URI"""
    return f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def get_foreign_keys():
    """Get all foreign key constraints in the database"""
    postgres_uri = get_postgres_uri()
    
    try:
        # Connect to PostgreSQL
        logger.info(f"Connecting to PostgreSQL database: {DB_NAME}")
        conn = psycopg2.connect(postgres_uri)
        
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Query to get all foreign key constraints
            cursor.execute("""
                SELECT
                    tc.constraint_name,
                    tc.table_name AS source_table,
                    kcu.column_name AS source_column,
                    ccu.table_name AS target_table,
                    ccu.column_name AS target_column,
                    rc.update_rule,
                    rc.delete_rule
                FROM
                    information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage AS kcu
                        ON tc.constraint_name = kcu.constraint_name
                        AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage AS ccu
                        ON ccu.constraint_name = tc.constraint_name
                        AND ccu.table_schema = tc.table_schema
                    JOIN information_schema.referential_constraints AS rc
                        ON rc.constraint_name = tc.constraint_name
                WHERE
                    tc.constraint_type = 'FOREIGN KEY'
                ORDER BY
                    tc.table_name,
                    kcu.column_name
            """)
            
            foreign_keys = cursor.fetchall()
            
            return foreign_keys
            
    except Exception as e:
        logger.error(f"Error getting foreign keys: {str(e)}")
        return []
    finally:
        if 'conn' in locals():
            conn.close()

def analyze_foreign_keys(foreign_keys):
    """Analyze foreign key constraints and recommend changes"""
    # Group foreign keys by source table
    grouped_fks = {}
    for fk in foreign_keys:
        source_table = fk['source_table']
        if source_table not in grouped_fks:
            grouped_fks[source_table] = []
        grouped_fks[source_table].append(fk)
    
    # Define business rules for foreign key actions
    business_rules = {
        # Format: (source_table, target_table, source_column): (update_rule, delete_rule, reason)
        ('attractions', 'cities', 'city_id'): ('CASCADE', 'SET NULL', 'Attractions should remain even if city is deleted, but city updates should cascade'),
        ('attractions', 'regions', 'region_id'): ('CASCADE', 'SET NULL', 'Attractions should remain even if region is deleted, but region updates should cascade'),
        ('attractions', 'attraction_types', 'type_id'): ('CASCADE', 'RESTRICT', 'Attraction types should not be deleted if attractions reference them'),
        ('accommodations', 'cities', 'city_id'): ('CASCADE', 'SET NULL', 'Accommodations should remain even if city is deleted, but city updates should cascade'),
        ('accommodations', 'regions', 'region_id'): ('CASCADE', 'SET NULL', 'Accommodations should remain even if region is deleted, but region updates should cascade'),
        ('accommodations', 'accommodation_types', 'type_id'): ('CASCADE', 'RESTRICT', 'Accommodation types should not be deleted if accommodations reference them'),
        ('cities', 'regions', 'region_id'): ('CASCADE', 'SET NULL', 'Cities should remain even if region is deleted, but region updates should cascade'),
    }
    
    # Analyze each foreign key
    recommendations = []
    for fk in foreign_keys:
        source_table = fk['source_table']
        target_table = fk['target_table']
        source_column = fk['source_column']
        current_update_rule = fk['update_rule']
        current_delete_rule = fk['delete_rule']
        
        # Check if we have a business rule for this foreign key
        key = (source_table, target_table, source_column)
        if key in business_rules:
            recommended_update_rule, recommended_delete_rule, reason = business_rules[key]
            
            # Check if current rules match recommended rules
            update_matches = current_update_rule == recommended_update_rule
            delete_matches = current_delete_rule == recommended_delete_rule
            
            if not (update_matches and delete_matches):
                recommendations.append({
                    'constraint_name': fk['constraint_name'],
                    'source_table': source_table,
                    'source_column': source_column,
                    'target_table': target_table,
                    'target_column': fk['target_column'],
                    'current_update_rule': current_update_rule,
                    'current_delete_rule': current_delete_rule,
                    'recommended_update_rule': recommended_update_rule,
                    'recommended_delete_rule': recommended_delete_rule,
                    'reason': reason
                })
    
    return recommendations

def generate_migration_script(recommendations):
    """Generate a migration script to fix foreign key constraints"""
    if not recommendations:
        return "-- No changes needed for foreign key constraints"
    
    script = """-- Migration: Fix Foreign Key Constraints
-- Date: 2025-05-09
-- Description: This migration updates foreign key constraints to match business requirements

"""
    
    for rec in recommendations:
        script += f"""-- Fix constraint {rec['constraint_name']} on {rec['source_table']}.{rec['source_column']}
-- Reason: {rec['reason']}
ALTER TABLE {rec['source_table']} DROP CONSTRAINT {rec['constraint_name']};
ALTER TABLE {rec['source_table']} ADD CONSTRAINT {rec['constraint_name']}
    FOREIGN KEY ({rec['source_column']})
    REFERENCES {rec['target_table']}({rec['target_column']})
    ON UPDATE {rec['recommended_update_rule']}
    ON DELETE {rec['recommended_delete_rule']};

"""
    
    return script

def main():
    """Main function"""
    logger.info("Reviewing foreign key constraints")
    
    # Get all foreign key constraints
    foreign_keys = get_foreign_keys()
    
    if not foreign_keys:
        logger.error("No foreign key constraints found")
        return
    
    # Print all foreign key constraints
    logger.info(f"Found {len(foreign_keys)} foreign key constraints")
    
    # Format for tabulate
    table_data = []
    for fk in foreign_keys:
        table_data.append([
            fk['constraint_name'],
            f"{fk['source_table']}.{fk['source_column']}",
            f"{fk['target_table']}.{fk['target_column']}",
            fk['update_rule'],
            fk['delete_rule']
        ])
    
    table_headers = ["Constraint Name", "Source", "Target", "ON UPDATE", "ON DELETE"]
    table = tabulate(table_data, headers=table_headers, tablefmt="grid")
    
    print("\nCurrent Foreign Key Constraints:")
    print(table)
    
    # Analyze foreign key constraints
    recommendations = analyze_foreign_keys(foreign_keys)
    
    if not recommendations:
        logger.info("All foreign key constraints match business requirements")
        print("\nAll foreign key constraints match business requirements")
        return
    
    # Print recommendations
    logger.info(f"Found {len(recommendations)} foreign key constraints that need to be updated")
    
    # Format for tabulate
    table_data = []
    for rec in recommendations:
        table_data.append([
            rec['constraint_name'],
            f"{rec['source_table']}.{rec['source_column']}",
            f"{rec['target_table']}.{rec['target_column']}",
            rec['current_update_rule'],
            rec['current_delete_rule'],
            rec['recommended_update_rule'],
            rec['recommended_delete_rule'],
            rec['reason']
        ])
    
    table_headers = ["Constraint", "Source", "Target", "Current Update", "Current Delete", "Recommended Update", "Recommended Delete", "Reason"]
    table = tabulate(table_data, headers=table_headers, tablefmt="grid")
    
    print("\nRecommended Foreign Key Constraint Changes:")
    print(table)
    
    # Generate migration script
    script = generate_migration_script(recommendations)
    
    # Save migration script
    script_path = "migrations/20250509_fix_foreign_key_constraints.sql"
    with open(script_path, "w") as f:
        f.write(script)
    
    logger.info(f"Generated migration script: {script_path}")
    print(f"\nGenerated migration script: {script_path}")

if __name__ == "__main__":
    main()
