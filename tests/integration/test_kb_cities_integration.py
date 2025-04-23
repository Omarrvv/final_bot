"""
Integration tests for city-related functionality in the KnowledgeBase.
Tests the interaction between KnowledgeBase and DatabaseManager with a real database.
"""
import pytest
import os
import json
import sqlite3
from datetime import datetime, timezone
from src.knowledge.knowledge_base import KnowledgeBase
from src.knowledge.database import DatabaseManager


@pytest.fixture
def test_db_path(tmpdir):
    """Create a temporary database file path for testing."""
    return os.path.join(tmpdir, "test_kb_cities.db")


@pytest.fixture
def initialized_db_manager(test_db_path):
    """Create and initialize a DatabaseManager with test data."""
    db_uri = f"sqlite:///{test_db_path}"
    db_manager = DatabaseManager(database_uri=db_uri)
    
    # Ensure the tables are created
    db_manager._create_sqlite_tables()
    
    # Create test cities
    cursor = db_manager.connection.cursor()
    
    # Create some test cities
    test_cities = [
        {
            "id": "cairo",
            "name_en": "Cairo",
            "name_ar": "القاهرة",
            "country": "Egypt",
            "city_type": "capital",
            "latitude": 30.0444,
            "longitude": 31.2357,
            "data": json.dumps({
                "population": 9500000,
                "founded": "969 AD",
                "landmarks": ["Pyramids", "Egyptian Museum"]
            }),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "alexandria",
            "name_en": "Alexandria",
            "name_ar": "الإسكندرية",
            "country": "Egypt",
            "city_type": "coastal",
            "latitude": 31.2001,
            "longitude": 29.9187,
            "data": json.dumps({
                "population": 5200000,
                "founded": "331 BC",
                "landmarks": ["Bibliotheca Alexandrina", "Citadel of Qaitbay"]
            }),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "luxor",
            "name_en": "Luxor",
            "name_ar": "الأقصر",
            "country": "Egypt",
            "city_type": "historical",
            "latitude": 25.6872,
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
    assert city["name_en"] == "Cairo"
    assert city["country"] == "Egypt"
    assert city["latitude"] == 30.0444
    assert city["longitude"] == 31.2357


def test_search_cities_by_name_integration(knowledge_base):
    """Test searching cities by name using the actual database."""
    results = knowledge_base.search_records("cities", {"name": "alex"}, limit=10)
    
    assert len(results) == 1
    assert results[0]["id"] == "alexandria"
    assert results[0]["name_en"] == "Alexandria"


def test_search_cities_all_integration(knowledge_base):
    """Test retrieving all cities using the actual database."""
    results = knowledge_base.search_records("cities", {}, limit=10)
    
    assert len(results) == 3
    # Results should contain Cairo, Alexandria, and Luxor
    city_ids = [city["id"] for city in results]
    assert "cairo" in city_ids
    assert "alexandria" in city_ids
    assert "luxor" in city_ids


def test_search_cities_by_type_integration(knowledge_base):
    """Test searching cities by type using the actual database."""
    results = knowledge_base.search_records("cities", {"city_type": "historical"}, limit=10)
    
    assert len(results) == 1
    assert results[0]["id"] == "luxor"
    assert results[0]["name_en"] == "Luxor"


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
    
    # All three pages should have different cities
    assert page1[0]["id"] != page2[0]["id"]
    assert page2[0]["id"] != page3[0]["id"]
    assert page1[0]["id"] != page3[0]["id"] 