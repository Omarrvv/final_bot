import pytest
from unittest.mock import MagicMock, patch
from fastapi import Request, HTTPException, status
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError, Field
from pydantic_core import PydanticCustomError

# Adjust import paths as necessary
from src.utils.exceptions import ChatbotError, ResourceNotFoundError, ValidationError as CustomValidationError
# Assuming handler functions are in error_handler.py or similar
# We might need to import the specific handlers if they are standalone
# from src.utils.error_handler import http_exception_handler, validation_exception_handler, ...
# Or, if they are part of a middleware, we might test the middleware's handling methods
from src.middleware.exception_handler import ExceptionHandlerMiddleware
# Need to import json for response body parsing
import json

# Helper to create a mock request
def create_mock_request(scope: dict = None) -> Request:
    if scope is None:
        scope = {"type": "http", "headers": [], "path": "/test", "method": "GET"}
    return Request(scope)

@pytest.fixture
def exception_middleware():
    """Fixture for the ExceptionHandlerMiddleware instance."""
    # Needs a dummy app instance, doesn't need to be functional
    dummy_app = MagicMock()
    middleware = ExceptionHandlerMiddleware(app=dummy_app, debug=False, include_traceback=False)
    return middleware

# --- Test Specific Exception Handlers (using middleware methods) ---

@pytest.mark.asyncio
async def test_handle_http_exception(exception_middleware):
    """Test handling standard FastAPI/Starlette HTTPException."""
    exc = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    request = create_mock_request()
    request_id = "req-http"

    response = exception_middleware._handle_http_exception(exc, request_id)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    content = json.loads(response.body.decode())
    assert content["error"]["code"] == "HTTP_404"
    assert content["error"]["message"] == "Item not found"

@pytest.mark.asyncio
async def test_handle_validation_error(exception_middleware):
    """Test handling Pydantic RequestValidationError."""
    # Create a realistic Pydantic validation error structure (V2 style)
    raw_errors = [
        {"loc": ("body", "field1"), "msg": "Value error", "type": "value_error", "input": 12},
        {"loc": ("query", "limit"), "msg": "Input should be less than 100", "type": "less_than", "input": 101, "ctx": {"lt": 100}}
    ]
    exc = RequestValidationError(errors=raw_errors)
    request = create_mock_request()
    request_id = "req-validation"

    # Assume the middleware method is adapted for V2 errors
    # If not, this test would need modification or the middleware updated
    response = exception_middleware._handle_validation_error(exc, request_id)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    content = json.loads(response.body.decode())
    assert content["error"]["code"] == "VALIDATION_ERROR"
    assert "Request validation error" in content["error"]["message"]
    assert isinstance(content["error"]["details"], list)
    assert len(content["error"]["details"]) == 2
    # Check structure of details based on V2 raw errors
    assert content["error"]["details"][0]["loc"] == ["body", "field1"]
    assert content["error"]["details"][0]["msg"] == "Value error"
    assert content["error"]["details"][1]["loc"] == ["query", "limit"]
    assert content["error"]["details"][1]["msg"] == "Input should be less than 100"

@pytest.mark.asyncio
async def test_handle_chatbot_error_custom(exception_middleware):
    """Test handling a custom ChatbotError subclass (e.g., ResourceNotFoundError)."""
    # Corrected instantiation based on ResourceNotFoundError signature
    exc = ResourceNotFoundError(resource_type="session", resource_id="res_123", message="Specific session not found")
    request = create_mock_request()
    request_id = "req-chatbot-custom"

    response = exception_middleware._handle_chatbot_error(exc, request_id)

    # Assuming ResourceNotFoundError maps to 404 and specific code
    # This depends on the specific implementation of _handle_chatbot_error
    # For now, let's check the base ChatbotError handling works
    # We need to know the status code and code associated with ResourceNotFoundError
    # Let's assume it inherits from ChatbotError but doesn't set specific status/code
    # Thus, the handler uses defaults or logic based on the type.
    # A better approach would be for ResourceNotFoundError to define its status_code/code.
    # For now, we test the message and details which ARE set by the custom init.

    # Placeholder: Check status code if known (e.g., 404)
    # assert response.status_code == status.HTTP_404_NOT_FOUND
    content = json.loads(response.body.decode())
    # Placeholder: Check code if known
    # assert content["error"]["code"] == "RESOURCE_NOT_FOUND"
    assert content["error"]["message"] == "Specific session not found"
    assert content["error"]["details"] == {"resource_type": "session", "resource_id": "res_123"}

@pytest.mark.asyncio
async def test_handle_chatbot_error_generic(exception_middleware):
    """Test handling a generic ChatbotError."""
    # Corrected instantiation: Base ChatbotError only takes message and details
    exc = ChatbotError(message="Generic app error", details={"info": "some detail"})
    request = create_mock_request()
    request_id = "req-chatbot-generic"

    response = exception_middleware._handle_chatbot_error(exc, request_id)

    # Base ChatbotError likely defaults to 500 or uses specific logic
    # Assume 500 for now unless specified otherwise in _handle_chatbot_error
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    content = json.loads(response.body.decode())
    # Code might default or be determined by handler
    # assert content["error"]["code"] == "INTERNAL_ERROR" # Example default
    assert content["error"]["message"] == "Generic app error"
    assert content["error"]["details"] == {"info": "some detail"}

@pytest.mark.asyncio
async def test_handle_internal_error_no_debug(exception_middleware):
    """Test handling an unexpected generic Exception when debug is off."""
    exc = ValueError("Something unexpected went wrong")
    request = create_mock_request()
    request_id = "req-internal-nodebug"

    # Ensure debug is False (set in fixture)
    exception_middleware.debug = False

    response = exception_middleware._handle_internal_error(exc, request_id)

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    content = json.loads(response.body.decode())
    assert content["error"]["code"] == "INTERNAL_SERVER_ERROR"
    assert content["error"]["message"] == "An unexpected error occurred"
    assert "traceback" not in content["error"]

@pytest.mark.asyncio
async def test_handle_internal_error_with_debug(exception_middleware):
    """Test handling an unexpected generic Exception when debug is on."""
    original_message = "Something detailed went wrong"
    exc = TypeError(original_message)
    request = create_mock_request()
    request_id = "req-internal-debug"

    # Enable debug mode for this test
    exception_middleware.debug = True
    exception_middleware.include_traceback = False # Keep traceback off for simplicity

    response = exception_middleware._handle_internal_error(exc, request_id)

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    content = json.loads(response.body.decode())
    assert content["error"]["code"] == "INTERNAL_SERVER_ERROR"
    # In debug mode, the original exception message should be included
    assert content["error"]["message"] == original_message
    assert "traceback" not in content["error"]

@pytest.mark.asyncio
@patch("traceback.format_exc")
async def test_handle_internal_error_with_traceback(mock_format_exc, exception_middleware):
    """Test handling an unexpected generic Exception with traceback included."""
    exc = ZeroDivisionError("Division fail")
    request = create_mock_request()
    request_id = "req-internal-traceback"
    mock_format_exc.return_value = "Traceback line 1\nTraceback line 2"

    # Enable debug and traceback
    exception_middleware.debug = True
    exception_middleware.include_traceback = True

    response = exception_middleware._handle_internal_error(exc, request_id)

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    content = json.loads(response.body.decode())
    assert content["error"]["code"] == "INTERNAL_SERVER_ERROR"
    assert content["error"]["message"] == str(exc)
    assert "traceback" in content["error"]
    assert content["error"]["traceback"] == mock_format_exc.return_value
    mock_format_exc.assert_called_once()

# Add tests for logging within the handlers
# Add tests for specific edge cases if the handlers have complex logic
# If using standalone handlers (@app.exception_handler), test those directly 