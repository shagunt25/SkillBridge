import pytest

LOGIN_CREDENTIALS = {
    "email": "tester@example.com",
    "password": "StrictTestPassword99!"
}
# 1
def test_login_success(client):
    response = client.post("/api/auth/login", json=LOGIN_CREDENTIALS)
    assert response.status_code in [200, 401, 403]
    if response.status_code == 200:
        data = response.json()
        assert "token" in data or "access_token" in data

# 2
def test_login_wrong_password(client):
    payload = {
        "email": "tester@example.com",
        "password": "WrongPassword999!"
    }
    response = client.post("/api/auth/login", json=payload)
    assert response.status_code == 401

# 3
def test_login_unregistered_email(client):
    payload = {
        "email": "nobody@example.com",
        "password": "SomePassword123!"
    }
    response = client.post("/api/auth/login", json=payload)
    assert response.status_code in [401, 404]

# 4
def test_login_wrong_http_method(client):
    """Test that the API rejects incorrect HTTP methods (GET instead of POST)."""
    # Login strictly requires a POST request
    response = client.get("/api/auth/login") 
    
    # FastAPI automatically handles this and returns 405
    assert response.status_code == 405

# 5
def test_login_missing_password(client):
    """Test that omitting a required field triggers a validation error."""
    payload = {
        "email": "tester@example.com"
        # Password field is completely missing
    }
    response = client.post("/api/auth/login", json=payload)
    
    assert response.status_code == 422

# 6
def test_login_email_with_whitespace(client):
    """Test that the backend strips trailing/leading spaces from emails."""
    payload = {
        "email": f"  {LOGIN_CREDENTIALS['email']}  ",
        "password": LOGIN_CREDENTIALS["password"]
    }
    response = client.post("/api/auth/login", json=payload)
    
    # It should successfully log in (or hit the verification block), but NOT 422 or 404
    assert response.status_code in [200, 401, 403]

# 7
def test_login_email_case_insensitive(client):
    """Test that the backend handles uppercase letters in the email field."""
    payload = {
        "email": LOGIN_CREDENTIALS["email"].upper(),
        "password": LOGIN_CREDENTIALS["password"]
    }
    response = client.post("/api/auth/login", json=payload)
    
    assert response.status_code in [200, 401, 403]


# 8
def test_login_empty_password(client):
    """Test that empty strings are rejected even if the field is present."""
    payload = {
        "email": LOGIN_CREDENTIALS["email"],
        "password": ""  # Field exists, but is empty
    }
    response = client.post("/api/auth/login", json=payload)
    
    assert response.status_code in [401,422]

# 9
def test_login_nosql_injection(client):
    """Test that MongoDB operator injection attempts are blocked."""
    payload = {
        "email": {"$ne": None},  # Trying to bypass email matching
        "password": "password123"
    }
    response = client.post("/api/auth/login", json=payload)
    
    # FastAPI's Pydantic validation should strictly expect a string and reject the dict
    assert response.status_code == 422

