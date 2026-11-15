import uuid

import pytest

from app.database.mongodb import db
from app.services import auth_service, otp_service

TEST_USER = {
    "name": "Automated Tester",
    "email": "tester@example.com",
    "password": "StrictTestPassword99!"
}

def test_signup_success(client):
    payload = {**TEST_USER, "email": f"signup_{uuid.uuid4().hex}@example.com"}
    try:
        response = client.post("/api/auth/signup", json=payload)
        assert response.status_code == 200
        assert response.json()["email"] == payload["email"]
    finally:
        db.users.delete_one({"email": payload["email"]})
        otp_service.otp_collection.delete_many({"email": payload["email"]})

def test_signup_duplicate_email(client):
    payload = {**TEST_USER, "email": f"duplicate_{uuid.uuid4().hex}@example.com"}
    try:
        assert client.post("/api/auth/signup", json=payload).status_code == 200
        response = client.post("/api/auth/signup", json=payload)
        assert response.status_code == 409
    finally:
        db.users.delete_one({"email": payload["email"]})
        otp_service.otp_collection.delete_many({"email": payload["email"]})
        otp_service.otp_rate_limits_collection.delete_many({})


def test_signup_duplicate_email_race_returns_conflict(client, monkeypatch):
    email = f"race_{uuid.uuid4().hex[:8]}@example.com"
    payload = {**TEST_USER, "email": email}
    first_response = client.post("/api/auth/signup", json=payload)

    assert first_response.status_code == 200

    monkeypatch.setattr(
        auth_service.users_collection,
        "find_one",
        lambda _query: None,
    )
    try:
        duplicate_response = client.post("/api/auth/signup", json=payload)
        assert duplicate_response.status_code == 409
        assert duplicate_response.json()["detail"] == (
            "An account with this email already exists."
        )
    finally:
        db.users.delete_one({"email": email})
        otp_service.otp_collection.delete_many({"email": email})
        otp_service.otp_rate_limits_collection.delete_many({})

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
    payload = {
        **TEST_USER,
        "email": f"case_{uuid.uuid4().hex}@example.com",
    }
    uppercase_user = {**payload, "email": payload["email"].upper()}
    try:
        assert client.post("/api/auth/signup", json=payload).status_code == 200
        response = client.post("/api/auth/signup", json=uppercase_user)
        assert response.status_code == 409
    finally:
        db.users.delete_one({"email": payload["email"]})
        otp_service.otp_collection.delete_many({"email": payload["email"]})
        otp_service.otp_rate_limits_collection.delete_many({})

# 7 
def test_signup_excessive_password_length(client):
    unique_email = f"longpass_{uuid.uuid4().hex[:8]}@example.com"
    bad_user = {
        "name": "Long Password User",
        "email": unique_email,
        "password": "A" * 1000  
    }
    
    response = client.post("/api/auth/signup", json=bad_user)
    assert response.status_code == 422


def test_signup_empty_password(client):
    """Test that a user cannot register an account with an empty password."""
    bad_user = TEST_USER.copy()
    # Provide a unique email to bypass the duplicate check
    bad_user["email"] = f"emptypass_{uuid.uuid4().hex[:8]}@example.com"
    bad_user["password"] = ""  
    
    response = client.post("/api/auth/signup", json=bad_user)
    
    # The API must reject this with a validation error (422) or bad request (400)
    assert response.status_code == 422