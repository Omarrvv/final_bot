import pytest
from unittest.mock import MagicMock, patch
import sqlite3
import os
from src.knowledge.database import DatabaseManager
from src.utils.exceptions import DatabaseError

# Sample data matching the structure returned by cursor methods
# Assuming columns: id, name_en, description_en, city, latitude, longitude, data (as JSON string)
SAMPLE_ATTRACTION_ROW = (
    'attraction_123',      # id
    'Pyramids',            # name_en
    'Ancient wonders',     # description_en
    'Giza',                # city
    29.9792,               # latitude
    31.1342,               # longitude
    '{"rating": 4.5}'      # data (JSON string)
)


@pytest.fixture
def mock_db_connection():
    """Mock database connection and cursor."""
    mock_conn = MagicMock(spec=sqlite3.Connection)
    mock_cursor = MagicMock(spec=sqlite3.Cursor)
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None
    mock_cursor.fetchall.return_value = []
    # Mock description - adjust based on actual queries used in methods
    mock_cursor.description = [
        ('id',), ('name_en',), ('description_en',), ('city',),
        ('latitude',), ('longitude',), ('data',)
    ]
    return mock_conn, mock_cursor


@pytest.fixture
def db_manager(mock_db_connection):
    """Fixture for DatabaseManager instance with mocked connection."""
    mock_conn, mock_cursor = mock_db_connection
    
    # Mock table_exists to return True for required tables
    def mock_table_exists(table_name):
        return True
    
    with patch('sqlite3.connect', return_value=mock_conn) as mock_connect, \
         patch.object(DatabaseManager, '_create_sqlite_tables', return_value=None) as mock_create_tables, \
         patch.object(DatabaseManager, '_table_exists', side_effect=mock_table_exists) as mock_exists, \
         patch('os.makedirs', return_value=None) as mock_makedirs:
        manager = DatabaseManager(database_uri="sqlite:///./dummy_test.db")
        mock_connect.assert_called_once_with("./dummy_test.db")
        mock_create_tables.assert_called_once()
        yield manager

# --- Tests for Existing DatabaseManager Methods ---

def test_get_attraction_found(db_manager, mock_db_connection):
    """Test retrieving an attraction by ID when it exists."""
    mock_conn, mock_cursor = mock_db_connection
    attraction_id = "attraction_123"
    mock_cursor.fetchone.return_value = SAMPLE_ATTRACTION_ROW

    record = db_manager.get_attraction(attraction_id)

    assert record is not None
    assert isinstance(record, dict)
    assert record['id'] == attraction_id
    assert record['name_en'] == 'Pyramids'
    assert record['city'] == 'Giza'
    assert record['data'] == '{"rating": 4.5}' # Data should still be JSON string
    # Verify SQL (adjust if needed based on actual implementation)
    expected_sql = "SELECT id, name_en, description_en, city, latitude, longitude, data FROM attractions WHERE id = ?"
    mock_cursor.execute.assert_called_once_with(expected_sql, (attraction_id,))


def test_get_attraction_not_found(db_manager, mock_db_connection):
    """Test retrieving an attraction by ID when it does not exist."""
    mock_conn, mock_cursor = mock_db_connection
    attraction_id = "non_existent_id"
    mock_cursor.fetchone.return_value = None

    record = db_manager.get_attraction(attraction_id)

    assert record is None
    expected_sql = "SELECT id, name_en, description_en, city, latitude, longitude, data FROM attractions WHERE id = ?"
    mock_cursor.execute.assert_called_once_with(expected_sql, (attraction_id,))


def test_search_attractions_success(db_manager, mock_db_connection):
    """Test searching attractions successfully."""
    mock_conn, mock_cursor = mock_db_connection
    query = {"city": "Giza"}
    limit = 5
    offset = 0
    mock_cursor.fetchall.return_value = [SAMPLE_ATTRACTION_ROW]
    
    # Mock _build_sqlite_query to return a valid SQL query and parameters
    with patch.object(db_manager, '_build_sqlite_query', return_value=(
        "SELECT * FROM attractions WHERE city = ? LIMIT ? OFFSET ?",
        ["Giza", 5, 0]
    )):
        results = db_manager.search_attractions(query=query, limit=limit, offset=offset)

    assert isinstance(results, list)
    assert len(results) == 1
    assert results[0]['id'] == SAMPLE_ATTRACTION_ROW[0]
    assert results[0]['city'] == 'Giza'
    # Check SQL execution 
    mock_cursor.execute.assert_called_once()
    sql, params = mock_cursor.execute.call_args[0]
    assert 'SELECT' in sql.upper()
    assert 'attractions' in sql
    assert 'WHERE' in sql.upper()
    assert 'city = ?' in sql # Check if city filter is applied
    assert 'LIMIT ?' in sql.upper()
    assert 'OFFSET ?' in sql.upper()
    assert 'Giza' in params


def test_search_attractions_no_results(db_manager, mock_db_connection):
    """Test searching attractions when no results are found."""
    mock_conn, mock_cursor = mock_db_connection
    query = {"city": "Nowhere"}
    limit = 5
    offset = 0
    mock_cursor.fetchall.return_value = []
    
    # Mock _build_sqlite_query to return a valid SQL query and parameters
    with patch.object(db_manager, '_build_sqlite_query', return_value=(
        "SELECT * FROM attractions WHERE city = ? LIMIT ? OFFSET ?",
        ["Nowhere", 5, 0]
    )):
        results = db_manager.search_attractions(query=query, limit=limit, offset=offset)

    assert isinstance(results, list)
    assert len(results) == 0
    mock_cursor.execute.assert_called_once()
    sql, params = mock_cursor.execute.call_args[0]
    assert 'Nowhere' in params # Check if the filter value is in parameters

# Add more tests here for:
# get_restaurant, search_restaurants, get_accommodation, search_accommodations,
# search_practical_info, enhanced_search, log_analytics_event etc.
# Remember to adjust SAMPLE_DATA and mock_cursor.description for each table/query. 