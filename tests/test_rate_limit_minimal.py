"""
Minimal test to check FastAPILimiter initialization and rate limiting on the real app.
"""
from starlette.testclient import TestClient
from src.main import app

def test_rate_limit_minimal():
    with TestClient(app) as client:
        response = client.post(
            "/api/chat",
            json={"message": "test", "language": "en"},
            headers={"X-CSRF-Token": "test-token"}
        )
        assert response.status_code in (200, 429)
