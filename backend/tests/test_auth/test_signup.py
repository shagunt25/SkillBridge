import pytest
import uuid

TEST_USER = {
    "name": "Automated Tester",
    "email": "tester@example.com",
    "password": "StrictTestPassword99!"
}

# 1
def test_signup_success(client):
    response = client.post("/api/auth/signup", json=TEST_USER)
    assert response.status_code in [200, 201]
    data = response.json()
    assert "email" in data
    assert data["email"] == TEST_USER["email"]

# 2
def test_signup_duplicate_email(client):
    response = client.post("/api/auth/signup", json=TEST_USER)
    assert response.status_code == 409

# 3
def test_signup_invalid_email_format(client):
    bad_user = {
        "name": "Invalid Email User",
        "email": "not-an-email-format",
        "password": "StrictTestPassword99!"
    }
    response = client.post("/api/auth/signup", json=bad_user)
    assert response.status_code == 422

# 4
def test_signup_name_too_short(client):
    bad_user = TEST_USER.copy()
    bad_user["name"] = "A" # Only 1 character
    response = client.post("/api/auth/signup", json=bad_user)
    # Pydantic should catch the length constraint and return 422 Unprocessable Entity
    assert response.status_code == 422

# 5
def test_signup_password_too_short(client):
    bad_user = TEST_USER.copy()
    bad_user["password"] = "short" # Less than 8 characters
    response = client.post("/api/auth/signup", json=bad_user)
    assert response.status_code == 422

# 6
def test_signup_duplicate_email_case_insensitive(client):
    """Test that signing up with an uppercase version of an existing email is blocked."""
    # Create a payload with the exact same email from TEST_USER, but capitalized
    uppercase_user = TEST_USER.copy()
    uppercase_user["email"] = uppercase_user["email"].upper()
    
    response = client.post("/api/auth/signup", json=uppercase_user)
    
    # The backend should recognize it as the same email and return 409 Conflict
    assert response.status_code == 409

# 7 
def test_signup_excessive_password_length(client):
    unique_email = f"longpass_{uuid.uuid4().hex[:8]}@example.com"
    bad_user = {
        "name": "Long Password User",
        "email": unique_email,
        "password": "A" * 1000  
    }
    
    response = client.post("/api/auth/signup", json=bad_user)
    
    # Accepts 422/400 if a max length is enforced, or 200/201 if the backend accepts it
    assert response.status_code in [400, 422, 200, 201]
# 8
def test_signup_empty_password(client):
    """Test that a user cannot register an account with an empty password."""
    bad_user = TEST_USER.copy()
    # Provide a unique email to bypass the duplicate check
    bad_user["email"] = f"emptypass_{uuid.uuid4().hex[:8]}@example.com"
    bad_user["password"] = ""  
    
    response = client.post("/api/auth/signup", json=bad_user)
    
    # The API must reject this with a validation error (422) or bad request (400)
    assert response.status_code in [400, 422]