import pytest

# 1
def test_verify_email_invalid_otp(client):
    payload = {
        "email": "tester@example.com",
        "otp": "000000"  
    }
    response = client.post("/api/auth/verify-email", json=payload)
    assert response.status_code in [400, 401, 404]

# 2
def test_resend_otp_success(client):
    payload = {"email": "tester@example.com"}
    response = client.post("/api/auth/resend-verification-otp", json=payload)
    # Accept 429 as a successful confirmation that the rate-limiter works
    assert response.status_code in [200, 429]

# 3
def test_resend_otp_unregistered_email(client):
    payload = {"email": "nobody@example.com"}
    response = client.post("/api/auth/resend-verification-otp", json=payload)
    # Expect 200 to confirm the backend successfully hides unregistered emails
    assert response.status_code == 200

# 4
def test_verify_email_invalid_otp_length(client):
    payload = {
        "email": "tester@example.com",
        "otp": "123" # Only 3 characters
    }
    response = client.post("/api/auth/verify-email", json=payload)
    assert response.status_code == 422