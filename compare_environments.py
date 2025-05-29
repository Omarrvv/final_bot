#!/usr/bin/env python3
"""
Compare data between production and test environments.

This script:
1. Connects to both production and test databases
2. Compares table structures and record counts
3. Samples and compares data from key tables
4. Reports differences and similarities
"""

import os
import sys
import logging
import argparse
import psycopg2
from psycopg2.extras import RealDictCursor
from tabulate import tabulate
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database connection parameters
PROD_DB_PARAMS = {
    'dbname': 'egypt_chatbot',
    'user': 'postgres',
    'password': 'postgres',
    'host': 'localhost',
    'port': '5432'
}

TEST_DB_PARAMS = {
    'dbname': 'egypt_chatbot_migration_test',
    'user': 'postgres',
    'password': 'postgres',
    'host': 'localhost',
    'port': '5432'
}

# Tables to compare
TABLES_TO_COMPARE = [
    'cities',
    'attractions',
    'accommodations',
    'regions',
    'users',
    'attraction_types',
    'accommodation_types'
]

def connect_to_db(params):
    """Connect to PostgreSQL database"""
    try:
        conn = psycopg2.connect(**params)
        conn.autocommit = False
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        return None

def get_table_structure(conn, table_name):
    """Get table structure"""
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(f"""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position
        """, (table_name,))
        return cursor.fetchall()

def get_table_count(conn, table_name):
    """Get record count for a table"""
    with conn.cursor() as cursor:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        return cursor.fetchone()[0]

def get_table_sample(conn, table_name, limit=5):
    """Get a sample of records from a table"""
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
        return cursor.fetchall()

def compare_table_structures(prod_structure, test_structure):
    """Compare table structures between environments"""
    prod_cols = {col['column_name']: col for col in prod_structure}
    test_cols = {col['column_name']: col for col in test_structure}
    
    # Find columns in prod but not in test
    prod_only = [col for col in prod_cols if col not in test_cols]
    
    # Find columns in test but not in prod
    test_only = [col for col in test_cols if col not in prod_cols]
    
    # Find columns with different data types
    different_types = []
    for col in prod_cols:
        if col in test_cols and prod_cols[col]['data_type'] != test_cols[col]['data_type']:
            different_types.append({
                'column': col,
                'prod_type': prod_cols[col]['data_type'],
                'test_type': test_cols[col]['data_type']
            })
    
    return {
        'prod_only': prod_only,
        'test_only': test_only,
        'different_types': different_types,
        'is_identical': len(prod_only) == 0 and len(test_only) == 0 and len(different_types) == 0
    }

def compare_environments(args):
    """Compare production and test environments"""
    # Connect to databases
    logger.info("Connecting to production database...")
    prod_conn = connect_to_db(PROD_DB_PARAMS)
    if not prod_conn:
        logger.error("Failed to connect to production database")
        return False
    
    logger.info("Connecting to test database...")
    test_conn = connect_to_db(TEST_DB_PARAMS)
    if not test_conn:
        logger.error("Failed to connect to test database")
        prod_conn.close()
        return False
    
    try:
        # Compare tables
        comparison_results = []
        
        for table in TABLES_TO_COMPARE:
            logger.info(f"Comparing table: {table}")
            
            # Get table structures
            prod_structure = get_table_structure(prod_conn, table)
            test_structure = get_table_structure(test_conn, table)
            
            # Compare structures
            structure_comparison = compare_table_structures(prod_structure, test_structure)
            
            # Get record counts
            prod_count = get_table_count(prod_conn, table)
            test_count = get_table_count(test_conn, table)
            
            # Get data samples if requested
            prod_sample = None
            test_sample = None
            if args.sample:
                prod_sample = get_table_sample(prod_conn, table, args.sample_size)
                test_sample = get_table_sample(test_conn, table, args.sample_size)
            
            # Add to results
            comparison_results.append({
                'table': table,
                'structure': structure_comparison,
                'prod_count': prod_count,
                'test_count': test_count,
                'count_match': prod_count == test_count,
                'prod_sample': prod_sample,
                'test_sample': test_sample
            })
        
        # Generate report
        print("\n=== Environment Comparison Report ===\n")
        print(f"Production Database: {PROD_DB_PARAMS['dbname']}")
        print(f"Test Database: {TEST_DB_PARAMS['dbname']}")
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Table structure and count comparison
        table_data = []
        for result in comparison_results:
            structure_status = "✅ Identical" if result['structure']['is_identical'] else "❌ Different"
            count_status = "✅ Match" if result['count_match'] else "❌ Differ"
            
            table_data.append([
                result['table'],
                structure_status,
                result['prod_count'],
                result['test_count'],
                count_status
            ])
        
        print(tabulate(
            table_data,
            headers=["Table", "Structure", "Prod Count", "Test Count", "Count Status"],
            tablefmt="grid"
        ))
        
        # Detailed structure differences
        print("\n=== Structure Differences ===\n")
        for result in comparison_results:
            if not result['structure']['is_identical']:
                print(f"\nTable: {result['table']}")
                
                if result['structure']['prod_only']:
                    print("  Columns in Production only:")
                    for col in result['structure']['prod_only']:
                        print(f"    - {col}")
                
                if result['structure']['test_only']:
                    print("  Columns in Test only:")
                    for col in result['structure']['test_only']:
                        print(f"    - {col}")
                
                if result['structure']['different_types']:
                    print("  Columns with different data types:")
                    for diff in result['structure']['different_types']:
                        print(f"    - {diff['column']}: Prod={diff['prod_type']}, Test={diff['test_type']}")
        
        # Data samples if requested
        if args.sample:
            print("\n=== Data Samples ===\n")
            for result in comparison_results:
                print(f"\nTable: {result['table']} (showing {min(args.sample_size, len(result['prod_sample']))} records)")
                
                if result['prod_sample'] and result['test_sample']:
                    print("\nProduction Sample:")
                    for i, record in enumerate(result['prod_sample']):
                        print(f"  Record {i+1}: {json.dumps(record, default=str)[:100]}...")
                    
                    print("\nTest Sample:")
                    for i, record in enumerate(result['test_sample']):
                        print(f"  Record {i+1}: {json.dumps(record, default=str)[:100]}...")
        
        # Summary
        identical_structures = sum(1 for r in comparison_results if r['structure']['is_identical'])
        matching_counts = sum(1 for r in comparison_results if r['count_match'])
        
        print("\n=== Summary ===\n")
        print(f"Tables with identical structures: {identical_structures}/{len(comparison_results)}")
        print(f"Tables with matching record counts: {matching_counts}/{len(comparison_results)}")
        
        if identical_structures == len(comparison_results) and matching_counts == len(comparison_results):
            print("\n✅ Environments are structurally identical with matching record counts")
        else:
            print("\n⚠️ Environments have differences that may need attention")
        
        return True
        
    except Exception as e:
        logger.error(f"Error comparing environments: {str(e)}")
        return False
    finally:
        prod_conn.close()
        test_conn.close()

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Compare production and test environments")
    parser.add_argument("--sample", action="store_true", help="Include data samples in the report")
    parser.add_argument("--sample-size", type=int, default=3, help="Number of sample records to show (default: 3)")
    args = parser.parse_args()
    
    success = compare_environments(args)
    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
