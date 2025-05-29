#!/usr/bin/env python
"""
JSONB Query Optimization

This script:
1. Analyzes current JSONB query patterns
2. Creates optimized query functions
3. Benchmarks different JSONB query approaches
4. Generates recommendations for JSONB usage

Usage:
    python optimize_jsonb_queries.py [--table TABLE] [--iterations N]
"""

import os
import sys
import time
import logging
import argparse
import json
import statistics
import psycopg2
from psycopg2.extras import RealDictCursor
from tabulate import tabulate

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('jsonb_optimization.log')
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

def connect_to_database():
    """Connect to the PostgreSQL database"""
    try:
        conn = psycopg2.connect(get_postgres_uri())
        conn.autocommit = True
        logger.info(f"Connected to database: {DB_NAME}")
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        return None

def analyze_jsonb_columns(conn):
    """Analyze JSONB columns in the database"""
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Find all tables with JSONB columns
            cursor.execute("""
                SELECT 
                    table_name, 
                    column_name
                FROM 
                    information_schema.columns
                WHERE 
                    data_type = 'jsonb'
                ORDER BY 
                    table_name, column_name
            """)
            
            jsonb_columns = cursor.fetchall()
            
            if not jsonb_columns:
                logger.info("No JSONB columns found in the database")
                return []
            
            logger.info(f"Found {len(jsonb_columns)} JSONB columns in the database")
            
            # Analyze each JSONB column
            results = []
            for column in jsonb_columns:
                table_name = column["table_name"]
                column_name = column["column_name"]
                
                # Check if column has an index
                cursor.execute("""
                    SELECT 
                        indexname, 
                        indexdef
                    FROM 
                        pg_indexes
                    WHERE 
                        tablename = %s AND 
                        indexdef LIKE %s
                """, (table_name, f"%{column_name}%"))
                
                indexes = cursor.fetchall()
                
                # Get sample data
                cursor.execute(f"""
                    SELECT 
                        {column_name}
                    FROM 
                        {table_name}
                    WHERE 
                        {column_name} IS NOT NULL
                    LIMIT 5
                """)
                
                samples = cursor.fetchall()
                
                # Analyze structure
                structure = {}
                for sample in samples:
                    if sample[column_name]:
                        try:
                            if isinstance(sample[column_name], str):
                                data = json.loads(sample[column_name])
                            else:
                                data = sample[column_name]
                                
                            if isinstance(data, dict):
                                for key in data.keys():
                                    structure[key] = structure.get(key, 0) + 1
                        except:
                            pass
                
                # Get row count
                cursor.execute(f"""
                    SELECT 
                        COUNT(*) as count
                    FROM 
                        {table_name}
                    WHERE 
                        {column_name} IS NOT NULL
                """)
                
                row_count = cursor.fetchone()["count"]
                
                results.append({
                    "table_name": table_name,
                    "column_name": column_name,
                    "indexes": indexes,
                    "structure": structure,
                    "row_count": row_count
                })
            
            return results
            
    except Exception as e:
        logger.error(f"Error analyzing JSONB columns: {e}")
        return []

def benchmark_query_patterns(conn, table_name, column_name, iterations=50):
    """Benchmark different JSONB query patterns"""
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Get sample data for queries
            cursor.execute(f"""
                SELECT 
                    {column_name}
                FROM 
                    {table_name}
                WHERE 
                    {column_name} IS NOT NULL
                LIMIT 1
            """)
            
            sample = cursor.fetchone()
            if not sample or not sample[column_name]:
                logger.error(f"No sample data found for {table_name}.{column_name}")
                return []
            
            # Extract a key from the sample
            sample_data = sample[column_name]
            if isinstance(sample_data, str):
                sample_data = json.loads(sample_data)
                
            if not isinstance(sample_data, dict) or not sample_data:
                logger.error(f"Sample data is not a dictionary or is empty")
                return []
                
            sample_key = list(sample_data.keys())[0]
            sample_value = sample_data[sample_key]
            
            # Define query patterns to test
            query_patterns = [
                {
                    "name": "Simple JSON extraction",
                    "sql": f"""
                        SELECT 
                            id, 
                            {column_name}->'{sample_key}' as value
                        FROM 
                            {table_name}
                        WHERE 
                            {column_name} IS NOT NULL
                        LIMIT 10
                    """
                },
                {
                    "name": "JSON text extraction",
                    "sql": f"""
                        SELECT 
                            id, 
                            {column_name}->>{sample_key} as value
                        FROM 
                            {table_name}
                        WHERE 
                            {column_name} IS NOT NULL
                        LIMIT 10
                    """
                },
                {
                    "name": "JSON containment (@>)",
                    "sql": f"""
                        SELECT 
                            id, 
                            {column_name}
                        FROM 
                            {table_name}
                        WHERE 
                            {column_name} @> '{{{sample_key}: "{sample_value}"}}'::jsonb
                        LIMIT 10
                    """
                },
                {
                    "name": "JSON existence (?)",
                    "sql": f"""
                        SELECT 
                            id, 
                            {column_name}
                        FROM 
                            {table_name}
                        WHERE 
                            {column_name} ? '{sample_key}'
                        LIMIT 10
                    """
                },
                {
                    "name": "JSON path match (@?)",
                    "sql": f"""
                        SELECT 
                            id, 
                            {column_name}
                        FROM 
                            {table_name}
                        WHERE 
                            {column_name} @? '$.{sample_key}'
                        LIMIT 10
                    """
                },
                {
                    "name": "JSON path query",
                    "sql": f"""
                        SELECT 
                            id, 
                            jsonb_path_query({column_name}, '$.{sample_key}') as value
                        FROM 
                            {table_name}
                        WHERE 
                            {column_name} IS NOT NULL
                        LIMIT 10
                    """
                }
            ]
            
            # Benchmark each query pattern
            results = []
            for pattern in query_patterns:
                name = pattern["name"]
                sql = pattern["sql"]
                
                execution_times = []
                
                try:
                    # Warm up
                    cursor.execute(sql)
                    cursor.fetchall()
                    
                    # Benchmark
                    for i in range(iterations):
                        start_time = time.time()
                        cursor.execute(sql)
                        cursor.fetchall()
                        end_time = time.time()
                        
                        execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
                        execution_times.append(execution_time)
                    
                    # Calculate statistics
                    avg_time = statistics.mean(execution_times)
                    min_time = min(execution_times)
                    max_time = max(execution_times)
                    median_time = statistics.median(execution_times)
                    p95_time = sorted(execution_times)[int(iterations * 0.95)]
                    
                    results.append({
                        "name": name,
                        "sql": sql,
                        "avg_ms": avg_time,
                        "min_ms": min_time,
                        "max_ms": max_time,
                        "median_ms": median_time,
                        "p95_ms": p95_time
                    })
                    
                    logger.info(f"Query Pattern: {name}")
                    logger.info(f"  Avg: {avg_time:.2f} ms")
                    logger.info(f"  Min: {min_time:.2f} ms")
                    logger.info(f"  Max: {max_time:.2f} ms")
                    logger.info(f"  Median: {median_time:.2f} ms")
                    logger.info(f"  P95: {p95_time:.2f} ms")
                    
                except Exception as e:
                    logger.error(f"Error benchmarking query pattern {name}: {e}")
            
            return results
            
    except Exception as e:
        logger.error(f"Error benchmarking query patterns: {e}")
        return []

def generate_optimized_queries(conn, table_name, column_name):
    """Generate optimized query functions for a JSONB column"""
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Get sample data
            cursor.execute(f"""
                SELECT 
                    {column_name}
                FROM 
                    {table_name}
                WHERE 
                    {column_name} IS NOT NULL
                LIMIT 1
            """)
            
            sample = cursor.fetchone()
            if not sample or not sample[column_name]:
                logger.error(f"No sample data found for {table_name}.{column_name}")
                return []
            
            # Extract structure from the sample
            sample_data = sample[column_name]
            if isinstance(sample_data, str):
                sample_data = json.loads(sample_data)
                
            if not isinstance(sample_data, dict):
                logger.error(f"Sample data is not a dictionary")
                return []
            
            # Generate optimized query functions
            functions = []
            
            # Function for getting a specific key
            for key in sample_data.keys():
                function_name = f"get_{table_name}_{key}"
                
                functions.append({
                    "name": function_name,
                    "description": f"Get {key} from {table_name}",
                    "sql": f"""
                        CREATE OR REPLACE FUNCTION {function_name}(p_id TEXT)
                        RETURNS TEXT AS $$
                        DECLARE
                            result TEXT;
                        BEGIN
                            SELECT {column_name}->>{key}
                            INTO result
                            FROM {table_name}
                            WHERE id = p_id;
                            
                            RETURN result;
                        END;
                        $$ LANGUAGE plpgsql;
                    """
                })
            
            # Function for searching by key value
            for key in sample_data.keys():
                function_name = f"search_{table_name}_by_{key}"
                
                functions.append({
                    "name": function_name,
                    "description": f"Search {table_name} by {key}",
                    "sql": f"""
                        CREATE OR REPLACE FUNCTION {function_name}(p_value TEXT)
                        RETURNS TABLE (
                            id TEXT,
                            data JSONB
                        ) AS $$
                        BEGIN
                            RETURN QUERY
                            SELECT t.id, t.{column_name}
                            FROM {table_name} t
                            WHERE t.{column_name}->>{key} ILIKE '%' || p_value || '%';
                            
                            RETURN;
                        END;
                        $$ LANGUAGE plpgsql;
                    """
                })
            
            # Function for multilingual search (if 'en' and 'ar' keys exist)
            if 'en' in sample_data and 'ar' in sample_data:
                function_name = f"search_{table_name}_multilingual"
                
                functions.append({
                    "name": function_name,
                    "description": f"Search {table_name} in multiple languages",
                    "sql": f"""
                        CREATE OR REPLACE FUNCTION {function_name}(p_value TEXT, p_language TEXT DEFAULT 'en')
                        RETURNS TABLE (
                            id TEXT,
                            name TEXT,
                            data JSONB
                        ) AS $$
                        BEGIN
                            RETURN QUERY
                            SELECT t.id, t.{column_name}->p_language AS name, t.{column_name}
                            FROM {table_name} t
                            WHERE t.{column_name}->p_language ILIKE '%' || p_value || '%';
                            
                            RETURN;
                        END;
                        $$ LANGUAGE plpgsql;
                    """
                })
            
            return functions
            
    except Exception as e:
        logger.error(f"Error generating optimized queries: {e}")
        return []

def generate_recommendations(analysis_results, benchmark_results):
    """Generate recommendations for JSONB usage"""
    recommendations = []
    
    # Check for missing indexes
    for analysis in analysis_results:
        table_name = analysis["table_name"]
        column_name = analysis["column_name"]
        indexes = analysis["indexes"]
        structure = analysis["structure"]
        row_count = analysis["row_count"]
        
        # Check if GIN index exists
        has_gin_index = any("gin" in index["indexdef"].lower() for index in indexes)
        
        if not has_gin_index and row_count > 100:
            recommendations.append({
                "type": "index",
                "priority": "high",
                "description": f"Add GIN index to {table_name}.{column_name}",
                "sql": f"""
                    CREATE INDEX idx_{table_name}_{column_name}_gin ON {table_name} USING GIN ({column_name});
                """
            })
        
        # Check for common keys that might benefit from expression indexes
        for key, count in structure.items():
            if count > row_count * 0.5:  # Key appears in more than 50% of rows
                recommendations.append({
                    "type": "index",
                    "priority": "medium",
                    "description": f"Add expression index for {table_name}.{column_name}->{key}",
                    "sql": f"""
                        CREATE INDEX idx_{table_name}_{column_name}_{key} ON {table_name} (({column_name}->'{key}'));
                    """
                })
    
    # Recommendations based on benchmark results
    if benchmark_results:
        # Find the fastest query pattern
        fastest = min(benchmark_results, key=lambda x: x["avg_ms"])
        slowest = max(benchmark_results, key=lambda x: x["avg_ms"])
        
        recommendations.append({
            "type": "query",
            "priority": "high",
            "description": f"Use {fastest['name']} pattern for best performance",
            "details": f"Average: {fastest['avg_ms']:.2f} ms, compared to {slowest['name']} at {slowest['avg_ms']:.2f} ms",
            "example": fastest["sql"]
        })
        
        # Check for slow patterns
        for result in benchmark_results:
            if result["avg_ms"] > 5.0:  # Arbitrary threshold
                recommendations.append({
                    "type": "query",
                    "priority": "medium",
                    "description": f"Avoid {result['name']} pattern for large result sets",
                    "details": f"Average: {result['avg_ms']:.2f} ms",
                    "example": result["sql"]
                })
    
    return recommendations

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="JSONB Query Optimization")
    parser.add_argument("--table", help="Specific table to analyze")
    parser.add_argument("--iterations", type=int, default=50, help="Number of iterations for benchmarking")
    
    args = parser.parse_args()
    
    # Connect to database
    conn = connect_to_database()
    if not conn:
        return 1
    
    try:
        # Analyze JSONB columns
        logger.info("Analyzing JSONB columns...")
        analysis_results = analyze_jsonb_columns(conn)
        
        if not analysis_results:
            logger.info("No JSONB columns to analyze")
            return 0
        
        # Print analysis results
        logger.info("\nJSONB Column Analysis:")
        for analysis in analysis_results:
            table_name = analysis["table_name"]
            column_name = analysis["column_name"]
            indexes = analysis["indexes"]
            structure = analysis["structure"]
            row_count = analysis["row_count"]
            
            logger.info(f"\nTable: {table_name}")
            logger.info(f"Column: {column_name}")
            logger.info(f"Row Count: {row_count}")
            
            logger.info("Indexes:")
            for index in indexes:
                logger.info(f"  - {index['indexname']}: {index['indexdef']}")
            
            logger.info("Structure:")
            for key, count in structure.items():
                percentage = (count / row_count) * 100 if row_count > 0 else 0
                logger.info(f"  - {key}: {count} rows ({percentage:.1f}%)")
        
        # Benchmark query patterns for a specific table or the first table
        benchmark_results = []
        if args.table:
            # Find the specified table
            table_analysis = next((a for a in analysis_results if a["table_name"] == args.table), None)
            if table_analysis:
                logger.info(f"\nBenchmarking query patterns for {args.table}...")
                benchmark_results = benchmark_query_patterns(
                    conn, 
                    table_analysis["table_name"], 
                    table_analysis["column_name"], 
                    args.iterations
                )
            else:
                logger.error(f"Table {args.table} not found or has no JSONB columns")
        else:
            # Use the first table
            logger.info(f"\nBenchmarking query patterns for {analysis_results[0]['table_name']}...")
            benchmark_results = benchmark_query_patterns(
                conn, 
                analysis_results[0]["table_name"], 
                analysis_results[0]["column_name"], 
                args.iterations
            )
        
        # Generate optimized queries
        optimized_queries = []
        for analysis in analysis_results:
            table_name = analysis["table_name"]
            column_name = analysis["column_name"]
            
            if args.table and args.table != table_name:
                continue
                
            logger.info(f"\nGenerating optimized queries for {table_name}.{column_name}...")
            queries = generate_optimized_queries(conn, table_name, column_name)
            optimized_queries.extend(queries)
        
        # Save optimized queries to file
        if optimized_queries:
            with open("optimized_jsonb_queries.sql", "w") as f:
                for query in optimized_queries:
                    f.write(f"-- {query['description']}\n")
                    f.write(f"{query['sql']}\n\n")
            
            logger.info(f"\nSaved {len(optimized_queries)} optimized query functions to optimized_jsonb_queries.sql")
        
        # Generate recommendations
        logger.info("\nGenerating recommendations...")
        recommendations = generate_recommendations(analysis_results, benchmark_results)
        
        # Print recommendations
        logger.info("\nRecommendations:")
        for i, rec in enumerate(recommendations, 1):
            logger.info(f"\n{i}. {rec['description']} (Priority: {rec['priority']})")
            if "details" in rec:
                logger.info(f"   Details: {rec['details']}")
            if "sql" in rec:
                logger.info(f"   SQL: {rec['sql']}")
            if "example" in rec:
                logger.info(f"   Example: {rec['example']}")
        
        # Save recommendations to file
        with open("jsonb_recommendations.json", "w") as f:
            json.dump(recommendations, f, indent=2)
        
        logger.info(f"\nSaved {len(recommendations)} recommendations to jsonb_recommendations.json")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    sys.exit(main())
