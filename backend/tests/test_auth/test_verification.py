import uuid
import pytest
from unittest.mock import patch
from app.database.mongodb import db
from datetime import datetime, timedelta
from app.services.otp_service import otp_collection

FIXED_TEST_OTP = "123456"
OTP_GENERATE_PATH = "app.services.otp_service.generate_otp"


@pytest.fixture
def unverified_user(client):
    """Fixture providing a fresh, unverified registered user with a deterministic OTP."""
    email = f"verify_{uuid.uuid4().hex[:8]}@example.com"
    password = "StrictTestPassword99!"

    # Patch OTP generation so the plain OTP is known in the test
    with patch(OTP_GENERATE_PATH, return_value=FIXED_TEST_OTP):
        signup_res = client.post("/api/auth/signup", json={
            "name": "Verification Tester",
            "email": email,
            "password": password
        })
        assert signup_res.status_code in [200, 201]

    return {"email": email, "password": password, "otp": FIXED_TEST_OTP}


# 1. HAPPY PATH: Complete Verification Lifecycle & DB State Assertion
def test_verify_email_success(client, unverified_user):
    """Verifies that submitting the valid OTP successfully verifies the user in DB."""
    email = unverified_user["email"]
    otp = unverified_user["otp"]

    # Submit valid verification request
    payload = {"email": email, "otp": otp}
    response = client.post("/api/auth/verify-email", json=payload)
    assert response.status_code == 200

    # Assert database state transitioned to email_verified == True
    updated_user = db.users.find_one({"email": email})
    assert updated_user is not None
    assert updated_user.get("email_verified") is True


# 2. EDGE CASE: OTP Replay Attack / Single-Use Check
def test_verify_email_otp_single_use(client, unverified_user):
    """Verifies that an OTP cannot be reused once it has already been used to verify."""
    email = unverified_user["email"]
    otp = unverified_user["otp"]

    # First attempt - success
    res_first = client.post("/api/auth/verify-email", json={"email": email, "otp": otp})
    assert res_first.status_code == 200

    # Second attempt with the exact same OTP - must fail
    res_second = client.post("/api/auth/verify-email", json={"email": email, "otp": otp})
    assert res_second.status_code in [400, 401, 404]


# 3. FAILURE CASE: Incorrect OTP
def test_verify_email_invalid_otp(client, unverified_user):
    """Verifies that a wrong OTP fails validation."""
    payload = {
        "email": unverified_user["email"],
        "otp": "000000"
    }
    response = client.post("/api/auth/verify-email", json=payload)
    assert response.status_code in [400, 401]


# 4. FAILURE CASE: Schema Validation / Invalid OTP Length
def test_verify_email_invalid_otp_length(client, unverified_user):
    """Verifies that Pydantic enforces the 6-character length constraint."""
    payload = {
        "email": unverified_user["email"],
        "otp": "123"  # Only 3 characters
    }
    response = client.post("/api/auth/verify-email", json=payload)
    assert response.status_code == 422


# 5. HAPPY PATH: Resend OTP
def test_resend_otp_success(client, unverified_user):
    """Verifies that resend OTP succeeds or is gracefully throttled."""
    payload = {"email": unverified_user["email"]}
    response = client.post("/api/auth/resend-verification-otp", json=payload)
    assert response.status_code in [200, 429]


# 6. SECURITY: Account Enumeration Prevention on Resend
def test_resend_otp_unregistered_email(client):
    """Verifies that requesting OTP for a non-existent email returns 200 to prevent user enumeration."""
    payload = {"email": f"ghost_{uuid.uuid4().hex[:8]}@example.com"}
    response = client.post("/api/auth/resend-verification-otp", json=payload)
    assert response.status_code == 200


# 7. EDGE CASE: Expired OTP
def test_verify_email_expired_otp(client, unverified_user):
    """Verifies that an OTP whose expires_at has passed is rejected."""
    email = unverified_user["email"]
    otp = unverified_user["otp"]


    otp_collection.update_one(
        {"email": email, "purpose": "email_verification"},
        {"$set": {"expires_at": datetime.utcnow() - timedelta(minutes=10)}}
    )

    response = client.post("/api/auth/verify-email", json={"email": email, "otp": otp})
    assert response.status_code in [400, 401]


# 8. SECURITY: Max Verification Attempts / Brute-Force Lockout
def test_verify_email_max_attempts_exceeded(client, unverified_user):
    """Verifies that exhausting attempts by repeatedly sending wrong OTPs locks out verification."""
    email = unverified_user["email"]
    real_otp = unverified_user["otp"]

    # Make 5 consecutive wrong OTP attempts through the actual API
    for _ in range(5):
        client.post("/api/auth/verify-email", json={"email": email, "otp": "999999"})

    # Even with the correct OTP, it must now be rejected due to attempt exhaustion or lockout
    response = client.post("/api/auth/verify-email", json={"email": email, "otp": real_otp})
    assert response.status_code in [400, 401, 429]

# 9. EDGE CASE: Alphabetic / Alphanumeric OTP
def test_verify_email_alphanumeric_otp(client, unverified_user):
    """Verifies that non-numeric characters in OTP are rejected."""
    payload = {
        "email": unverified_user["email"],
        "otp": "ABCDEF"
    }
    response = client.post("/api/auth/verify-email", json=payload)
    assert response.status_code in [400, 401, 422]


# 10. EDGE CASE: Verifying an Already Verified User
def test_verify_email_already_verified(client, unverified_user):
    """Verifies handling when a user attempts to verify an already verified account."""
    email = unverified_user["email"]
    otp = unverified_user["otp"]

    # 1. Verify once
    first_res = client.post("/api/auth/verify-email", json={"email": email, "otp": otp})
    assert first_res.status_code == 200

    # 2. Re-attempt verification on the same account
    second_res = client.post("/api/auth/verify-email", json={"email": email, "otp": otp})
    assert second_res.status_code in [400, 409, 401, 404]