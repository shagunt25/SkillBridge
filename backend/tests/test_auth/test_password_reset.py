import pytest

# 1
def test_forgot_password_success(client):
    payload = {"email": "tester@example.com"}
    response = client.post("/api/auth/forgot-password", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "message" in data

# 2
def test_forgot_password_invalid_email_format(client):
    payload = {"email": "not-an-email"}
    response = client.post("/api/auth/forgot-password", json=payload)
    assert response.status_code == 422

# 3
def test_verify_reset_otp_invalid(client):
    payload = {
        "email": "tester@example.com",
        "otp": "000000"
    }
    response = client.post("/api/auth/verify-reset-otp", json=payload)
    assert response.status_code in [400, 401, 404]

# 4
def test_reset_password_short_password(client):
    # Schema requires new_password to be at least 8 characters
    payload = {
        "reset_token": "dummy_reset_token",
        "new_password": "short"
    }
    response = client.post("/api/auth/reset-password", json=payload)
    assert response.status_code == 422

# 5
def test_reset_password_invalid_token(client):
    """Test that a fake or expired reset token is rejected."""
    payload = {
        "reset_token": "some-random-hacker-token",
        "new_password": "ValidPassword123!"
    }
    response = client.post("/api/auth/reset-password", json=payload)
    
    # Should block the reset attempt
    assert response.status_code in [400, 401, 404]

