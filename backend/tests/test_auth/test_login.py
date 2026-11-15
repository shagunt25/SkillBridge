from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.database.mongodb import db
from app.services import auth_service
from app.utils.security import hash_password

LOGIN_CREDENTIALS = {
    "email": "tester@example.com",
    "password": "StrictTestPassword99!"
}

@pytest.fixture
def verified_login_user():
    email = f"login-{uuid4().hex}@example.com"
    password = LOGIN_CREDENTIALS["password"]
    db.users.insert_one({
        "name": "Login Test User",
        "email": email,
        "password_hash": hash_password(password),
        "email_verified": True,
        "session_version": 0,
    })
    yield {"email": email, "password": password}
    db.users.delete_one({"email": email})


def test_login_success(client, verified_login_user):
    response = client.post(
        "/api/auth/login",
        json=verified_login_user,
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Login successful"}
    assert "skillbridge_auth=" in response.headers["set-cookie"]
    assert "httponly" in response.headers["set-cookie"].lower()


def test_login_wrong_password(client, verified_login_user):
    payload = {
        "email": verified_login_user["email"],
        "password": "WrongPassword999!"
    }
    response = client.post("/api/auth/login", json=payload)
    assert response.status_code == 401

def test_login_unregistered_email(client):
    payload = {
        "email": "nobody@example.com",
        "password": "SomePassword123!"
    }
    response = client.post("/api/auth/login", json=payload)
    assert response.status_code == 401

def test_login_wrong_http_method(client):
    """Test that the API rejects incorrect HTTP methods (GET instead of POST)."""
    response = client.get("/api/auth/login") 
    assert response.status_code == 405

def test_login_missing_password(client):
    """Test that omitting a required field triggers a validation error."""
    payload = {
        "email": "tester@example.com"
        # Password field is completely missing
    }
    response = client.post("/api/auth/login", json=payload)
    
    assert response.status_code == 422

def test_login_email_with_whitespace(client, verified_login_user):
    payload = {
        "email": f"  {verified_login_user['email']}  ",
        "password": verified_login_user["password"]
    }
    response = client.post("/api/auth/login", json=payload)

    assert response.status_code == 200

def test_login_email_case_insensitive(client, verified_login_user):
    payload = {
        "email": verified_login_user["email"].upper(),
        "password": verified_login_user["password"]
    }
    response = client.post("/api/auth/login", json=payload)
    
    assert response.status_code == 200


def test_login_empty_password(client, verified_login_user):
    """Test that empty strings are rejected even if the field is present."""
    payload = {
        "email": verified_login_user["email"],
        "password": ""  # Field exists, but is empty
    }
    response = client.post("/api/auth/login", json=payload)
    
    assert response.status_code == 401

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


def test_concurrent_login_attempts_cannot_exceed_reserved_limit(monkeypatch):
    email = f"concurrent-rate-limit-{uuid4().hex}@example.com"
    client_ip = f"192.0.2.{uuid4().int % 250 + 1}"
    monkeypatch.setattr(
        auth_service,
        "LOGIN_RATE_LIMIT_EMAIL_IP_MAX_ATTEMPTS",
        3,
    )
    monkeypatch.setattr(
        auth_service,
        "LOGIN_RATE_LIMIT_IP_MAX_ATTEMPTS",
        100,
    )
    bucket_ids = [
        bucket_id
        for bucket_id, _, _ in auth_service._login_rate_limit_buckets(
            email,
            client_ip,
        )
    ]
    auth_service.login_rate_limits_collection.delete_many(
        {"_id": {"$in": bucket_ids}}
    )

    def reserve_attempt():
        try:
            return auth_service.reserve_login_attempt(email, client_ip)
        except HTTPException as exc:
            assert exc.status_code == 429
            return None

    try:
        with ThreadPoolExecutor(max_workers=12) as executor:
            reservations = list(executor.map(lambda _: reserve_attempt(), range(12)))

        accepted = [reservation for reservation in reservations if reservation]
        assert len(accepted) == 3
    finally:
        auth_service.login_rate_limits_collection.delete_many(
            {"_id": {"$in": bucket_ids}}
        )

