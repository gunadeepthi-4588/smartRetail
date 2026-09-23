import pytest
from app import create_app
from werkzeug.security import check_password_hash, generate_password_hash

@pytest.fixture
def client():
    app = create_app("testing")
    app.config["TESTING"] = True
    with app.test_client() as client:
        with app.app_context():
            yield client

def test_login_successful_demo_account(client):
    """Verifies that the seeded demo account logs in successfully and returns sanitized user data."""
    payload = {
        "email": "owner@smartretail.com",
        "password": "SmartRetail@123"
    }
    response = client.post("/api/auth/login", json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "success"
    assert data["message"] == "Login successful"
    
    user = data["user"]
    assert user["email"] == "owner@smartretail.com"
    assert user["name"] == "Rajesh Kumar"
    assert user["role"] == "Store Owner"
    assert user["store_name"] == "Metro Mart Superstore"
    assert user["store_id"] == 1
    
    # Sensitive fields MUST NOT be present
    assert "password" not in user
    assert "password_hash" not in user

def test_login_invalid_password(client):
    """Verifies that invalid password returns 401 Unauthorized."""
    payload = {
        "email": "owner@smartretail.com",
        "password": "IncorrectPassword"
    }
    response = client.post("/api/auth/login", json=payload)
    assert response.status_code == 401
    data = response.get_json()
    assert data["status"] == "error"
    assert "Invalid email or password" in data["message"]

def test_login_missing_credentials(client):
    """Verifies that missing email or password returns 400 Bad Request."""
    response = client.post("/api/auth/login", json={"email": "owner@smartretail.com"})
    assert response.status_code == 400
    
    response2 = client.post("/api/auth/login", json={"password": "SmartRetail@123"})
    assert response2.status_code == 400

def test_auth_me_endpoint(client):
    """Verifies that /api/auth/me returns current store owner profile."""
    response = client.get("/api/auth/me?user_id=1")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "success"
    assert data["user"]["name"] == "Rajesh Kumar"
    assert data["user"]["store_name"] == "Metro Mart Superstore"
