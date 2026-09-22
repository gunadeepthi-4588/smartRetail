import pytest
from app import create_app

@pytest.fixture
def client():
    app = create_app("testing")
    app.config["TESTING"] = True
    with app.test_client() as client:
        with app.app_context():
            yield client

def test_api_health_endpoint(client):
    """Verifies that the core /api/health endpoint returns 200 and online status."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "online"
    assert data["service"] == "SmartRetail Backend API"
    assert "timestamp" in data

def test_db_health_endpoint_structure(client):
    """Verifies /api/health/db returns structured JSON without exposing secrets."""
    response = client.get("/api/health/db")
    assert response.status_code in (200, 503)
    data = response.get_json()
    assert "status" in data
    assert "database" in data
    assert "database_name" in data
    assert "timestamp" in data
    # Sensitive credentials MUST NEVER be present in the response
    assert "password" not in str(data).lower()
    assert "db_password" not in str(data).lower()

def test_invalid_db_config_error_handling():
    """Verifies that invalid DB configuration produces controlled error and doesn't crash."""
    app = create_app("development")
    app.config["DB_HOST"] = "non_existent_host_12345"
    app.config["DB_PORT"] = 9999
    
    with app.test_client() as client:
        response = client.get("/api/health/db")
        assert response.status_code == 503
        data = response.get_json()
        assert data["status"] == "error"
        assert data["database"] == "disconnected"
        assert "password" not in str(data).lower()
