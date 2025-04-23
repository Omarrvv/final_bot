# FastAPI Middleware Components

This directory contains middleware components for the Egypt Tourism Chatbot FastAPI application.

## Available Middleware

### 1. RequestLoggingMiddleware

The `RequestLoggingMiddleware` logs details about incoming HTTP requests and their responses, including:

- Request method and path
- Client IP address
- User agent
- Status code
- Processing time
- Request/response bodies (optional)

#### Usage

```python
from fastapi import FastAPI
from src.middleware.request_logger import add_request_logging_middleware

app = FastAPI()

# Add request logging middleware
add_request_logging_middleware(
    app,
    exclude_paths=["/health", "/metrics"],  # Custom paths to exclude
    log_request_body=True,  # Log request bodies (default: False)
    log_response_body=True,  # Log response bodies (default: False)
)
```

### 2. RequestIDMiddleware

The `RequestIDMiddleware` ensures that each request has a unique identifier, which is used for tracing requests through the system and correlating log entries.

- Generates a UUID4 identifier for each request if not provided
- Extracts existing request IDs from the `X-Request-ID` header
- Makes the request ID available via `request.state.request_id`
- Adds the request ID to response headers

#### Usage

```python
from fastapi import FastAPI, Request
from src.middleware.request_id import add_request_id_middleware, get_request_id

app = FastAPI()

# Add request ID middleware
add_request_id_middleware(
    app,
    header_name="X-Request-ID",  # Default header name
    generate_if_not_present=True,  # Generate IDs if not provided
    return_header=True  # Add the ID to response headers
)

# Access the request ID in a route handler
@app.get("/")
async def root(request: Request):
    request_id = get_request_id(request)
    return {"request_id": request_id}
```

### 3. ExceptionHandlerMiddleware

The `ExceptionHandlerMiddleware` provides centralized exception handling for all routes, converting various types of exceptions into standardized API responses.

- Handles built-in FastAPI/Starlette HTTP exceptions
- Handles validation errors from Pydantic
- Provides custom exception classes for different error types
- Logs exceptions with appropriate severity levels
- Supports debug mode with detailed error information

#### Usage

```python
from fastapi import FastAPI
from src.middleware.exception_handler import (
    add_exception_handler_middleware,
    NotFoundError,
    ValidationError,
    UnauthorizedError
)

app = FastAPI()

# Add exception handler middleware
add_exception_handler_middleware(
    app,
    debug=False,  # Enable for development
    include_traceback=False  # Include stack traces in debug mode
)

# Use custom exception types in route handlers
@app.get("/items/{item_id}")
async def get_item(item_id: str):
    if not item_exists(item_id):
        raise NotFoundError(
            message=f"Item with ID {item_id} not found",
            details={"item_id": item_id}
        )
    return {"item_id": item_id}
```

### 4. CORS Configuration

The `cors` module provides secure configuration for Cross-Origin Resource Sharing (CORS) with FastAPI.

- Prevents use of wildcard (`*`) origins in production
- Provides secure defaults for allowed methods and headers
- Supports regex patterns for matching origins
- Includes helper function for common development and production origins

#### Usage

```python
from fastapi import FastAPI
from src.middleware.cors import add_cors_middleware, get_default_origins

app = FastAPI()

# Get default origins plus your frontend URL
allowed_origins = get_default_origins(frontend_url="https://example.com")

# Add CORS middleware with secure configuration
add_cors_middleware(
    app,
    allowed_origins=allowed_origins,  # Never use ["*"] in production
    allow_credentials=True,
    allowed_methods=["GET", "POST", "PUT", "DELETE"]
)
```

## Middleware Order

The order in which middleware components are added is important:

1. **RequestIDMiddleware**: Should be added first so all subsequent logs have request IDs
2. **RequestLoggingMiddleware**: Added early to log all requests, including those rejected by other middleware
3. **ExceptionHandlerMiddleware**: Added next to handle exceptions from all subsequent middleware
4. **CORS Middleware**: Added next to handle CORS preflight requests and headers
5. Other application-specific middleware

## Testing

Tests for all middleware components are located in `tests/middleware/`. To run the tests:

```bash
# Run all middleware tests
pytest tests/middleware/ -v

# Run tests for a specific middleware
pytest tests/middleware/test_request_logger.py -v
pytest tests/middleware/test_request_id.py -v
pytest tests/middleware/test_exception_handler.py -v
pytest tests/middleware/test_cors.py -v
```

## Examples

For examples of middleware usage and configuration, see:

- `examples/middleware_usage.py` - Examples for individual middleware
- `examples/middleware_configuration.py` - Example of configuring all middleware together
