from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import uuid
import pytest
from fastapi import HTTPException
from unittest.mock import Mock, patch
from app.database.mongodb import db
from datetime import datetime, timedelta, timezone
from app.services import otp_service
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
        assert signup_res.status_code == 200

    yield {"email": email, "password": password, "otp": FIXED_TEST_OTP}
    db.users.delete_one({"email": email})
    otp_collection.delete_many({"email": email})
    otp_service.otp_rate_limits_collection.delete_many({})


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
    assert res_second.status_code == 400


# 3. FAILURE CASE: Incorrect OTP
def test_verify_email_invalid_otp(client, unverified_user):
    """Verifies that a wrong OTP fails validation."""
    payload = {
        "email": unverified_user["email"],
        "otp": "000000"
    }
    response = client.post("/api/auth/verify-email", json=payload)
    assert response.status_code == 400


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
    """Resending an eligible account sends one new verification code."""
    payload = {"email": unverified_user["email"]}
    email = unverified_user["email"]
    otp_service.otp_rate_limits_collection.delete_one({
        "_id": otp_service._otp_cooldown_id(email, "email_verification")
    })

    with patch(
        "app.services.otp_service._send_otp_email"
    ) as send_email:
        response = client.post("/api/auth/resend-verification-otp", json=payload)

    assert response.status_code == 200
    send_email.assert_called_once()


# 6. SECURITY: Account Enumeration Prevention on Resend
def test_resend_otp_unregistered_email(client):
    """Verifies that requesting OTP for a non-existent email returns 200 to prevent user enumeration."""
    email = f"ghost_{uuid.uuid4().hex[:8]}@example.com"
    payload = {"email": email}
    response = client.post("/api/auth/resend-verification-otp", json=payload)
    assert response.status_code == 200
    assert response.json()["message"] == otp_service.VERIFICATION_OTP_MESSAGE
    assert otp_collection.find_one({"email": email}) is None


def test_resend_otp_delivery_failure_is_generic(client):
    email = f"delivery-failure_{uuid.uuid4().hex}@example.com"
    db.users.insert_one({
        "email": email,
        "email_verified": False,
    })
    cooldown_id = otp_service._otp_cooldown_id(
        email,
        "email_verification",
    )
    otp_service.otp_rate_limits_collection.delete_one({"_id": cooldown_id})

    try:
        unknown_response = client.post(
            "/api/auth/resend-verification-otp",
            json={"email": f"unknown_{uuid.uuid4().hex}@example.com"},
        )
        with patch(
            "app.services.otp_service._send_otp_email",
            side_effect=HTTPException(
                status_code=503,
                detail="Email delivery failed.",
            ),
        ):
            delivery_failure_response = client.post(
                "/api/auth/resend-verification-otp",
                json={"email": email},
            )

        assert delivery_failure_response.status_code == 200
        assert delivery_failure_response.json() == unknown_response.json()
    finally:
        db.users.delete_one({"email": email})
        otp_collection.delete_many({"email": email})
        otp_service.otp_rate_limits_collection.delete_one({"_id": cooldown_id})


def test_otp_cooldown_claim_is_atomic(monkeypatch):
    email = f"cooldown_{uuid.uuid4().hex}@example.com"
    cooldown_id = otp_service._otp_cooldown_id(email, "email_verification")
    otp_service.otp_rate_limits_collection.delete_one({"_id": cooldown_id})

    try:
        with ThreadPoolExecutor(max_workers=12) as executor:
            claims = list(executor.map(
                lambda _: otp_service._claim_otp_cooldown(
                    email,
                    "email_verification",
                ),
                range(12),
            ))

        assert sum(claim is not None for claim in claims) == 1
    finally:
        otp_service.otp_rate_limits_collection.delete_one({"_id": cooldown_id})


def test_otp_requests_are_limited_per_ip(client, monkeypatch):
    monkeypatch.setattr(
        otp_service,
        "OTP_RATE_LIMIT_IP_MAX_REQUESTS",
        2,
    )
    monkeypatch.setattr(
        otp_service,
        "OTP_RATE_LIMIT_EMAIL_MAX_REQUESTS",
        100,
    )
    otp_service.otp_rate_limits_collection.delete_many({})

    try:
        responses = [
            client.post(
                "/api/auth/resend-verification-otp",
                json={"email": f"ip-limit-{uuid.uuid4().hex}@example.com"},
            )
            for _ in range(3)
        ]

        assert [response.status_code for response in responses] == [
            200,
            200,
            429,
        ]
        assert responses[-1].headers["retry-after"].isdigit()
    finally:
        otp_service.otp_rate_limits_collection.delete_many({})


def test_otp_email_limit_is_generic_and_does_not_send(client, monkeypatch):
    email = f"email-limit-{uuid.uuid4().hex}@example.com"
    db.users.insert_one({
        "email": email,
        "email_verified": False,
    })
    monkeypatch.setattr(
        otp_service,
        "OTP_RATE_LIMIT_IP_MAX_REQUESTS",
        100,
    )
    monkeypatch.setattr(
        otp_service,
        "OTP_RATE_LIMIT_EMAIL_MAX_REQUESTS",
        1,
    )
    monkeypatch.setattr(
        otp_service,
        "_claim_otp_cooldown",
        lambda *_args: otp_service.utc_now() + timedelta(seconds=30),
    )
    otp_service.otp_rate_limits_collection.delete_many({})

    try:
        with patch(
            "app.services.otp_service._send_otp_email"
        ) as send_email:
            responses = [
                client.post(
                    "/api/auth/resend-verification-otp",
                    json={"email": email},
                )
                for _ in range(2)
            ]

        assert [response.status_code for response in responses] == [200, 200]
        assert responses[0].json() == responses[1].json()
        send_email.assert_called_once()
    finally:
        db.users.delete_one({"email": email})
        otp_collection.delete_many({"email": email})
        otp_service.otp_rate_limits_collection.delete_many({})


# 7. EDGE CASE: Expired OTP
def test_verify_email_expired_otp(client, unverified_user):
    """Verifies that an OTP whose expires_at has passed is rejected."""
    email = unverified_user["email"]
    otp = unverified_user["otp"]


    otp_collection.update_one(
        {"email": email, "purpose": "email_verification"},
        {
            "$set": {
                "expires_at": (
                    datetime.now(timezone.utc).replace(tzinfo=None)
                    - timedelta(minutes=10)
                )
            }
        }
    )

    response = client.post("/api/auth/verify-email", json={"email": email, "otp": otp})
    assert response.status_code == 400


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
    assert response.status_code == 400


def test_concurrent_incorrect_otp_attempts_are_all_counted(
    client,
    unverified_user,
    monkeypatch,
):
    email = unverified_user["email"]
    barrier = Barrier(2)

    def incorrect_password(_submitted_otp, _otp_hash):
        barrier.wait(timeout=5)
        return False

    monkeypatch.setattr(otp_service, "verify_password", incorrect_password)

    def submit_incorrect_otp():
        with pytest.raises(HTTPException):
            otp_service.verify_otp(email, "000000")

    with ThreadPoolExecutor(max_workers=2) as executor:
        list(executor.map(lambda _: submit_incorrect_otp(), range(2)))

    record = otp_collection.find_one({
        "email": email,
        "purpose": "email_verification",
    })
    assert record["attempts"] == 2


def test_concurrent_valid_otp_is_consumed_once(
    client,
    unverified_user,
    monkeypatch,
):
    email = unverified_user["email"]
    barrier = Barrier(2)

    def valid_password(_submitted_otp, _otp_hash):
        barrier.wait(timeout=5)
        return True

    monkeypatch.setattr(otp_service, "verify_password", valid_password)

    def submit_valid_otp():
        try:
            otp_service.verify_otp(email, unverified_user["otp"])
            return True
        except HTTPException:
            return False

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: submit_valid_otp(), range(2)))

    assert results.count(True) == 1
    assert otp_collection.find_one({
        "email": email,
        "purpose": "email_verification",
    }) is None

# 9. EDGE CASE: Alphabetic / Alphanumeric OTP
def test_verify_email_alphanumeric_otp(client, unverified_user):
    """Verifies that non-numeric characters in OTP are rejected."""
    payload = {
        "email": unverified_user["email"],
        "otp": "ABCDEF"
    }
    response = client.post("/api/auth/verify-email", json=payload)
    assert response.status_code == 400


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
    assert second_res.status_code == 400


def test_smtp_sender_uses_tls_and_sends_otp(monkeypatch):
    monkeypatch.setattr(otp_service, "EMAIL_BACKEND", "smtp")
    monkeypatch.setattr(otp_service, "SMTP_HOST", "smtp.gmail.com")
    monkeypatch.setattr(otp_service, "SMTP_PORT", 587)
    monkeypatch.setattr(otp_service, "SMTP_USERNAME", "skillbridge@example.com")
    monkeypatch.setattr(otp_service, "SMTP_PASSWORD", "test-app-password")
    monkeypatch.setattr(otp_service, "SMTP_FROM_EMAIL", "")
    monkeypatch.setattr(otp_service, "SMTP_FROM_NAME", "SkillBridge")
    monkeypatch.setattr(otp_service, "SMTP_TIMEOUT_SECONDS", 10)

    with patch("app.services.otp_service.smtplib.SMTP") as smtp_factory:
        otp_service._send_otp_email(
            "student@example.com",
            "123456",
            "email_verification",
        )

    smtp_factory.assert_called_once_with(
        "smtp.gmail.com",
        587,
        timeout=10,
    )
    smtp = smtp_factory.return_value.__enter__.return_value
    smtp.starttls.assert_called_once()
    smtp.login.assert_called_once_with(
        "skillbridge@example.com",
        "test-app-password",
    )
    message = smtp.send_message.call_args.args[0]
    assert message["To"] == "student@example.com"
    assert message["From"] == "SkillBridge <skillbridge@example.com>"
    assert "123456" in message.get_content()


def test_failed_smtp_send_removes_unsent_otp(monkeypatch):
    email = f"smtp_failure_{uuid.uuid4().hex[:8]}@example.com"
    db.users.insert_one({
        "email": email,
        "email_verified": False,
    })
    monkeypatch.setattr(otp_service, "EMAIL_BACKEND", "smtp")
    monkeypatch.setattr(otp_service, "SMTP_USERNAME", "skillbridge@example.com")
    monkeypatch.setattr(otp_service, "SMTP_PASSWORD", "test-app-password")
    monkeypatch.setattr(otp_service.smtplib, "SMTP", Mock(side_effect=OSError))

    try:
        with pytest.raises(HTTPException) as error:
            otp_service.create_and_send_otp(email)

        assert error.value.status_code == 503
        assert otp_collection.find_one({
            "email": email,
            "purpose": "email_verification",
        }) is None
    finally:
        db.users.delete_one({"email": email})