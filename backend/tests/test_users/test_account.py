import uuid
import pytest
from app.database.mongodb import db

@pytest.fixture(scope="function")
def active_user(client):
    # Generate a unique email for every test to prevent 409 Conflicts
    unique_email = f"tester_{uuid.uuid4().hex[:8]}@example.com"
    password = "StrictTestPassword99!"
    
    # 1. Sign up
    client.post("/api/auth/signup", json={
        "name": "Account Tester", 
        "email": unique_email, 
        "password": password
    })
    
    # 2. Verify
    db.users.update_one(
        {"email": unique_email},
        {"$set": {"email_verified": True, "is_verified": True}}
    )
    
    # 3. Log in
    response = client.post("/api/auth/login", json={
        "email": unique_email,
        "password": password
    })
    
    token = response.json().get("access_token", response.json().get("token"))
    return {"email": unique_email, "password": password, "token": token}

def test_read_current_user(client, active_user):
    headers = {"Authorization": f"Bearer {active_user['token']}"}
    response = client.get("/api/users/me", headers=headers)
    
    assert response.status_code == 200
    assert response.json()["email"] == active_user["email"]

def test_read_user_no_token(client):
    # Clear any residual cookies the TestClient might have retained
    client.cookies.clear()
    response = client.get("/api/users/me")
    assert response.status_code == 401

def test_change_password(client, active_user):
    headers = {"Authorization": f"Bearer {active_user['token']}"}
    payload = {
        "old_password": active_user["password"],
        "new_password": "NewSecurePassword123!"
    }
    response = client.post("/api/users/me/change-password", headers=headers, json=payload)
    assert response.status_code == 200

def test_change_password_wrong_old_password(client, active_user):
    headers = {"Authorization": f"Bearer {active_user['token']}"}
    payload = {
        "old_password": "IncorrectPassword123!", # Deliberately wrong
        "new_password": "NewSecurePassword123!"
    }
    response = client.post("/api/users/me/change-password", headers=headers, json=payload)
    
    # The backend should reject this request
    assert response.status_code in [400, 401]

def test_delete_account(client, active_user):
    headers = {"Authorization": f"Bearer {active_user['token']}"}
    response = client.delete("/api/users/me", headers=headers)
    assert response.status_code == 200

def test_change_password_too_short(client, active_user):
    headers = {"Authorization": f"Bearer {active_user['token']}"}
    payload = {
        "old_password": active_user["password"],
        "new_password": "short" # Invalid new password length
    }
    response = client.post("/api/users/me/change-password", headers=headers, json=payload)
    assert response.status_code == 422

def test_read_user_invalid_token(client):
    """Test that a fake or corrupted JWT token is rejected."""
    client.cookies.clear()  # <-- Add this line to flush the valid session
    headers = {"Authorization": "Bearer this.is.a.fake.token"}
    response = client.get("/api/users/me", headers=headers)
    
    assert response.status_code == 401
    
