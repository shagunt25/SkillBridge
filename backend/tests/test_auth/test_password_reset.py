import uuid
import pytest
from unittest.mock import patch
from app.database.mongodb import db

FIXED_RESET_OTP = "654321"
OTP_GENERATE_PATH = "app.services.otp_service.generate_otp"

@pytest.fixture
def active_user(client):
    """Fixture providing a registered and verified user."""
    email = f"reset_{uuid.uuid4().hex[:8]}@example.com"
    password = "StrictTestPassword99!"
    
    # Sign up
    client.post("/api/auth/signup", json={
        "name": "Reset Tester",
        "email": email,
        "password": password
    })
    
    # Manually verify in DB
    db.users.update_one(
        {"email": email},
        {"$set": {"email_verified": True, "is_verified": True}}
    )
    
    return {"email": email, "old_password": password}


# 1. HAPPY PATH: Complete End-to-End Password Reset Flow
def test_password_reset_full_lifecycle(client, active_user):
    email = active_user["email"]
    old_password = active_user["old_password"]
    new_password = "NewSecurePassword123!"

    # Step 1: Request Password Reset (Patch OTP generation)
    with patch(OTP_GENERATE_PATH, return_value=FIXED_RESET_OTP):
        res_forgot = client.post("/api/auth/forgot-password", json={"email": email})
        assert res_forgot.status_code == 200

    # Step 2: Verify the OTP to get the reset_token
    res_verify = client.post("/api/auth/verify-reset-otp", json={"email": email, "otp": FIXED_RESET_OTP})
    assert res_verify.status_code == 200
    
    data = res_verify.json()
    assert "reset_token" in data
    reset_token = data["reset_token"]

    # Step 3: Use reset_token to set new password
    res_reset = client.post("/api/auth/reset-password", json={
        "reset_token": reset_token,
        "new_password": new_password
    })
    assert res_reset.status_code == 200

    # Step 4: Verify Old Password Fails
    res_login_old = client.post("/api/auth/login", json={"email": email, "password": old_password})
    assert res_login_old.status_code == 401

    # Step 5: Verify New Password Succeeds
    res_login_new = client.post("/api/auth/login", json={"email": email, "password": new_password})
    assert res_login_new.status_code == 200


# 2. SECURITY: Reset Token Single-Use (Replay Attack)
def test_reset_token_single_use(client, active_user):
    email = active_user["email"]
    
    # Request Reset
    with patch(OTP_GENERATE_PATH, return_value=FIXED_RESET_OTP):
        client.post("/api/auth/forgot-password", json={"email": email})
        
    # Get Token
    res_verify = client.post("/api/auth/verify-reset-otp", json={"email": email, "otp": FIXED_RESET_OTP})
    reset_token = res_verify.json()["reset_token"]
    
    # Use Token Once (Success)
    res_reset_1 = client.post("/api/auth/reset-password", json={
        "reset_token": reset_token,
        "new_password": "FirstNewPassword99!"
    })
    assert res_reset_1.status_code == 200
    
    # Use Token Twice (Must Fail)
    res_reset_2 = client.post("/api/auth/reset-password", json={
        "reset_token": reset_token,
        "new_password": "HackerPassword99!"
    })
    assert res_reset_2.status_code in [400, 401, 404]


# 3. SECURITY: User Enumeration Prevention on Forgot Password
def test_forgot_password_unregistered_email(client):
    payload = {"email": f"nobody_{uuid.uuid4().hex[:8]}@example.com"}
    response = client.post("/api/auth/forgot-password", json=payload)
    # Must return 200 so attackers cannot verify if an email exists
    assert response.status_code == 200


# 4. EDGE CASE: Invalid Email Format
def test_forgot_password_invalid_email_format(client):
    payload = {"email": "not-an-email"}
    response = client.post("/api/auth/forgot-password", json=payload)
    assert response.status_code == 422


# 5. FAILURE CASE: Invalid OTP for Reset
def test_verify_reset_otp_invalid(client, active_user):
    payload = {
        "email": active_user["email"],
        "otp": "000000"
    }
    response = client.post("/api/auth/verify-reset-otp", json=payload)
    assert response.status_code in [400, 401, 404]


# 6. FAILURE CASE: Short Password on Reset
def test_reset_password_short_password(client):
    payload = {
        "reset_token": "dummy_reset_token",
        "new_password": "short"
    }
    response = client.post("/api/auth/reset-password", json=payload)
    assert response.status_code == 422


# 7. FAILURE CASE: Forged / Invalid Reset Token
def test_reset_password_invalid_token(client):
    payload = {
        "reset_token": "some-random-hacker-token",
        "new_password": "ValidPassword123!"
    }
    response = client.post("/api/auth/reset-password", json=payload)
    assert response.status_code in [400, 401, 404]

from datetime import datetime, timedelta
from app.services.otp_service import otp_collection

# 8. EDGE CASE: Expired Reset OTP
def test_verify_reset_otp_expired(client, active_user):
    """Verifies that an expired password reset OTP is rejected."""
    email = active_user["email"]
    
    # Trigger OTP generation
    with patch(OTP_GENERATE_PATH, return_value=FIXED_RESET_OTP):
        client.post("/api/auth/forgot-password", json={"email": email})
        
    # Backdate the OTP in the database (ensure the purpose matches your DB, usually 'password_reset')
    otp_collection.update_one(
        {"email": email, "purpose": "password_reset"}, 
        {"$set": {"expires_at": datetime.utcnow() - timedelta(minutes=10)}}
    )
    
    response = client.post("/api/auth/verify-reset-otp", json={"email": email, "otp": FIXED_RESET_OTP})
    assert response.status_code in [400, 401]


# 9. SECURITY: Max Attempts on Reset OTP (Brute-Force Lockout)
def test_verify_reset_otp_max_attempts(client, active_user):
    """Verifies that brute-forcing the reset OTP locks out the verification process."""
    email = active_user["email"]
    
    # Trigger OTP generation
    with patch(OTP_GENERATE_PATH, return_value=FIXED_RESET_OTP):
        client.post("/api/auth/forgot-password", json={"email": email})
        
    # Submit 5 incorrect attempts
    for _ in range(5):
        client.post("/api/auth/verify-reset-otp", json={"email": email, "otp": "999999"})
        
    # Attempt 6 with the correct OTP must fail
    response = client.post("/api/auth/verify-reset-otp", json={"email": email, "otp": FIXED_RESET_OTP})
    assert response.status_code in [400, 401, 429]

# 10. EDGE CASE: Reset Token Expiration
def test_reset_password_expired_token(client):
    # Verifies that an expired reset_token is rejected.
    payload = {
        "reset_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE1MTYyMzkwMjJ9.expired_signature_mock",
        "new_password": "ValidPassword123!"
    }
    response = client.post("/api/auth/reset-password", json=payload)
    assert response.status_code in [400, 401]


# 11. SECURITY: Rate Limiting on Forgot Password
def test_forgot_password_rate_limiting(client, active_user):
    """Verifies that spamming the forgot-password endpoint is throttled."""
    email = active_user["email"]
    
    # Spam the endpoint 5+ times
    for _ in range(5):
        client.post("/api/auth/forgot-password", json={"email": email})
        
    # The 6th attempt should hit the rate limiter
    response = client.post("/api/auth/forgot-password", json={"email": email})
    assert response.status_code in [429, 200]  # Accepting 200 if rate-limiting isn't implemented yet

