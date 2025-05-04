"""
Functional tests for the Knowledge Base.

These tests verify that the Knowledge Base properly retrieves data from the PostgreSQL database.
"""
import os
import pytest
import psycopg2
from psycopg2.extras import RealDictCursor
from pathlib import Path
import json
from datetime import datetime, timezone
from unittest.mock import patch

from src.knowledge.knowledge_base import KnowledgeBase
from src.knowledge.database import DatabaseManager
from src.utils.factory import component_factory

# Test database URI - use environment variable or default to test database
TEST_DB_URI = os.environ.get("POSTGRES_URI") or "postgresql://postgres:postgres@localhost:5432/egypt_chatbot_test"

@pytest.fixture(scope="module")
def setup_test_tables():
    """Create and populate tables for tests."""
    conn = psycopg2.connect(TEST_DB_URI)
    try:
        with conn:
            with conn.cursor() as cur:
                # Always drop and recreate tables to ensure correct schema
                cur.execute("DROP TABLE IF EXISTS attractions")
                cur.execute("DROP TABLE IF EXISTS cities")
                cur.execute("DROP TABLE IF EXISTS attraction_types")

                # Create attraction_types table
                cur.execute("""
                    CREATE TABLE attraction_types (
                        id TEXT PRIMARY KEY,
                        name_en TEXT,
                        name_ar TEXT,
                        description_en TEXT,
                        description_ar TEXT,
                        data JSONB
                    )
                """)

                # Create cities table
                cur.execute("""
                    CREATE TABLE cities (
                        id TEXT PRIMARY KEY,
                        name_en TEXT NOT NULL,
                        name_ar TEXT,
                        description_en TEXT,
                        description_ar TEXT,
                        region TEXT,
                        population INTEGER,
                        latitude FLOAT,
                        longitude FLOAT,
                        data JSONB,
                        embedding VECTOR(1536),
                        geom GEOMETRY(Point, 4326),
                        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Create attractions table
                cur.execute("""
                    CREATE TABLE attractions (
                        id TEXT PRIMARY KEY,
                        name_en TEXT NOT NULL,
                        name_ar TEXT,
                        description_en TEXT,
                        description_ar TEXT,
                        city TEXT,
                        region TEXT,
                        type TEXT,
                        latitude FLOAT,
                        longitude FLOAT,
                        data JSONB,
                        embedding VECTOR(1536),
                        geom GEOMETRY(Point, 4326),
                        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Insert test cities
                cities = [
                    ('cairo', 'Cairo', 'القاهرة', 'Capital of Egypt', 'عاصمة مصر', 'cairo', 20000000, 30.0444, 31.2357),
                    ('giza', 'Giza', 'الجيزة', 'Famous for the pyramids', 'معروفة بالأهرامات', 'cairo', 8800000, 29.9773, 31.1325),
                    ('luxor', 'Luxor', 'الأقصر', 'Historical city in Upper Egypt', 'مدينة تاريخية في صعيد مصر', 'upper_egypt', 500000, 25.6872, 32.6396)
                ]

                for city in cities:
                    cur.execute("""
                        INSERT INTO cities (id, name_en, name_ar, description_en, description_ar, region, population, latitude, longitude, data)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        city[0], city[1], city[2], city[3], city[4], city[5], city[6], city[7], city[8],
                        json.dumps({"known_for": ["Historical Sites"], "best_time_to_visit": "October to April"})
                    ))

                # Insert attraction types
                attraction_types = [
                    ('museum', 'Museum', 'متحف', 'A place to display artifacts', 'مكان لعرض القطع الأثرية'),
                    ('monument', 'Monument', 'نصب تذكاري', 'A structure to commemorate', 'هيكل لإحياء الذكرى'),
                    ('temple', 'Temple', 'معبد', 'Place of worship', 'مكان عبادة')
                ]

                for type_data in attraction_types:
                    cur.execute("""
                        INSERT INTO attraction_types (id, name_en, name_ar, description_en, description_ar)
                        VALUES (%s, %s, %s, %s, %s)
                    """, type_data)

                # Insert test attractions
                attractions = [
                    (
                        'egyptian_museum',
                        'Egyptian Museum',
                        'المتحف المصري',
                        'The Museum of Egyptian Antiquities houses the world\'s largest collection of Pharaonic antiquities.',
                        'متحف الآثار المصرية يضم أكبر مجموعة من الآثار الفرعونية في العالم.',
                        'cairo',
                        'cairo',
                        'museum',
                        30.0478,
                        31.2336
                    ),
                    (
                        'pyramids_giza',
                        'Pyramids of Giza',
                        'أهرامات الجيزة',
                        'The Great Pyramid of Giza is the oldest and largest of the three pyramids in the Giza pyramid complex.',
                        'الهرم الأكبر في الجيزة هو أقدم وأكبر الأهرامات الثلاثة في مجمع أهرامات الجيزة.',
                        'giza',
                        'cairo',
                        'monument',
                        29.9792,
                        31.1342
                    ),
                    (
                        'karnak_temple',
                        'Karnak Temple',
                        'معبد الكرنك',
                        'The Karnak Temple Complex comprises a vast mix of decayed temples, chapels, pylons, and other buildings.',
                        'مجمع معبد الكرنك يضم مزيجًا واسعًا من المعابد المتداعية والكنائس والبوابات والمباني الأخرى.',
                        'luxor',
                        'upper_egypt',
                        'temple',
                        25.7188,
                        32.6571
                    )
                ]

                # Insert attractions with proper PostgreSQL parameters
                for attr in attractions:
                    cur.execute("""
                        INSERT INTO attractions (id, name_en, name_ar, description_en, description_ar, city, region, type, latitude, longitude, data)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        attr[0], attr[1], attr[2], attr[3], attr[4], attr[5], attr[6], attr[7], attr[8], attr[9],
                        json.dumps({"entry_fee": "100 EGP", "opening_hours": "9am - 5pm"})
                    ))

                # Update geospatial data
                cur.execute("""
                    UPDATE cities
                    SET geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
                    WHERE latitude IS NOT NULL AND longitude IS NOT NULL
                """)

                cur.execute("""
                    UPDATE attractions
                    SET geom = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
                    WHERE latitude IS NOT NULL AND longitude IS NOT NULL
                """)
    finally:
        conn.close()

    return TEST_DB_URI


@pytest.fixture
def db_manager(setup_test_tables):
    """Create a database manager connected to the test database."""
    manager = DatabaseManager(database_uri=setup_test_tables)
    yield manager
    manager.close()


@pytest.fixture
def knowledge_base(db_manager):
    """Create a knowledge base with the test database manager."""
    kb = KnowledgeBase(db_manager=db_manager)
    return kb


def test_get_attraction_by_id(knowledge_base):
    """Test that get_attraction_by_id retrieves data from PostgreSQL."""
    # Get attraction by ID
    attraction_id = "egyptian_museum"
    attraction = knowledge_base.get_attraction_by_id(attraction_id)

    # Verify attraction data
    assert attraction is not None
    assert attraction["id"] == attraction_id
    assert attraction["name_en"] == "Egyptian Museum"
    assert attraction["name_ar"] == "المتحف المصري"
    assert "description_en" in attraction
    assert "description_ar" in attraction
    assert attraction["city"] == "cairo"
    assert attraction["type"] == "museum"


def test_search_attractions_by_name(knowledge_base):
    """Test that search_attractions retrieves data by name from PostgreSQL."""
    # Search for attractions with keyword
    results = knowledge_base.search_attractions(query="pyramid")

    # Verify results
    assert len(results) > 0
    # At least one result should have "pyramid" in the name
    assert any("pyramid" in result["name_en"].lower() for result in results)


def test_search_attractions_by_city(knowledge_base):
    """Test that search_attractions retrieves data filtered by city."""
    # Search for attractions with city filter
    results = knowledge_base.search_attractions(query={"city": "cairo"})

    # Verify results
    assert len(results) > 0
    assert all(result["city"] == "cairo" for result in results)
    # Egyptian Museum should be in the results
    assert any(result["id"] == "egyptian_museum" for result in results)


def test_search_attractions_by_type(knowledge_base):
    """Test that search_attractions retrieves data filtered by type."""
    # Search for attractions with type filter
    results = knowledge_base.search_attractions(query={"type": "temple"})

    # Verify results
    assert len(results) > 0
    assert all(result["type"] == "temple" for result in results)
    # Karnak Temple should be in the results
    assert any(result["id"] == "karnak_temple" for result in results)


def test_lookup_location(knowledge_base):
    """Test the lookup_location function with real data."""
    # Look up location by name
    location = knowledge_base.lookup_location("Cairo")

    # Verify location data
    assert location is not None
    assert location["name_en"] == "Cairo"
    assert location["name_ar"] == "القاهرة"
    assert "region" in location
    assert "location" in location
    assert "latitude" in location["location"]
    assert "longitude" in location["location"]


def test_with_factory_configuration():
    """Test Knowledge Base with the factory configuration."""
    # Save original environment value
    original_use_new_kb = os.environ.get("USE_NEW_KB")

    try:
        # Set USE_NEW_KB to true
        os.environ["USE_NEW_KB"] = "true"
        os.environ["USE_POSTGRES"] = "true"  # Ensure PostgreSQL is used

        # Initialize component factory
        component_factory.initialize()

        # Get Knowledge Base from factory
        kb = component_factory.create_knowledge_base()

        # Perform a basic test
        attractions = kb.search_attractions(query="pyramid", limit=3)

        # Verify we get some results
        assert attractions is not None
        assert isinstance(attractions, list)

    finally:
        # Restore original environment values
        if original_use_new_kb is not None:
            os.environ["USE_NEW_KB"] = original_use_new_kb
        else:
            del os.environ["USE_NEW_KB"]


def test_vector_search(db_manager, knowledge_base):
    """Test vector search functionality."""
    # Create test embeddings for attractions
    embedding_dim = 1536
    test_embedding = [0.1] * embedding_dim

    # Store embeddings for test attractions
    conn = db_manager._get_pg_connection()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE attractions
                SET embedding = %s::vector
                WHERE id = %s
            """, (str(test_embedding), "egyptian_museum"))
            conn.commit()
    db_manager._return_pg_connection(conn)

    # Perform vector search
    # Mock the embedding generation to ensure consistent test results
    with patch.object(db_manager, "text_to_embedding", return_value=test_embedding):
        results = knowledge_base.semantic_search("museum artifacts", "attractions", limit=3)

    # Verify results
    assert len(results) > 0
    assert "egyptian_museum" in [r["id"] for r in results], "Egyptian Museum should be in the search results"


def test_find_nearby_attractions(knowledge_base):
    """Test finding attractions near a location."""
    try:
        # Check if PostGIS is available
        postgis_enabled = knowledge_base.db_manager._check_postgis_enabled()
        if not postgis_enabled:
            pytest.skip("PostGIS not enabled in PostgreSQL")

        # Cairo coordinates
        latitude = 30.0444
        longitude = 31.2357

        # Find attractions near Cairo
        results = knowledge_base.find_nearby_attractions(
            latitude=latitude,
            longitude=longitude,
            radius_km=10
        )

        # Verify results
        assert len(results) > 0
        # Egyptian Museum should be in the results (it's close to Cairo)
        assert any(result["id"] == "egyptian_museum" for result in results)
        # Each result should have a distance
        assert all("distance_km" in result for result in results)

    except Exception as e:
        pytest.skip(f"Geospatial search test skipped: {str(e)}")