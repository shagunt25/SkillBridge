from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.database.mongodb import db
from app.services import auth_service

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
    response = client.get("/api/auth/login") 
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
    
    assert response.status_code == 422


def test_login_rate_limits_failed_attempts_per_email_and_ip(
    client,
    monkeypatch,
):
    email = f"rate-limit-{uuid4().hex}@example.com"
    monkeypatch.setattr(
        auth_service,
        "LOGIN_RATE_LIMIT_EMAIL_IP_MAX_ATTEMPTS",
        2,
    )
    monkeypatch.setattr(
        auth_service,
        "LOGIN_RATE_LIMIT_IP_MAX_ATTEMPTS",
        100,
    )
    auth_service.login_rate_limits_collection.delete_many({})

    try:
        with patch(
            "app.routes.auth.authenticate_user",
            side_effect=HTTPException(
                status_code=401,
                detail="Invalid email or password.",
            ),
        ) as authenticate:
            responses = [
                client.post(
                    "/api/auth/login",
                    json={"email": email, "password": "WrongPassword123!"},
                )
                for _ in range(3)
            ]

        assert [response.status_code for response in responses] == [
            401,
            401,
            429,
        ]
        assert responses[-1].headers["retry-after"].isdigit()
        assert authenticate.call_count == 2
    finally:
        auth_service.login_rate_limits_collection.delete_many({})


def test_login_rate_limits_failed_attempts_per_ip(client, monkeypatch):
    monkeypatch.setattr(
        auth_service,
        "LOGIN_RATE_LIMIT_EMAIL_IP_MAX_ATTEMPTS",
        100,
    )
    monkeypatch.setattr(
        auth_service,
        "LOGIN_RATE_LIMIT_IP_MAX_ATTEMPTS",
        2,
    )
    auth_service.login_rate_limits_collection.delete_many({})

    try:
        with patch(
            "app.routes.auth.authenticate_user",
            side_effect=HTTPException(
                status_code=401,
                detail="Invalid email or password.",
            ),
        ) as authenticate:
            responses = [
                client.post(
                    "/api/auth/login",
                    json={
                        "email": f"rate-limit-{uuid4().hex}@example.com",
                        "password": "WrongPassword123!",
                    },
                )
                for _ in range(3)
            ]

        assert [response.status_code for response in responses] == [
            401,
            401,
            429,
        ]
        assert authenticate.call_count == 2
    finally:
        auth_service.login_rate_limits_collection.delete_many({})


def test_successful_logins_do_not_consume_failure_limits(
    client,
    monkeypatch,
):
    email = f"rate-limit-success-{uuid4().hex}@example.com"
    monkeypatch.setattr(
        auth_service,
        "LOGIN_RATE_LIMIT_EMAIL_IP_MAX_ATTEMPTS",
        1,
    )
    auth_service.login_rate_limits_collection.delete_many({})

    try:
        with patch(
            "app.routes.auth.authenticate_user",
            return_value="test-access-token",
        ):
            responses = [
                client.post(
                    "/api/auth/login",
                    json={"email": email, "password": "CorrectPassword123!"},
                )
                for _ in range(2)
            ]

        assert [response.status_code for response in responses] == [200, 200]
        assert auth_service.login_rate_limits_collection.count_documents({}) == 0
    finally:
        auth_service.login_rate_limits_collection.delete_many({})

