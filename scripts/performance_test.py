#!/usr/bin/env python
"""
Performance Testing Script for Egypt Tourism Chatbot

This script conducts comprehensive performance tests to identify bottlenecks:
1. Database query performance (PostgreSQL)
2. Session management performance (Redis)
3. Vector search performance
4. JSONB query performance
5. Concurrent user simulation

Usage:
    python performance_test.py [--test-type TYPE] [--iterations N] [--concurrency N]

Options:
    --test-type TYPE    Type of test to run (db, redis, vector, jsonb, concurrent, all)
    --iterations N      Number of iterations for each test (default: 100)
    --concurrency N     Number of concurrent users to simulate (default: 10)
"""

import os
import sys
import time
import logging
import random
import argparse
import json
import statistics
import concurrent.futures
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import redis
import numpy as np
from pgvector.psycopg2 import register_vector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('performance_test.log')
    ]
)
logger = logging.getLogger(__name__)

# Database connection parameters
DB_NAME = os.environ.get("DB_NAME", "egypt_chatbot")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "postgres")
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
REDIS_URI = os.environ.get("REDIS_URI", "redis://localhost:6379/0")

def get_postgres_uri():
    """Get PostgreSQL connection URI"""
    return f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def connect_to_database():
    """Connect to the PostgreSQL database"""
    try:
        conn = psycopg2.connect(get_postgres_uri())
        conn.autocommit = True
        
        # Register pgvector extension
        register_vector(conn)
        
        logger.info(f"Connected to database: {DB_NAME}")
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        return None

def connect_to_redis():
    """Connect to Redis"""
    try:
        redis_client = redis.from_url(REDIS_URI)
        redis_client.ping()  # Test connection
        logger.info(f"Connected to Redis: {REDIS_URI}")
        return redis_client
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        return None

def test_database_performance(conn, iterations=100):
    """Test database query performance"""
    logger.info(f"Testing database query performance with {iterations} iterations")
    
    # Define test queries
    test_queries = [
        {
            "name": "Simple SELECT",
            "sql": "SELECT id, name FROM cities LIMIT 10"
        },
        {
            "name": "JOIN query",
            "sql": """
                SELECT c.id, c.name, r.name as region_name
                FROM cities c
                JOIN regions r ON c.region_id = r.id
                LIMIT 10
            """
        },
        {
            "name": "Aggregation query",
            "sql": """
                SELECT region_id, COUNT(*) as city_count
                FROM cities
                GROUP BY region_id
            """
        },
        {
            "name": "Complex JOIN",
            "sql": """
                SELECT c.id, c.name, r.name as region_name, 
                       COUNT(a.id) as attraction_count
                FROM cities c
                JOIN regions r ON c.region_id = r.id
                LEFT JOIN attractions a ON a.city_id = c.id
                GROUP BY c.id, c.name, r.name
                LIMIT 10
            """
        },
        {
            "name": "Full-text search",
            "sql": """
                SELECT id, name
                FROM attractions
                WHERE name_en ILIKE '%temple%' OR name_ar ILIKE '%معبد%'
                LIMIT 10
            """
        }
    ]
    
    results = {}
    
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        for query in test_queries:
            query_name = query["name"]
            sql = query["sql"]
            
            execution_times = []
            
            for i in range(iterations):
                start_time = time.time()
                cursor.execute(sql)
                cursor.fetchall()  # Fetch all results
                end_time = time.time()
                
                execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
                execution_times.append(execution_time)
            
            # Calculate statistics
            avg_time = statistics.mean(execution_times)
            min_time = min(execution_times)
            max_time = max(execution_times)
            median_time = statistics.median(execution_times)
            p95_time = sorted(execution_times)[int(iterations * 0.95)]
            
            results[query_name] = {
                "avg_ms": avg_time,
                "min_ms": min_time,
                "max_ms": max_time,
                "median_ms": median_time,
                "p95_ms": p95_time
            }
            
            logger.info(f"Query: {query_name}")
            logger.info(f"  Avg: {avg_time:.2f} ms")
            logger.info(f"  Min: {min_time:.2f} ms")
            logger.info(f"  Max: {max_time:.2f} ms")
            logger.info(f"  Median: {median_time:.2f} ms")
            logger.info(f"  P95: {p95_time:.2f} ms")
    
    return results

def test_jsonb_performance(conn, iterations=100):
    """Test JSONB query performance"""
    logger.info(f"Testing JSONB query performance with {iterations} iterations")
    
    # Define test queries
    test_queries = [
        {
            "name": "JSONB simple access",
            "sql": """
                SELECT id, name->>'en' as name_en
                FROM cities
                LIMIT 10
            """
        },
        {
            "name": "JSONB containment",
            "sql": """
                SELECT id, name
                FROM cities
                WHERE name @> '{"en": "Cairo"}'
                LIMIT 10
            """
        },
        {
            "name": "JSONB path access",
            "sql": """
                SELECT id, name, data->'population' as population
                FROM cities
                WHERE data ? 'population'
                LIMIT 10
            """
        },
        {
            "name": "JSONB GIN index search",
            "sql": """
                SELECT id, name
                FROM cities
                WHERE name @> '{"en": "Cairo"}' OR name @> '{"ar": "القاهرة"}'
                LIMIT 10
            """
        },
        {
            "name": "JSONB complex query",
            "sql": """
                SELECT c.id, c.name->>'en' as name_en, 
                       jsonb_array_length(COALESCE(c.data->'amenities', '[]'::jsonb)) as amenities_count
                FROM cities c
                WHERE c.data ? 'population' AND (c.data->>'population')::int > 10000
                LIMIT 10
            """
        }
    ]
    
    results = {}
    
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        for query in test_queries:
            query_name = query["name"]
            sql = query["sql"]
            
            execution_times = []
            
            for i in range(iterations):
                start_time = time.time()
                try:
                    cursor.execute(sql)
                    cursor.fetchall()  # Fetch all results
                except Exception as e:
                    logger.error(f"Error executing JSONB query {query_name}: {e}")
                    continue
                    
                end_time = time.time()
                
                execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
                execution_times.append(execution_time)
            
            if not execution_times:
                logger.warning(f"No successful executions for query: {query_name}")
                continue
                
            # Calculate statistics
            avg_time = statistics.mean(execution_times)
            min_time = min(execution_times)
            max_time = max(execution_times)
            median_time = statistics.median(execution_times)
            p95_time = sorted(execution_times)[int(len(execution_times) * 0.95)]
            
            results[query_name] = {
                "avg_ms": avg_time,
                "min_ms": min_time,
                "max_ms": max_time,
                "median_ms": median_time,
                "p95_ms": p95_time
            }
            
            logger.info(f"JSONB Query: {query_name}")
            logger.info(f"  Avg: {avg_time:.2f} ms")
            logger.info(f"  Min: {min_time:.2f} ms")
            logger.info(f"  Max: {max_time:.2f} ms")
            logger.info(f"  Median: {median_time:.2f} ms")
            logger.info(f"  P95: {p95_time:.2f} ms")
    
    return results

def test_vector_search_performance(conn, iterations=50):
    """Test vector search performance"""
    logger.info(f"Testing vector search performance with {iterations} iterations")
    
    # Generate a random embedding vector
    def generate_embedding():
        embedding = np.random.normal(0, 1, 1536)
        embedding = embedding / np.linalg.norm(embedding)
        return embedding
    
    results = {}
    
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        # Test different vector search methods
        test_queries = [
            {
                "name": "L2 distance search",
                "sql_template": """
                    SELECT id, name, embedding <-> %s as distance
                    FROM attractions
                    ORDER BY distance
                    LIMIT 5
                """
            },
            {
                "name": "Inner product search",
                "sql_template": """
                    SELECT id, name, embedding <#> %s as distance
                    FROM attractions
                    ORDER BY distance
                    LIMIT 5
                """
            },
            {
                "name": "Cosine distance search",
                "sql_template": """
                    SELECT id, name, 1 - (embedding <=> %s) as similarity
                    FROM attractions
                    ORDER BY similarity DESC
                    LIMIT 5
                """
            }
        ]
        
        for query in test_queries:
            query_name = query["name"]
            sql_template = query["sql_template"]
            
            execution_times = []
            
            for i in range(iterations):
                # Generate a random embedding for each iteration
                embedding = generate_embedding()
                
                start_time = time.time()
                try:
                    cursor.execute(sql_template, (embedding,))
                    cursor.fetchall()  # Fetch all results
                except Exception as e:
                    logger.error(f"Error executing vector search {query_name}: {e}")
                    continue
                    
                end_time = time.time()
                
                execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
                execution_times.append(execution_time)
            
            if not execution_times:
                logger.warning(f"No successful executions for vector search: {query_name}")
                continue
                
            # Calculate statistics
            avg_time = statistics.mean(execution_times)
            min_time = min(execution_times)
            max_time = max(execution_times)
            median_time = statistics.median(execution_times)
            p95_time = sorted(execution_times)[int(len(execution_times) * 0.95)]
            
            results[query_name] = {
                "avg_ms": avg_time,
                "min_ms": min_time,
                "max_ms": max_time,
                "median_ms": median_time,
                "p95_ms": p95_time
            }
            
            logger.info(f"Vector Search: {query_name}")
            logger.info(f"  Avg: {avg_time:.2f} ms")
            logger.info(f"  Min: {min_time:.2f} ms")
            logger.info(f"  Max: {max_time:.2f} ms")
            logger.info(f"  Median: {median_time:.2f} ms")
            logger.info(f"  P95: {p95_time:.2f} ms")
    
    return results

def test_redis_performance(redis_client, iterations=100):
    """Test Redis performance"""
    logger.info(f"Testing Redis performance with {iterations} iterations")
    
    if not redis_client:
        logger.error("Redis client is not available")
        return {}
    
    results = {}
    
    # Test different Redis operations
    test_operations = [
        {
            "name": "SET operation",
            "func": lambda i: redis_client.set(f"test:key:{i}", f"value:{i}")
        },
        {
            "name": "GET operation",
            "func": lambda i: redis_client.get(f"test:key:{i}")
        },
        {
            "name": "HSET operation",
            "func": lambda i: redis_client.hset(f"test:hash:{i}", "field1", f"value:{i}")
        },
        {
            "name": "HGET operation",
            "func": lambda i: redis_client.hget(f"test:hash:{i}", "field1")
        },
        {
            "name": "JSON SET operation",
            "func": lambda i: redis_client.set(f"test:json:{i}", json.dumps({"id": i, "data": f"value:{i}"}))
        },
        {
            "name": "JSON GET operation",
            "func": lambda i: json.loads(redis_client.get(f"test:json:{i}") or "{}")
        }
    ]
    
    for operation in test_operations:
        operation_name = operation["name"]
        func = operation["func"]
        
        execution_times = []
        
        for i in range(iterations):
            start_time = time.time()
            try:
                func(i)
            except Exception as e:
                logger.error(f"Error executing Redis operation {operation_name}: {e}")
                continue
                
            end_time = time.time()
            
            execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
            execution_times.append(execution_time)
        
        if not execution_times:
            logger.warning(f"No successful executions for Redis operation: {operation_name}")
            continue
            
        # Calculate statistics
        avg_time = statistics.mean(execution_times)
        min_time = min(execution_times)
        max_time = max(execution_times)
        median_time = statistics.median(execution_times)
        p95_time = sorted(execution_times)[int(len(execution_times) * 0.95)]
        
        results[operation_name] = {
            "avg_ms": avg_time,
            "min_ms": min_time,
            "max_ms": max_time,
            "median_ms": median_time,
            "p95_ms": p95_time
        }
        
        logger.info(f"Redis Operation: {operation_name}")
        logger.info(f"  Avg: {avg_time:.2f} ms")
        logger.info(f"  Min: {min_time:.2f} ms")
        logger.info(f"  Max: {max_time:.2f} ms")
        logger.info(f"  Median: {median_time:.2f} ms")
        logger.info(f"  P95: {p95_time:.2f} ms")
    
    # Clean up test keys
    redis_client.delete(*[f"test:key:{i}" for i in range(iterations)])
    redis_client.delete(*[f"test:hash:{i}" for i in range(iterations)])
    redis_client.delete(*[f"test:json:{i}" for i in range(iterations)])
    
    return results

def simulate_user_session(conn, redis_client, user_id):
    """Simulate a user session with the chatbot"""
    try:
        # Create a session
        session_id = f"test-session-{user_id}-{int(time.time())}"
        
        # Store session in Redis
        session_data = {
            "user_id": f"test-user-{user_id}",
            "created_at": datetime.now().isoformat(),
            "language": random.choice(["en", "ar"]),
            "messages": []
        }
        
        redis_client.set(f"session:{session_id}", json.dumps(session_data))
        
        # Get random attraction
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT id, name FROM attractions ORDER BY RANDOM() LIMIT 1")
            attraction = cursor.fetchone()
            
            if not attraction:
                logger.error("No attractions found in database")
                return False
            
            attraction_name = json.loads(attraction['name'])['en'] if isinstance(attraction['name'], str) else attraction['name']['en']
            
            # Generate a query
            query = f"Tell me about {attraction_name}"
            
            # Add message to session
            message = {
                "role": "user",
                "content": query,
                "timestamp": datetime.now().isoformat()
            }
            
            session_data["messages"].append(message)
            redis_client.set(f"session:{session_id}", json.dumps(session_data))
            
            # Simulate chatbot processing
            time.sleep(0.1)
            
            # Get attraction details
            cursor.execute("SELECT * FROM attractions WHERE id = %s", (attraction['id'],))
            attraction_details = cursor.fetchone()
            
            # Generate response
            response = f"Here's information about {attraction_name}: "
            if attraction_details:
                description = json.loads(attraction_details['description'])['en'] if isinstance(attraction_details['description'], str) else attraction_details['description']['en']
                response += description
            else:
                response += "This is a popular attraction in Egypt."
            
            # Add response to session
            message = {
                "role": "assistant",
                "content": response,
                "timestamp": datetime.now().isoformat()
            }
            
            session_data["messages"].append(message)
            redis_client.set(f"session:{session_id}", json.dumps(session_data))
            
            # Clean up
            redis_client.delete(f"session:{session_id}")
            
            return True
    except Exception as e:
        logger.error(f"Error simulating user session: {e}")
        return False

def test_concurrent_users(conn, redis_client, concurrency=10):
    """Test performance with concurrent users"""
    logger.info(f"Testing performance with {concurrency} concurrent users")
    
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(simulate_user_session, conn, redis_client, i) for i in range(concurrency)]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    end_time = time.time()
    
    total_time = end_time - start_time
    successful = results.count(True)
    failed = results.count(False)
    
    logger.info(f"Concurrent Users Test Results:")
    logger.info(f"  Total Time: {total_time:.2f} seconds")
    logger.info(f"  Successful Sessions: {successful}")
    logger.info(f"  Failed Sessions: {failed}")
    logger.info(f"  Throughput: {successful / total_time:.2f} sessions/second")
    
    return {
        "total_time_seconds": total_time,
        "successful_sessions": successful,
        "failed_sessions": failed,
        "throughput_sessions_per_second": successful / total_time if total_time > 0 else 0
    }

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Performance Testing for Egypt Tourism Chatbot")
    parser.add_argument("--test-type", choices=["db", "redis", "vector", "jsonb", "concurrent", "all"], 
                        default="all", help="Type of test to run")
    parser.add_argument("--iterations", type=int, default=100, help="Number of iterations for each test")
    parser.add_argument("--concurrency", type=int, default=10, help="Number of concurrent users to simulate")
    
    args = parser.parse_args()
    
    logger.info(f"Starting performance tests with {args.iterations} iterations and {args.concurrency} concurrent users")
    
    # Connect to database and Redis
    conn = connect_to_database()
    redis_client = connect_to_redis()
    
    if not conn:
        logger.error("Failed to connect to database")
        return 1
    
    results = {}
    
    try:
        # Run selected tests
        if args.test_type in ["db", "all"]:
            results["database"] = test_database_performance(conn, args.iterations)
        
        if args.test_type in ["jsonb", "all"]:
            results["jsonb"] = test_jsonb_performance(conn, args.iterations)
        
        if args.test_type in ["vector", "all"]:
            results["vector"] = test_vector_search_performance(conn, args.iterations)
        
        if args.test_type in ["redis", "all"] and redis_client:
            results["redis"] = test_redis_performance(redis_client, args.iterations)
        
        if args.test_type in ["concurrent", "all"] and redis_client:
            results["concurrent"] = test_concurrent_users(conn, redis_client, args.concurrency)
        
        # Save results to file
        with open("performance_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        logger.info("Performance tests completed successfully")
        logger.info(f"Results saved to performance_results.json")
        
        return 0
    except Exception as e:
        logger.error(f"Error during performance tests: {e}")
        return 1
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    sys.exit(main())
