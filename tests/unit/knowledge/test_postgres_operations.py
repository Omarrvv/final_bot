import pytest
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import logging
from datetime import datetime

from src.knowledge.database import DatabaseManager, DatabaseType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Fixture for test database connection
@pytest.fixture
def pg_test_db():
    """Create isolated test database connection with real PostgreSQL"""
    uri = os.environ.get("POSTGRES_URI") or "postgresql://omarmohamed@localhost:5432/postgres"
    logger.info(f"Testing PostgreSQL connection to: {uri}")
    
    try:
        conn = psycopg2.connect(uri)
        conn.autocommit = True
        
        # Create test schema
        with conn.cursor() as cur:
            cur.execute("CREATE SCHEMA IF NOT EXISTS test_schema")
            
        yield conn
        
        # Cleanup test schema
        with conn.cursor() as cur:
            cur.execute("DROP SCHEMA IF EXISTS test_schema CASCADE")
        conn.close()
        
    except Exception as e:
        logger.error(f"Failed to connect to PostgreSQL: {e}")
        pytest.skip(f"PostgreSQL connection failed: {e}")

# Fixture for DatabaseManager with PostgreSQL
@pytest.fixture
def db_manager():
    """Create DatabaseManager configured for PostgreSQL"""
    # Force PostgreSQL usage regardless of environment variable
    original_testing = os.environ.get("TESTING")
    
    # Make sure the TESTING environment variable doesn't override our database choice
    if "TESTING" in os.environ:
        del os.environ["TESTING"]
    
    os.environ["USE_POSTGRES"] = "true"
    os.environ["POSTGRES_URI"] = os.environ.get("POSTGRES_URI") or "postgresql://omarmohamed@localhost:5432/postgres"
    
    # Create manager with proper constructor signature
    manager = DatabaseManager()
    
    # Ensure we're using PostgreSQL
    assert manager.db_type == DatabaseType.POSTGRES
    assert manager.pg_pool is not None
    
    yield manager
    
    # Clean up test data
    if manager.pg_pool:
        with manager.pg_pool.getconn() as conn:
            with conn.cursor() as cur:
                tables = ["attractions", "restaurants", "hotels", "accommodations"]
                for table in tables:
                    try:
                        cur.execute(f"DELETE FROM {table} WHERE id LIKE 'test_%'")
                    except Exception as e:
                        # Table might not exist, that's OK
                        pass
            conn.commit()
        manager.pg_pool.putconn(conn)
    
    # Restore original testing environment
    if original_testing is not None:
        os.environ["TESTING"] = original_testing
    elif "TESTING" in os.environ:
        del os.environ["TESTING"]

def test_postgres_connection_pool(db_manager):
    """Test that the PostgreSQL connection pool is properly initialized"""
    assert db_manager.db_type == DatabaseType.POSTGRES
    assert db_manager.pg_pool is not None
    
    # Test pool checkout
    conn = db_manager.pg_pool.getconn()
    assert conn is not None
    
    try:
        # Verify connection works with a simple query
        with conn.cursor() as cur:
            cur.execute("SELECT 1 as test")
            result = cur.fetchone()
            assert result[0] == 1
        
        # Create a temporary table for testing
        with conn.cursor() as cur:
            cur.execute("""
            CREATE TEMPORARY TABLE connection_test (
                id SERIAL PRIMARY KEY,
                test_value TEXT
            )
            """)
            
            # Insert some data
            cur.execute("INSERT INTO connection_test (test_value) VALUES (%s)", ("test1",))
            cur.execute("INSERT INTO connection_test (test_value) VALUES (%s)", ("test2",))
            
            # Verify data is visible
            cur.execute("SELECT COUNT(*) FROM connection_test")
            count = cur.fetchone()[0]
            assert count == 2
        
        # Test multiple operations in the same connection
        with conn.cursor() as cur:
            # More inserts
            cur.execute("INSERT INTO connection_test (test_value) VALUES (%s)", ("test3",))
            cur.execute("INSERT INTO connection_test (test_value) VALUES (%s)", ("test4",))
            
            # Read back
            cur.execute("SELECT COUNT(*) FROM connection_test")
            count = cur.fetchone()[0]
            assert count == 4
            
            # Query with conditions 
            cur.execute("SELECT * FROM connection_test WHERE test_value = %s", ("test3",))
            result = cur.fetchone()
            assert result is not None
            assert result[1] == "test3"
    finally:
        # Return connection to pool
        db_manager.pg_pool.putconn(conn)

def test_postgres_attraction_crud(db_manager):
    """Test Create, Read, Update, Delete operations for attractions in PostgreSQL"""
    # Generate a unique test ID
    test_id = f"test_attraction_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Get a direct connection from the pool
    conn = db_manager.pg_pool.getconn()
    
    try:
        # CREATE - Insert a test attraction
        with conn.cursor() as cur:
            insert_sql = """
            INSERT INTO attractions (
                id, name_en, name_ar, type, 
                latitude, longitude, data
            ) VALUES (
                %s, %s, %s, %s, 
                %s, %s, %s
            )
            """
            test_data = {
                "description_en": "Test description",
                "description_ar": "وصف الاختبار",
                "ticket_price": {"adult": 150, "child": 75}
            }
            params = (
                test_id,
                "Test Attraction",
                "اختبار المعلم",
                "historical",
                30.0444,
                31.2357,
                json.dumps(test_data)
            )
            cur.execute(insert_sql, params)
            conn.commit()
        
        # READ - Retrieve the attraction
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            select_sql = "SELECT * FROM attractions WHERE id = %s"
            cur.execute(select_sql, (test_id,))
            attraction = cur.fetchone()
            
            # Verify data
            assert attraction is not None
            assert attraction["name_en"] == "Test Attraction"
            assert attraction["type"] == "historical"
            assert attraction["latitude"] == 30.0444
            assert attraction["longitude"] == 31.2357
            
            # Check JSON data - data might be returned as a string or as a dict
            data = attraction["data"]
            if isinstance(data, str):
                data = json.loads(data)
            assert data["description_en"] == "Test description"
            assert data["ticket_price"]["adult"] == 150
        
        # UPDATE - Modify the attraction
        with conn.cursor() as cur:
            update_sql = """
            UPDATE attractions 
            SET name_en = %s, data = %s
            WHERE id = %s
            """
            updated_data = {
                "description_en": "Updated description",
                "description_ar": "وصف الاختبار المحدث",
                "ticket_price": {"adult": 200, "child": 100}
            }
            cur.execute(update_sql, ("Updated Test Attraction", json.dumps(updated_data), test_id))
            conn.commit()
        
        # READ AGAIN - Verify update
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(select_sql, (test_id,))
            updated_attraction = cur.fetchone()
            
            # Verify updated data
            assert updated_attraction["name_en"] == "Updated Test Attraction"
            
            # Check updated JSON data - data might be returned as a string or as a dict
            updated_data_from_db = updated_attraction["data"]
            if isinstance(updated_data_from_db, str):
                updated_data_from_db = json.loads(updated_data_from_db)
            assert updated_data_from_db["description_en"] == "Updated description"
            assert updated_data_from_db["ticket_price"]["adult"] == 200
        
        # DELETE - Remove the attraction
        with conn.cursor() as cur:
            delete_sql = "DELETE FROM attractions WHERE id = %s"
            cur.execute(delete_sql, (test_id,))
            conn.commit()
        
        # Verify deletion
        with conn.cursor() as cur:
            cur.execute(select_sql, (test_id,))
            deleted_check = cur.fetchone()
            assert deleted_check is None
            
    finally:
        # Always return the connection to the pool
        db_manager.pg_pool.putconn(conn)

def test_postgres_attraction_search(db_manager):
    """Test search functionality for attractions in PostgreSQL"""
    # Create test attractions
    test_attractions = []
    
    # Get a direct connection from the pool
    conn = db_manager.pg_pool.getconn()
    
    try:
        # Create multiple test attractions with different attributes
        for i in range(3):
            test_id = f"test_attraction_search_{i}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            test_attractions.append(test_id)
            
            # Insert test attraction
            with conn.cursor() as cur:
                insert_sql = """
                INSERT INTO attractions (
                    id, name_en, name_ar, type, 
                    latitude, longitude, data
                ) VALUES (
                    %s, %s, %s, %s, 
                    %s, %s, %s
                )
                """
                attraction_type = "historical" if i % 2 == 0 else "cultural"
                data = json.dumps({
                    "description_en": f"Test description {i}",
                    "description_ar": f"وصف الاختبار {i}",
                    "ticket_price": {"adult": 100 + i * 50, "child": 50 + i * 25}
                })
                
                params = (
                    test_id,
                    f"Test Attraction {i}",
                    f"اختبار المعلم {i}",
                    attraction_type,
                    30.0444,
                    31.2357,
                    data
                )
                cur.execute(insert_sql, params)
        
        # Commit all inserts at once
        conn.commit()
        
        # Test search by name
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            search_sql = """
            SELECT * FROM attractions 
            WHERE name_en LIKE %s
            """
            cur.execute(search_sql, ("%Test Attraction%",))
            name_results = cur.fetchall()
            
            # Verify search results
            assert len(name_results) >= 3
            for result in name_results:
                assert "Test Attraction" in result["name_en"]
        
        # Test search by type
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            search_sql = """
            SELECT * FROM attractions 
            WHERE type = %s
            """
            cur.execute(search_sql, ("historical",))
            type_results = cur.fetchall()
            
            # Verify search results
            assert len(type_results) >= 1
            for result in type_results:
                assert result["type"] == "historical"
        
    finally:
        # Clean up test data
        with conn.cursor() as cur:
            for test_id in test_attractions:
                delete_sql = "DELETE FROM attractions WHERE id = %s"
                cur.execute(delete_sql, (test_id,))
            conn.commit()
        
        # Return connection to pool
        db_manager.pg_pool.putconn(conn)

def test_postgres_restaurant_operations(db_manager):
    """Test operations specific to restaurants in PostgreSQL"""
    # Create test restaurant with fields that match the database schema
    test_id = f"test_restaurant_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    test_restaurant = {
        "id": test_id,
        "name_en": "Test Restaurant",
        "name_ar": "مطعم اختباري",
        "latitude": 30.0444, 
        "longitude": 31.2357,
        "cuisine": "Egyptian",
        "city": "Cairo",  # Added required fields
        "region": "Cairo",  # Added required fields
        "data": json.dumps({
            "description_en": "A test restaurant for unit testing",
            "description_ar": "مطعم اختباري للاختبارات",
            "price_range": "moderate",
            "menu_highlights": ["Koshari", "Ful Medames"],
            "type": "restaurant"  # Moved type to data JSON since it's not in schema
        })
    }
    
    # INSERT - using the general method
    insert_result = db_manager.insert_restaurant(test_restaurant)
    assert insert_result is True
    
    # GET - get the restaurant
    restaurant = db_manager.get_restaurant(test_id)
    
    assert restaurant is not None
    assert restaurant["name_en"] == "Test Restaurant"
    assert restaurant["cuisine"] == "Egyptian"
    
    # SEARCH - using the search_restaurants method
    search_results = db_manager.search_restaurants({"cuisine": "Egyptian"})
    
    assert len(search_results) >= 1
    assert any(r["id"] == test_id for r in search_results)
    
    # Clean up - direct SQL for flexibility
    with db_manager.pg_pool.getconn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM restaurants WHERE id = %s", (test_id,))
        conn.commit()
        db_manager.pg_pool.putconn(conn)

def test_postgres_hotel_operations(db_manager):
    """Test operations specific to hotels in PostgreSQL"""
    # Create test hotel
    test_id = f"test_hotel_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Prepare the test data - make sure data is already a JSON string
    hotel_data = {
        "description_en": "A test hotel for unit testing",
        "description_ar": "فندق اختباري للاختبارات",
        "price_range": "luxury",
        "amenities": ["Pool", "Spa", "WiFi"],
        "stars": 4  # Move stars into the data JSON
    }
    
    test_hotel = {
        "id": test_id,
        "name_en": "Test Hotel",
        "name_ar": "فندق اختباري",
        "latitude": 30.0444,
        "longitude": 31.2357,
        "type": "hotel",
        "data": json.dumps(hotel_data)  # Ensure this is a JSON string
    }
    
    # INSERT - use accommodation method
    insert_result = db_manager.insert_accommodation(test_hotel)
    assert insert_result is True
    
    # GET - use get_accommodation method
    hotel = db_manager.get_accommodation(test_id)
    
    assert hotel is not None
    assert hotel["name_en"] == "Test Hotel"
    assert hotel["data"]["stars"] == 4  # Check stars in the data field
    
    # SEARCH - use search_accommodations method with updated field path
    search_results = db_manager.search_accommodations({"type": "hotel"})
    
    assert len(search_results) >= 1
    assert any(r["id"] == test_id for r in search_results)
    
    # Clean up - direct SQL for flexibility
    with db_manager.pg_pool.getconn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM accommodations WHERE id = %s", (test_id,))
        conn.commit()
        db_manager.pg_pool.putconn(conn)

def test_postgres_error_handling(db_manager):
    """Test error handling in PostgreSQL operations"""
    # Test handling of duplicate keys
    test_id = f"test_duplicate_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    test_attraction = {
        "id": test_id,
        "name_en": "Test Duplicate",
        "name_ar": "اختبار مكرر",
        "type": "historical",
        "latitude": 30.0444,
        "longitude": 31.2357,
        "data": json.dumps({"description_en": "Test description"})
    }
    
    # First insert should succeed
    first_result = db_manager.insert_attraction(test_attraction)
    assert first_result is True
    
    # Second insert with same ID should fail gracefully
    second_result = db_manager.insert_attraction(test_attraction)
    assert second_result is False  # Should return False, not raise exception
    
    # Test handling of invalid IDs
    invalid_result = db_manager.get_attraction("nonexistent_id_12345")
    assert invalid_result is None  # Should return None, not raise exception
    
    # Clean up
    db_manager.delete_attraction(test_id)

def test_postgres_transaction_management(db_manager, pg_test_db):
    """Test transaction management in PostgreSQL"""
    test_id = f"test_transaction_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Direct connection for testing transactions
    with pg_test_db.cursor() as cur:
        try:
            # Start transaction (ensure autocommit is False at the beginning)
            pg_test_db.autocommit = False
            
            # Insert test data - using latitude/longitude fields instead of location
            cur.execute(
                "INSERT INTO attractions (id, name_en, name_ar, type, latitude, longitude, data) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (test_id, "Transaction Test", "اختبار المعاملة", "historical", 
                30.0444, 31.2357, 
                json.dumps({"description_en": "Test description"}))
            )
            
            # Check data is visible within transaction
            cur.execute("SELECT * FROM attractions WHERE id = %s", (test_id,))
            in_transaction = cur.fetchone()
            assert in_transaction is not None
            
            # Rollback transaction
            pg_test_db.rollback()
            
            # Verify data is not in database after rollback
            cur.execute("SELECT * FROM attractions WHERE id = %s", (test_id,))
            after_rollback = cur.fetchone()
            assert after_rollback is None
        finally:
            # Create a new connection for any further operations
            # instead of trying to change autocommit on existing connection
            pg_test_db.rollback()  # Make sure any pending transaction is rolled back
            
            # Use a separate connection for autocommit operations if needed
            new_conn = psycopg2.connect(pg_test_db.dsn)
            new_conn.autocommit = True
            new_conn.close()

def test_postgres_connection_pool_stress(db_manager):
    """Test connection pool behavior under moderate load"""
    # Run multiple concurrent operations to test pool
    concurrent_ops = 3  # Adjust based on your pool settings
    
    for i in range(concurrent_ops):
        test_id = f"test_pool_{i}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Get a direct connection from the pool
        conn = db_manager.pg_pool.getconn()
        try:
            # Set autocommit to False for transaction control
            conn.autocommit = False
            
            # Insert test data
            with conn.cursor() as cur:
                insert_sql = """
                INSERT INTO attractions (id, name_en, name_ar, type, data) 
                VALUES (%s, %s, %s, %s, %s)
                """
                params = (
                    test_id,
                    f"Pool Test {i}",
                    f"اختبار التجمع {i}",
                    "historical",
                    json.dumps({"description_en": f"Connection pool test {i}"})
                )
                cur.execute(insert_sql, params)
            
            # Commit the insert transaction
            conn.commit()
            
            # Verify data was inserted
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                select_sql = "SELECT * FROM attractions WHERE id = %s"
                cur.execute(select_sql, (test_id,))
                attraction = cur.fetchone()
                assert attraction is not None
                assert attraction["name_en"] == f"Pool Test {i}"
            
            # Delete the test data
            with conn.cursor() as cur:
                delete_sql = "DELETE FROM attractions WHERE id = %s"
                cur.execute(delete_sql, (test_id,))
            
            # Commit the delete transaction  
            conn.commit()
            
        except Exception as e:
            # Rollback on error
            conn.rollback()
            raise
        finally:
            # Always return connection to the pool
            db_manager.pg_pool.putconn(conn)