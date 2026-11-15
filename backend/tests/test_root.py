import asyncio
from unittest.mock import patch

from pymongo.errors import ServerSelectionTimeoutError
import pytest

from app.main import FRONTEND_ORIGINS, app, lifespan


def test_read_root(client):
    """Verify that GET / returns a 200 OK and expected response payload."""
    response = client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, dict)
    # Check that a standard message or status key exists
    assert "message" in data or "status" in data


def test_read_root_method_not_allowed(client):
    """Verify that sending a POST request to GET / returns 405 Method Not Allowed."""
    response = client.post("/")
    assert response.status_code == 405


def test_api_routes_are_canonical_and_legacy_paths_stay_available(client):
    client.cookies.clear()

    canonical_response = client.get("/api/progress")
    legacy_response = client.get("/progress")

    assert canonical_response.status_code == 401
    assert legacy_response.status_code == 401

    documented_paths = client.get("/openapi.json").json()["paths"]
    assert "/api/target/career" in documented_paths
    assert "/api/analysis/skill-gap" in documented_paths
    assert "/api/roadmap/generate" in documented_paths
    assert "/api/progress" in documented_paths
    assert "/api/dashboard" in documented_paths
    assert "/target/career" not in documented_paths
    assert "/progress" not in documented_paths


def test_liveness_does_not_depend_on_database(client):
    with patch(
        "app.main.check_database_connection",
        side_effect=ServerSelectionTimeoutError("unavailable"),
    ):
        response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


def test_readiness_returns_success_when_database_is_available(client):
    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_readiness_returns_service_unavailable_when_database_is_down(client):
    with patch(
        "app.main.check_database_connection",
        side_effect=ServerSelectionTimeoutError("unavailable"),
    ):
        response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json()["detail"] == "Database is unavailable."


def test_startup_fails_clearly_when_database_is_unavailable():
    async def start_application():
        async with lifespan(app):
            pass

    with patch(
        "app.main.check_database_connection",
        side_effect=ServerSelectionTimeoutError("unavailable"),
    ), pytest.raises(
        RuntimeError,
        match="MongoDB is unavailable during startup",
    ):
        asyncio.run(start_application())