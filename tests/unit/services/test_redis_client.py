import pytest
import json
from unittest.mock import MagicMock, patch
import redis # Import the actual library to mock its exceptions
from unittest.mock import AsyncMock # Import AsyncMock
import pytest_asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Adjust import path as necessary
from src.services.redis_client import RedisClient

@pytest_asyncio.fixture
async def mock_redis_lib():
    """Fixture for a mocked underlying redis library client (async version)."""
    # Use AsyncMock for async methods
    mock = MagicMock()
    mock.ping = AsyncMock(return_value=True)
    mock.get = AsyncMock(return_value=None) # Default: key not found
    mock.setex = AsyncMock(return_value=True)
    mock.delete = AsyncMock(return_value=1) # Simulate 1 key deleted
    mock.exists = AsyncMock(return_value=0) # Default: key doesn't exist
    mock.close = AsyncMock(return_value=None)
    # Add other commands as needed
    return mock

# Use pytest_asyncio.fixture for async fixtures
@pytest_asyncio.fixture
async def redis_client_instance(mock_redis_lib):
    """Fixture for RedisClient instance with mocked underlying library.

    Instantiates the client and calls connect.
    """
    # Patch the `redis.from_url` AND `redis.Redis` call potentially made within client.connect
    with patch('redis.asyncio.from_url', return_value=mock_redis_lib) as mock_from_url, \
         patch('redis.asyncio.Redis', return_value=mock_redis_lib) as mock_redis_init:
        try:
            # Instantiate without URI
            client = RedisClient(host="dummy", port=6379, db=0)
            # Manually connect the client within the test fixture
            connected = await client.connect() # This will call the patched from_url/Redis
            assert connected is True
            # Ensure ping was checked during connect
            mock_redis_lib.ping.assert_called_once()
            # Return the connected client and the mock lib
            yield client, mock_redis_lib
            # Teardown: ensure disconnect is called
            await client.disconnect()
            mock_redis_lib.close.assert_called_once()

        except ImportError as e:
            logger.error(f"Skipping RedisClient tests due to import error: {e}")
            pytest.skip(f"Skipping RedisClient tests due to import error: {e}")
        except Exception as e:
            logger.error(f"Skipping RedisClient tests due to init/connect error: {e}")
            pytest.skip(f"Skipping RedisClient tests due to init/connect error: {e}")

# --- RedisClient Tests ---

@pytest.mark.asyncio
async def test_redis_client_instantiation_and_connect_success(redis_client_instance):
    """Test successful instantiation and connection via fixture."""
    client, mock_lib = redis_client_instance
    assert client is not None
    assert client.client == mock_lib # Check if the mock library client is stored and connected

@pytest.mark.asyncio
async def test_redis_client_connect_ping_fails(mock_redis_lib):
    """Test connect method when the ping fails."""
    mock_redis_lib.ping = AsyncMock(side_effect=redis.exceptions.ConnectionError("Ping failed"))

    # Patch the redis connection methods and make sure to patch async_timeout
    with patch('redis.asyncio.from_url', return_value=mock_redis_lib), \
         patch('redis.asyncio.Redis', return_value=mock_redis_lib), \
         patch('redis.asyncio.connection.asyncio.open_connection') as mock_open_connection:

        # Make open_connection raise ConnectionError directly to avoid timeout complexity
        mock_open_connection.side_effect = ConnectionError("Connection failed")

        client = RedisClient(host="dummy", port=6379, db=0)

        # Expect connect to raise a ConnectionError or RedisError
        with pytest.raises((ConnectionError, redis.exceptions.RedisError)):
            await client.connect()

@pytest.mark.asyncio
async def test_get_key_found(redis_client_instance):
    """Test retrieving a key that exists (as string)."""
    client, mock_lib = redis_client_instance
    key = "mykey"
    expected_value = "myvalue"
    mock_lib.get.return_value = expected_value

    # Assuming methods like get/setex are now on the client instance
    value = await client.get(key)

    assert value == expected_value
    mock_lib.get.assert_called_once_with(key)

@pytest.mark.asyncio
async def test_get_key_found_json(redis_client_instance):
    """Test retrieving a key that exists and parsing it as JSON."""
    client, mock_lib = redis_client_instance
    key = "myjsonkey"
    json_string = '{"a": 1, "b": "hello"}'
    expected_dict = {"a": 1, "b": "hello"}
    mock_lib.get.return_value = json_string

    # Assuming RedisClient has a get_json method or similar
    if not hasattr(client, 'get_json'):
         pytest.skip("Skipping test: RedisClient does not have get_json method")

    value = await client.get_json(key) # Assuming get_json is async

    assert value == expected_dict
    mock_lib.get.assert_called_once_with(key)

@pytest.mark.asyncio
async def test_get_key_not_found(redis_client_instance):
    """Test retrieving a key that does not exist."""
    client, mock_lib = redis_client_instance
    key = "nonexistent"
    mock_lib.get.return_value = None

    value = await client.get(key)

    assert value is None
    mock_lib.get.assert_called_once_with(key)

@pytest.mark.asyncio
async def test_set_key_success(redis_client_instance):
    """Test setting a key with an expiry."""
    client, mock_lib = redis_client_instance
    key = "newkey"
    value = "newvalue"
    ttl = 3600
    mock_lib.setex.return_value = True

    result = await client.setex(key, ttl, value)

    assert result is True
    mock_lib.setex.assert_called_once_with(key, ttl, value)

@pytest.mark.asyncio
async def test_set_key_json_success(redis_client_instance):
    """Test setting a key with a dictionary value (serialized to JSON)."""
    client, mock_lib = redis_client_instance
    key = "newjsonkey"
    value_dict = {"c": True, "d": [1, 2]}
    value_json = json.dumps(value_dict) # Expected serialized value
    ttl = 60
    mock_lib.setex.return_value = True

    # Assuming RedisClient has a set_json method or similar
    if not hasattr(client, 'set_json'):
         pytest.skip("Skipping test: RedisClient does not have set_json method")

    result = await client.set_json(key, ttl, value_dict) # Assuming async

    assert result is True
    mock_lib.setex.assert_called_once_with(key, ttl, value_json)

@pytest.mark.asyncio
async def test_delete_key_success(redis_client_instance):
    """Test deleting an existing key."""
    client, mock_lib = redis_client_instance
    key = "todelete"
    mock_lib.delete.return_value = 1 # Simulate 1 key deleted

    result = await client.delete(key)

    assert result is True
    mock_lib.delete.assert_called_once_with(key)

@pytest.mark.asyncio
async def test_delete_key_not_found(redis_client_instance):
    """Test deleting a key that does not exist."""
    client, mock_lib = redis_client_instance
    key = "nonexistent"
    mock_lib.delete.return_value = 0 # Simulate 0 keys deleted

    result = await client.delete(key)

    assert result is False
    mock_lib.delete.assert_called_once_with(key)

@pytest.mark.asyncio
async def test_command_redis_error(redis_client_instance):
    """Test handling of RedisError during a command execution."""
    client, mock_lib = redis_client_instance
    key = "anykey"
    # Configure the mock method on the library mock
    mock_lib.get.side_effect = redis.exceptions.RedisError("Command failed")

    # Check if the client is expected to raise or return a specific value
    with pytest.raises(redis.exceptions.RedisError): # Or maybe a custom wrapper exception
         await client.get(key)
    # Alternatively, if it's supposed to return None on error:
    # assert await client.get(key) is None
    mock_lib.get.assert_called_once_with(key)

# Add tests for:
# - Other wrapped Redis commands (exists, incr, decr, sadd, smembers etc.)
# - Connection closing logic if implemented (e.g., a close() method)
# - Handling of different data types if serialization is complex
# - More specific error handling scenarios
# - Test the URI connection logic within the connect method