import uuid
import pytest
from app.database.mongodb import db

@pytest.fixture
def active_user_token(client):
    """Fixture providing a valid JWT for an active, verified user."""
    email = f"logout_{uuid.uuid4().hex[:8]}@example.com"
    password = "StrictTestPassword99!"
    
    # Sign up and verify
    client.post("/api/auth/signup", json={
        "name": "Logout Tester",
        "email": email,
        "password": password
    })
    db.users.update_one(
        {"email": email},
        {"$set": {"email_verified": True, "is_verified": True}}
    )
    
    # Log in to get token
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    return res.json().get("access_token") or res.json().get("token")


# 1. HAPPY PATH: Successful Logout
def test_logout_success(client, active_user_token):
    """Verifies that an authenticated user can successfully log out."""
    headers = {"Authorization": f"Bearer {active_user_token}"}
    response = client.post("/api/auth/logout", headers=headers)
    assert response.status_code == 200


# 2. SECURITY: Token Invalidation
def test_logout_invalidates_token(client, active_user_token):
    """Verifies that after logging out, the token cannot be used to access protected routes."""
    headers = {"Authorization": f"Bearer {active_user_token}"}
    
    # 1. Log out
    logout_res = client.post("/api/auth/logout", headers=headers)
    assert logout_res.status_code == 200
    
    # 2. Attempt to use the same token on a protected route
    protected_res = client.get("/api/users/me", headers=headers)
    
    # The backend must reject the invalidated token
    assert protected_res.status_code == 401


# 3. EDGE CASE: Logout without Token
def test_logout_no_token(client):
    """Verifies that attempting to log out without being authenticated returns 401."""
    client.cookies.clear()
    response = client.post("/api/auth/logout")
    assert response.status_code == 401

# 4. EDGE CASE: Wrong HTTP Method
def test_logout_wrong_method(client):
    """Verifies that sending a GET request to logout is rejected."""
    response = client.get("/api/auth/logout")
    assert response.status_code == 405


# 5. EDGE CASE: Malformed Token
def test_logout_malformed_token(client):
    """Verifies that sending a corrupted token returns 401 instead of crashing with 500."""
    headers = {"Authorization": "Bearer not.a.real.jwt"}
    response = client.post("/api/auth/logout", headers=headers)
    assert response.status_code == 401

# 6. BEHAVIOR: Cookie Clearing
def test_logout_clears_cookie(client, active_user_token):
    """Verifies that the logout response includes instructions to clear the auth cookie."""
    headers = {"Authorization": f"Bearer {active_user_token}"}
    
    # Send the logout request
    response = client.post("/api/auth/logout", headers=headers)
    assert response.status_code == 200
    
    # Check if a 'set-cookie' header exists in the response
    set_cookie_header = response.headers.get("set-cookie", "").lower()
    
    # delete_cookie() usually sets Max-Age=0 or Expires in the past
    # Replace 'access_token' with your actual COOKIE_NAME if it's different
    assert "max-age=0" in set_cookie_header or "expires=" in set_cookie_header

