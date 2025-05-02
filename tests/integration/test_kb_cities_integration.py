"""
Integration tests for city-related functionality in the KnowledgeBase.
Tests the interaction between KnowledgeBase and DatabaseManager with a real database.
"""
import pytest
import os
import json

from datetime import datetime, timezone
from src.knowledge.knowledge_base import KnowledgeBase
from src.knowledge.database import DatabaseManager

pytestmark = pytest.mark.skipif(
    not hasattr(DatabaseManager(), 'connection') or DatabaseManager().connection is None,
    reason="Skipping SQLite-specific tests when DatabaseManager is not using SQLite."
)


@pytest.fixture
def test_db_path(tmpdir):
    """Create a temporary database file path for testing."""
    return os.path.join(tmpdir, "test_kb_cities.db")


@pytest.fixture
def initialized_db_manager(test_db_path):
    """Create and initialize a DatabaseManager with test data."""
    # Use the default DatabaseManager (now PostgreSQL-only)
    db_manager = DatabaseManager()
    # Create test cities using the appropriate DB interface
    cursor = db_manager.connection.cursor()
    
    # Create some test cities
    # NOTE: If using PostgreSQL, ensure the cities table exists and is empty before inserting.
    test_cities = [
        {
            "id": "cairo",
            "name": json.dumps({"en": "Cairo", "ar": "القاهرة"}),
            "description": json.dumps({"en": "Capital of Egypt", "ar": "عاصمة مصر"}),
            "region_id": None,
            "population": 9500000,
            "location": json.dumps({"latitude": 30.0444, "longitude": 31.2357}),
            "images": json.dumps([]),
            "known_for": json.dumps(["Pyramids", "Egyptian Museum"]),
            "best_time_to_visit": None,
            "data": json.dumps({"founded": "969 AD"}),
            "embedding": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "alexandria",
            "name": json.dumps({"en": "Alexandria", "ar": "الإسكندرية"}),
            "description": json.dumps({"en": "Coastal city in Egypt", "ar": "مدينة ساحلية في مصر"}),
            "region_id": None,
            "population": 5200000,
            "location": json.dumps({"latitude": 31.2001, "longitude": 29.9187}),
            "images": json.dumps([]),
            "known_for": json.dumps(["Bibliotheca Alexandrina", "Citadel of Qaitbay"]),
            "best_time_to_visit": None,
            "data": json.dumps({"founded": "331 BC"}),
            "embedding": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "luxor",
            "name": json.dumps({"en": "Luxor", "ar": "الأقصر"}),
            "description": json.dumps({"en": "Historical city in Egypt", "ar": "مدينة تاريخية في مصر"}),
            "region_id": None,
            "population": 500000,
            "location": json.dumps({"latitude": 25.6872, "longitude": 32.6396}),
            "images": json.dumps([]),
            "known_for": json.dumps(["Karnak Temple", "Valley of the Kings"]),
            "best_time_to_visit": None,
            "data": json.dumps({"founded": "Ancient times"}),
            "embedding": None,
            "longitude": 32.6396,
            "data": json.dumps({
                "population": 500000,
                "founded": "Ancient times",
                "landmarks": ["Karnak Temple", "Valley of the Kings"]
            }),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    # Insert test cities
    for city in test_cities:
        cursor.execute('''
            INSERT INTO cities (
                id, name_en, name_ar, country, city_type, latitude, longitude,
                data, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            city["id"], city["name_en"], city["name_ar"], city["country"],
            city["city_type"], city["latitude"], city["longitude"],
            city["data"], city["created_at"], city["updated_at"]
        ))
    
    # Commit changes
    db_manager.connection.commit()
    
    return db_manager


@pytest.fixture
def knowledge_base(initialized_db_manager):
    """Create a KnowledgeBase instance with the initialized DatabaseManager."""
    return KnowledgeBase(db_manager=initialized_db_manager)


def test_get_city_by_id_integration(knowledge_base):
    """Test retrieving a city by ID using the actual database."""
    city = knowledge_base.get_record_by_id("cities", "cairo")
    
    assert city is not None
    assert city["id"] == "cairo"
    import json
    name = json.loads(city["name"])
    assert name["en"] == "Cairo"
    # Check location JSON
    location = json.loads(city["location"])
    assert abs(location["latitude"] - 30.0444) < 1e-4
    assert abs(location["longitude"] - 31.2357) < 1e-4


def test_search_cities_by_name_integration(knowledge_base):
    """Test searching cities by name using the actual database."""
    results = knowledge_base.search_records("cities", {"name": "alex"}, limit=10)
    
    assert len(results) == 1
    assert results[0]["id"] == "alexandria"
    import json
    name = json.loads(results[0]["name"])
    assert name["en"] == "Alexandria"


def test_search_cities_all_integration(knowledge_base):
    """Test retrieving all cities using the actual database."""
    results = knowledge_base.search_records("cities", {}, limit=10)
    
    assert len(results) == 3
    # Results should contain Cairo, Alexandria, and Luxor
    # Check that all expected cities are present by name (normalized schema)
    import json
    city_names = [json.loads(city["name"])['en'] for city in results]
    assert "Cairo" in city_names
    assert "Alexandria" in city_names
    assert "Luxor" in city_names


def test_search_cities_by_type_integration(knowledge_base):
    """Test searching cities by type using the actual database."""
    # Use a filter on 'description' or 'data' for type, since 'city_type' is not in the normalized schema
    import json
    results = knowledge_base.search_records("cities", {"description": "Historical"}, limit=10)
    assert any(json.loads(city["name"])['en'] == "Luxor" for city in results)
    # If you want to be strict about count:
    luxor_cities = [city for city in results if json.loads(city["name"])["en"] == "Luxor"]
    assert len(luxor_cities) == 1


def test_search_cities_pagination_integration(knowledge_base):
    """Test pagination when searching cities using the actual database."""
    # Get first page (1 result)
    page1 = knowledge_base.search_records("cities", {}, limit=1, offset=0)
    # Get second page (1 result)
    page2 = knowledge_base.search_records("cities", {}, limit=1, offset=1)
    # Get third page (1 result)
    page3 = knowledge_base.search_records("cities", {}, limit=1, offset=2)
    
    assert len(page1) == 1
    assert len(page2) == 1
    assert len(page3) == 1
    
    # All three pages should have different city names (normalized schema)
    import json
    names = [json.loads(page[0]["name"])['en'] for page in [page1, page2, page3]]
    assert len(set(names)) == 3
    assert set(names) == {"Cairo", "Alexandria", "Luxor"}
    assert page1[0]["id"] != page3[0]["id"] 