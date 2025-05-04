"""
Pytest configuration file for Egypt Tourism Chatbot tests.
"""

import os
import json
import pytest
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock
from .setup_test_env import setup_test_environment, cleanup_test_environment
from fastapi.testclient import TestClient
import secrets
import jwt
from datetime import datetime, timedelta, timezone
import psycopg2
from psycopg2.extras import RealDictCursor

# Import DatabaseManager for fixture
from src.knowledge.database import DatabaseManager

# Global variable to store temporary directory
_TEMP_TEST_DIR = None

def pytest_sessionstart(session):
    """
    Called before test session starts.
    Set up the global test environment.
    """
    global _TEMP_TEST_DIR
    _TEMP_TEST_DIR = setup_test_environment()

    # Save the test directory path to a temp file for reference
    with open(".test_dir_path", "w") as f:
        f.write(_TEMP_TEST_DIR)

    print(f"\nTest environment set up in: {_TEMP_TEST_DIR}\n")

def pytest_sessionfinish(session, exitstatus):
    """
    Called after whole test run finished.
    Clean up the test environment.
    """
    global _TEMP_TEST_DIR
    if _TEMP_TEST_DIR:
        cleanup_test_environment(_TEMP_TEST_DIR)
        _TEMP_TEST_DIR = None

        # Remove the temp file
        if os.path.exists(".test_dir_path"):
            os.unlink(".test_dir_path")

    print("\nTest environment cleaned up.\n")

@pytest.fixture
def test_temp_dir():
    """
    Fixture to provide test directory path to tests.
    """
    global _TEMP_TEST_DIR
    return _TEMP_TEST_DIR

@pytest.fixture
def mock_env_vars():
    """
    Fixture to provide access to the test environment variables.
    """
    env_vars = {
        "CONTENT_PATH": os.environ.get("CONTENT_PATH"),
        "DATABASE_URI": os.environ.get("DATABASE_URI"),
        "SESSION_STORAGE_URI": os.environ.get("SESSION_STORAGE_URI"),
        "VECTOR_DB_URI": os.environ.get("VECTOR_DB_URI"),
        "JWT_SECRET": "***", # Hidden for security
        "API_HOST": os.environ.get("API_HOST"),
        "API_PORT": os.environ.get("API_PORT"),
        "FRONTEND_URL": os.environ.get("FRONTEND_URL"),
        "USE_NEW_KB": os.environ.get("USE_NEW_KB"),
        "USE_NEW_API": os.environ.get("USE_NEW_API"),
        "USE_POSTGRES": os.environ.get("USE_POSTGRES"),
        "USE_REDIS": os.environ.get("USE_REDIS"),
    }
    return env_vars

# --- Mock Redis for all tests ---
@pytest.fixture(scope="session", autouse=True)
def mock_redis():
    """
    Mock Redis for all tests to prevent any real Redis connections.
    This ensures tests don't rely on external Redis service.
    """
    mock_redis_client = AsyncMock()
    mock_redis_client.ping.return_value = True
    mock_redis_client.close.return_value = None

    # Create a from_url mock that returns our mock client
    async def mock_from_url(*args, **kwargs):
        return mock_redis_client

    # Patch redis.asyncio.from_url
    with patch('redis.asyncio.from_url', mock_from_url):
        # Patch FastAPILimiter.init to be a no-op
        with patch('fastapi_limiter.FastAPILimiter.init', AsyncMock(return_value=None)):
            yield mock_redis_client

# --- Add FastAPI App and Async Client Fixtures ---

@pytest.fixture
def app():
    """Fixture to provide the FastAPI app instance."""
    # Ensure dependencies are loaded *after* test environment setup if needed
    from src.main import app as fastapi_app # Use alias
    return fastapi_app

@pytest.fixture
def client(app):
    """Provides a FastAPI TestClient instance."""
    with TestClient(app) as test_client:
        yield test_client

# --- Minimal App Fixtures for Debugging --- #
from fastapi import FastAPI as MinimalFastAPI # Use alias to avoid confusion

@pytest.fixture
def minimal_app():
    """A minimal FastAPI app for basic fixture testing."""
    app = MinimalFastAPI()
    @app.get("/ping")
    async def _minimal_ping():
        return {"ping": "pong"}
    return app

import pytest_asyncio

@pytest_asyncio.fixture
async def minimal_client(minimal_app):
    """Async client for the minimal FastAPI app."""
    from httpx import AsyncClient
    async with AsyncClient(base_url="http://test") as client:
        yield client

@pytest.fixture
def test_auth_token():
    """Generate a test auth token for authentication."""
    # Generate a simple session token for testing
    return secrets.token_hex(16)

@pytest.fixture
def mock_session_validate():
    """Mock session validation to return test user data."""
    async def mock_validate(*args, **kwargs):
        # Return test user data for all validation attempts
        return {
            "user_id": "test_user_1",
            "username": "testuser",
            "email": "test@example.com",
            "role": "user",
            "created_at": datetime.now(timezone.utc).isoformat()
        }

    # Patch the session validation
    with patch("src.services.session.SessionService.validate_session", mock_validate):
        yield

@pytest.fixture
def authenticated_client(app, test_auth_token, mock_session_validate):
    """Provides a FastAPI TestClient that is pre-authenticated."""
    with TestClient(app) as test_client:
        # Set the session_token cookie
        test_client.cookies.set("session_token", test_auth_token)
        # Also set it as a Bearer token in default headers
        test_client.headers["Authorization"] = f"Bearer {test_auth_token}"
        yield test_client

@pytest_asyncio.fixture
async def initialized_db_manager():
    """Fixture that provides a DatabaseManager with properly initialized tables."""
    # Use PostgreSQL for tests
    db_uri = os.environ.get("POSTGRES_URI") or "postgresql://postgres:postgres@localhost:5432/egypt_chatbot_test"

    # Create a new database manager instance
    db_manager = DatabaseManager(database_uri=db_uri)

    # Ensure tables are created with the correct schema
    # This will use the schema defined in setup_test_env.py
    try:
        # Get connection from the pool
        conn = db_manager._get_pg_connection()

        # First verify that the tables exist with the expected schema
        with conn:
            with conn.cursor() as cursor:
                # Check if tables exist
                tables = ["users", "cities", "attractions", "restaurants", "accommodations", "regions"]
                for table in tables:
                    cursor.execute(f"SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = '{table}')")
                    if not cursor.fetchone()[0]:
                        # If table doesn't exist, we need to initialize the schema
                        from tests.setup_test_env import initialize_postgres_test_schema
                        initialize_postgres_test_schema()
                        break

        # Now insert test data
        with conn:
            with conn.cursor() as cursor:
                # Clean up any existing test data to avoid conflicts
                cursor.execute("DELETE FROM restaurants WHERE id = %s", ("test_restaurant_1",))
                cursor.execute("DELETE FROM accommodations WHERE id = %s", ("test_hotel_1",))
                cursor.execute("DELETE FROM attractions WHERE id = %s", ("test_attraction_1",))
                cursor.execute("DELETE FROM cities WHERE id = %s", ("test_city_1",))

                # Insert test restaurant
                test_restaurant = {
                    "id": "test_restaurant_1",
                    "name_en": "Test Restaurant",
                    "name_ar": "مطعم اختبار",
                    "cuisine": "Egyptian",
                    "city": "Cairo",
                    "region": "Cairo",
                    "latitude": 30.0444,
                    "longitude": 31.2357,
                    "description_en": "A test restaurant description",
                    "description_ar": "وصف لمطعم اختبار",
                    "data": json.dumps({"price_range": "moderate"}),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }

                cursor.execute("""
                    INSERT INTO restaurants (
                        id, name_en, name_ar, cuisine, city, region, latitude, longitude,
                        description_en, description_ar, data, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    test_restaurant["id"], test_restaurant["name_en"], test_restaurant["name_ar"],
                    test_restaurant["cuisine"], test_restaurant["city"], test_restaurant["region"],
                    test_restaurant["latitude"], test_restaurant["longitude"],
                    test_restaurant["description_en"], test_restaurant["description_ar"],
                    test_restaurant["data"], test_restaurant["created_at"], test_restaurant["updated_at"]
                ))

                # Insert test hotel/accommodation
                test_hotel = {
                    "id": "test_hotel_1",
                    "name_en": "Test Hotel",
                    "name_ar": "فندق اختبار",
                    "type": "hotel",
                    "stars": 4,
                    "city": "Cairo",
                    "region": "Cairo",
                    "latitude": 30.0444,
                    "longitude": 31.2357,
                    "description_en": "A test hotel description",
                    "description_ar": "وصف لفندق اختبار",
                    "data": json.dumps({"amenities": ["wifi", "pool"]}),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }

                cursor.execute("""
                    INSERT INTO accommodations (
                        id, name_en, name_ar, type, city, region, latitude, longitude,
                        description_en, description_ar, data, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    test_hotel["id"], test_hotel["name_en"], test_hotel["name_ar"],
                    test_hotel["type"], test_hotel["city"], test_hotel["region"],
                    test_hotel["latitude"], test_hotel["longitude"],
                    test_hotel["description_en"], test_hotel["description_ar"],
                    test_hotel["data"], test_hotel["created_at"], test_hotel["updated_at"]
                ))

                # Insert test attraction
                test_attraction = {
                    "id": "test_attraction_1",
                    "name_en": "Test Attraction",
                    "name_ar": "معلم اختبار",
                    "type": "monument",
                    "city": "Cairo",
                    "region": "Cairo",
                    "latitude": 30.0444,
                    "longitude": 31.2357,
                    "description_en": "A test attraction description",
                    "description_ar": "وصف لمعلم اختبار",
                    "data": json.dumps({"entry_fee": "100 EGP", "rating": 4.8}),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }

                cursor.execute("""
                    INSERT INTO attractions (
                        id, name_en, name_ar, type, city, region, latitude, longitude,
                        description_en, description_ar, data, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    test_attraction["id"], test_attraction["name_en"], test_attraction["name_ar"],
                    test_attraction["type"], test_attraction["city"], test_attraction["region"],
                    test_attraction["latitude"], test_attraction["longitude"],
                    test_attraction["description_en"], test_attraction["description_ar"],
                    test_attraction["data"], test_attraction["created_at"], test_attraction["updated_at"]
                ))

                # Insert test city
                test_city = {
                    "id": "test_city_1",
                    "name_en": "Test City",
                    "name_ar": "مدينة اختبار",
                    "region": "Test Region",
                    "latitude": 30.0444,
                    "longitude": 31.2357,
                    "data": json.dumps({"population": 1000000, "attractions": ["test_attraction_1"]}),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }

                cursor.execute("""
                    INSERT INTO cities (
                        id, name_en, name_ar, region, latitude, longitude,
                        data, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    test_city["id"], test_city["name_en"], test_city["name_ar"],
                    test_city["region"], test_city["latitude"], test_city["longitude"],
                    test_city["data"], test_city["created_at"], test_city["updated_at"]
                ))

                # Update geospatial data
                if db_manager._check_postgis_enabled():
                    for table in ["cities", "attractions", "restaurants", "accommodations"]:
                        cursor.execute(f"""
                            UPDATE {table} SET geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
                            WHERE geom IS NULL AND latitude IS NOT NULL AND longitude IS NOT NULL
                        """)

                conn.commit()

        # Return connection to pool
        db_manager._return_pg_connection(conn)

        yield db_manager
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error in initialized_db_manager fixture: {str(e)}")
        raise
    finally:
        # Ensure connection is closed properly
        await db_manager.close() if hasattr(db_manager.close, '__await__') else db_manager.close()

@pytest_asyncio.fixture
async def test_knowledge_base(initialized_db_manager):
    """Fixture that provides a KnowledgeBase with test data."""
    from src.knowledge.knowledge_base import KnowledgeBase
    kb = KnowledgeBase(db_manager=initialized_db_manager)
    return kb

@pytest.fixture
def query_data():
    """Test query data fixture for KB integration tests."""
    return {
        "name": "Egyptian Museum query",
        "message": "information about the Egyptian Museum",
        "language": "en",
        "expected_keywords": ["museum", "Cairo", "artifacts", "collection"]
    }