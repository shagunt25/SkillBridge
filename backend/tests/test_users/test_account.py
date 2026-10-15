import uuid
import pytest
from app.database.mongodb import db
import jwt
import time
from app.utils.security import JWT_SECRET, JWT_ALGORITHM

@pytest.fixture(scope="function")
def active_user(client):
    """Fixture providing a newly registered, verified user and their active token."""
    unique_email = f"account_{uuid.uuid4().hex[:8]}@example.com"
    password = "StrictTestPassword99!"
    
    # Sign up
    client.post("/api/auth/signup", json={
        "name": "Account Tester", 
        "email": unique_email, 
        "password": password
    })
    
    # Manually verify
    db.users.update_one(
        {"email": unique_email},
        {"$set": {"email_verified": True, "is_verified": True}}
    )
    
    # Log in
    response = client.post("/api/auth/login", json={
        "email": unique_email,
        "password": password
    })
    
    token = response.json().get("access_token") or response.json().get("token")
    return {"email": unique_email, "password": password, "token": token}


# ==========================================
# 1. READ CURRENT USER (GET /api/users/me)
# ==========================================

def test_read_current_user_success(client, active_user):
    """Verifies that an authenticated user can read their own profile."""
    headers = {"Authorization": f"Bearer {active_user['token']}"}
    response = client.get("/api/users/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == active_user["email"]

def test_read_user_no_token(client):
    """Verifies that accessing the profile without a token is rejected."""
    client.cookies.clear()
    response = client.get("/api/users/me")
    assert response.status_code == 401

def test_read_user_invalid_token(client):
    """Verifies that accessing the profile with a fake/corrupted token is rejected."""
    headers = {"Authorization": "Bearer this.is.a.fake.token"}
    response = client.get("/api/users/me", headers=headers)
    assert response.status_code == 401


# ==========================================
# 2. CHANGE PASSWORD (POST /api/users/me/change-password)
# ==========================================

def test_change_password_success(client, active_user):
    """Verifies that providing the correct old password allows updating to a new one."""
    headers = {"Authorization": f"Bearer {active_user['token']}"}
    payload = {
        "old_password": active_user["password"],
        "new_password": "NewSecurePassword123!"
    }
    response = client.post("/api/users/me/change-password", headers=headers, json=payload)
    assert response.status_code == 200
    
    # Verify the new password actually works for logging in
    login_res = client.post("/api/auth/login", json={
        "email": active_user["email"],
        "password": payload["new_password"]
    })
    assert login_res.status_code == 200

def test_change_password_wrong_old_password(client, active_user):
    """Verifies that providing an incorrect old password blocks the update."""
    headers = {"Authorization": f"Bearer {active_user['token']}"}
    payload = {
        "old_password": "WrongOldPassword123!",
        "new_password": "NewSecurePassword123!"
    }
    response = client.post("/api/users/me/change-password", headers=headers, json=payload)
    assert response.status_code in [400, 401, 403]

def test_change_password_too_short(client, active_user):
    """Verifies that the new password strictly adheres to length constraints."""
    headers = {"Authorization": f"Bearer {active_user['token']}"}
    payload = {
        "old_password": active_user["password"],
        "new_password": "short"
    }
    response = client.post("/api/users/me/change-password", headers=headers, json=payload)
    assert response.status_code == 422

def test_change_password_same_as_old(client, active_user):
    """Verifies behavior when the user tries to change the password to the exact same one."""
    headers = {"Authorization": f"Bearer {active_user['token']}"}
    payload = {
        "old_password": active_user["password"],
        "new_password": active_user["password"]
    }
    response = client.post("/api/users/me/change-password", headers=headers, json=payload)
    # Accepting 400 (strict policy) or 200 (lenient policy) based on backend implementation
    assert response.status_code in [400, 422, 200]

def test_change_password_no_token(client):
    """Verifies that changing a password requires authentication."""
    payload = {
        "old_password": "SomePassword123!",
        "new_password": "NewSecurePassword123!"
    }
    response = client.post("/api/users/me/change-password", json=payload)
    assert response.status_code == 401


# ==========================================
# 3. DELETE ACCOUNT (DELETE /api/users/me)
# ==========================================

def test_delete_account_lifecycle(client, active_user):
    """Verifies account deletion removes DB records and immediately invalidates access."""
    email = active_user["email"]
    headers = {"Authorization": f"Bearer {active_user['token']}"}
    
    # 1. Delete the account
    del_res = client.delete("/api/users/me", headers=headers)
    assert del_res.status_code == 200
    
    # 2. Database verification (Cascade Check)
    deleted_user = db.users.find_one({"email": email})
    assert deleted_user is None, "User record must be completely removed from the database"
    
    # 3. Token invalidation check
    read_res = client.get("/api/users/me", headers=headers)
    assert read_res.status_code in [401, 404], "Deleted user token must no longer work"

def test_delete_account_no_token(client):
    """Verifies that deleting an account requires authentication."""
    response = client.delete("/api/users/me")
    assert response.status_code == 401

# 4. COMPLIANCE & PRIVACY: True Cascade Deletion (Orphaned Data Check)
def test_delete_account_removes_related_data(client, active_user):
    """Verifies that deleting an account also purges their related data (e.g., resumes)."""
    email = active_user["email"]
    headers = {"Authorization": f"Bearer {active_user['token']}"}
    
    # 1. Manually insert a mock resume/analysis record tied to this user
    db.resumes.insert_one({"user_email": email, "filename": "my_resume.pdf", "content": "..."})
    
    # 2. Delete the account
    client.delete("/api/users/me", headers=headers)
    
    # 3. Verify the related data is completely purged
    orphaned_resume = db.resumes.find_one({"user_email": email})
    # Accept this failing if your backend hasn't implemented cascade deletion for resumes yet
    assert orphaned_resume is None, "Related user data must be deleted to prevent orphaned records"


# 5. EDGE CASE: Wrong HTTP Methods
def test_read_user_wrong_method(client, active_user):
    """Verifies that sending a POST request to a GET-only profile route is rejected."""
    headers = {"Authorization": f"Bearer {active_user['token']}"}
    response = client.post("/api/users/me", headers=headers)
    assert response.status_code == 405

# 6. EDGE CASE: Missing Fields in Payload
def test_change_password_missing_fields(client, active_user):
    """Verifies that requests missing required fields are rejected by Pydantic."""
    headers = {"Authorization": f"Bearer {active_user['token']}"}
    
    # Missing old_password
    response1 = client.post("/api/users/me/change-password", headers=headers, json={
        "new_password": "NewSecurePassword123!"
    })
    assert response1.status_code == 422

    # Missing new_password
    response2 = client.post("/api/users/me/change-password", headers=headers, json={
        "old_password": active_user["password"]
    })
    assert response2.status_code == 422


# 7. SECURITY: Excessive Password Length
def test_change_password_max_length(client, active_user):
    """Verifies that excessively long passwords are rejected to prevent bcrypt DOS/truncation."""
    headers = {"Authorization": f"Bearer {active_user['token']}"}
    payload = {
        "old_password": active_user["password"],
        "new_password": "A" * 100  # 100 character password
    }
    response = client.post("/api/users/me/change-password", headers=headers, json=payload)
    # Ideally your Pydantic schema caps length at 50-64 characters
    assert response.status_code == 422

# 8. SECURITY: Expired Access Token
def test_read_user_expired_token(client, active_user):
    """Verifies that a validly signed but mathematically expired JWT is rejected."""
    current_time = int(time.time())
    
    expired_payload = {
        "sub": active_user["email"],
        "iat": current_time - 1800,  # Issued 30 mins ago
        "exp": current_time - 900    # Expired 15 mins ago
    }
    
    token = jwt.encode(expired_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    # 1. Clear the valid cookie set by the fixture's login
    client.cookies.clear()
    
    # 2. Inject the expired token into the specific cookie the backend reads
    # Note: If your COOKIE_NAME is different, change "skillbridge_auth" to match it.
    client.cookies.set("skillbridge_auth", token)
    
    # 3. Make the request WITHOUT the Authorization header
    response = client.get("/api/users/me")
    
    assert response.status_code == 401

# 10. SECURITY: Stale Token Rejection (Password Change Invalidation)
def test_token_invalidated_after_password_change(client, active_user):
    """Verifies that old tokens are rejected after a user changes their password."""
    # Extract the token manually to bypass httpx CookieConflict errors
    original_token = None
    for cookie in client.cookies.jar:
        if cookie.name == "skillbridge_auth":
            original_token = cookie.value
            break
            
    assert original_token is not None, "Authentication cookie was not found in the client jar"
    
    # 1. Change the password
    payload = {
        "old_password": active_user["password"],
        "new_password": "BrandNewPassword123!"
    }
    change_res = client.post("/api/users/me/change-password", json=payload)
    assert change_res.status_code == 200
    
    # 2. Attempt to access the profile by passing the OLD token explicitly
    profile_res = client.get("/api/users/me", cookies={"skillbridge_auth": original_token})
    
    # The backend must reject this because 'iat' < 'password_changed_at'
    assert profile_res.status_code == 401


