import pytest
import re
import time
from app.database.mongodb import db

def test_password_recovery_journey(client, capfd):
    """
    E2E TEST: Simulates a user forgetting their password, verifying an OTP (read from email), 
    resetting the password, and logging back in successfully.
    """
    test_email = "recovery_user@example.com"
    old_password = "OldPassword123!"
    new_password = "NewSecurePassword456!"
    
    # 0. Setup: Clean state & register a verified user
    db.users.delete_one({"email": test_email})
    db.email_otps.delete_many({"email": test_email}) 

    db.password_reset_tokens.delete_many({"email": test_email}) if "password_resets" in db.list_collection_names() else None
    
    client.post("/api/auth/signup", json={"name": "Recovery User", "email": test_email, "password": old_password})
    db.users.update_one({"email": test_email}, {"$set": {"email_verified": True}})
    
    # Clear the captured output buffer before we trigger the forgot-password email
    capfd.readouterr()
    
    # ---------------------------------------------------------
    # PHASE A: Forgot Password Request
    # ---------------------------------------------------------
    forgot_response = client.post("/api/auth/forgot-password", json={"email": test_email})
    assert forgot_response.status_code == 200, f"Forgot password failed: {forgot_response.text}"
    
    # Simulate the user opening their email inbox by capturing the backend's print statement
    captured = capfd.readouterr()
    
    # Use regex to extract the 6-digit OTP from the "[DEV EMAIL]" output
    match = re.search(r"OTP .*?: (\d{6})", captured.out)
    assert match is not None, f"Failed to capture the OTP from the email log! Output was: {captured.out}"
    otp_code = match.group(1)

    # ---------------------------------------------------------
    # PHASE B: Verify OTP
    # ---------------------------------------------------------
    verify_response = client.post(
        "/api/auth/verify-reset-otp", 
        json={"email": test_email, "otp": otp_code}
    )
    assert verify_response.status_code == 200, f"OTP Verification failed: {verify_response.text}"
    reset_token = verify_response.json().get("reset_token")
    assert reset_token is not None, "API did not return a reset_token!"

    # ---------------------------------------------------------
    # PHASE C: Reset Password
    # ---------------------------------------------------------
    reset_response = client.post(
        "/api/auth/reset-password", 
        json={"reset_token": reset_token, "new_password": new_password}
    )
    assert reset_response.status_code == 200, f"Password Reset failed: {reset_response.text}"

    # ---------------------------------------------------------
    # PHASE D: Verify New Password Works
    # ---------------------------------------------------------
    login_response = client.post(
        "/api/auth/login", 
        json={"email": test_email, "password": new_password}
    )
    assert login_response.status_code == 200, "Login with the NEW password failed!"

@pytest.mark.skip(reason="Blocked: Awaiting backend lead to allow unauthenticated requests on /logout to clear dead cookies")
def test_logout_with_expired_or_invalid_token(client):
    # 1. Manually inject a fake, invalid, or expired token into the test client's cookies
    client.cookies.set("access_token", "eyJhbGciOiJIUzI1NiIsInR5cCI.fake.token")
    
    # 2. Attempt to log out
    response = client.post("/api/auth/logout")
    
    # 3. The backend should handle this gracefully, returning 200 OK 
    # and actively commanding the browser to delete the cookie
    assert response.status_code == 200
    
    # 4. Verify the cookie is actually cleared (value is empty or max-age is <= 0)
    assert "access_token" in response.cookies
    assert response.cookies["access_token"].value == '""' or response.cookies["access_token"].value == ""


def test_account_management_and_teardown_journey(client):
    """
    E2E TEST: Simulates a user changing their password, reading their profile, 
    and finally deleting their account (ensuring cascade deletion of resume data).
    """
    test_email = "teardown_user@example.com"
    initial_password = "InitialPassword123!"
    updated_password = "UpdatedPassword456!"
    
    # 0. Setup: Clean state & register a verified user
    db.users.delete_one({"email": test_email})
    db.resumes.delete_many({"user_email": test_email})
    
    client.post("/api/auth/signup", json={"name": "Teardown User", "email": test_email, "password": initial_password})
    db.users.update_one({"email": test_email}, {"$set": {"email_verified": True}})
    
    # 1. Login to establish session
    client.post("/api/auth/login", json={"email": test_email, "password": initial_password})
    db.resumes.insert_one({"user_email": test_email, "skills": [{"name": "Python"}]})

    # ---------------------------------------------------------
    # PHASE A: Change Password
    # ---------------------------------------------------------
    change_pw_response = client.post(
        "/api/users/me/change-password", 
        json={"old_password": initial_password, "new_password": updated_password}
    )
    assert change_pw_response.status_code == 200, f"Change password failed: {change_pw_response.text}"

    # TODO: Backend Lead - Remove time.sleep(1) once DB/JWT timestamp precision mismatch is fixed
    time.sleep(1)  # Ensure the backend has time to invalidate the old session cookie

    # ---------------------------------------------------------
    # PHASE A.5: Re-Authenticate
    # ---------------------------------------------------------
    # The secure backend invalidated the old cookie. We must log in again.
    re_login_response = client.post("/api/auth/login", json={"email": test_email, "password": updated_password})
    assert re_login_response.status_code == 200, "Re-login with updated password failed!"

    # ---------------------------------------------------------
    # PHASE B: Read Profile
    # ---------------------------------------------------------
    profile_response = client.get("/api/users/me")
    assert profile_response.status_code == 200, f"Read profile failed: {profile_response.text}"
    assert profile_response.json().get("email") == test_email

    # ---------------------------------------------------------
    # PHASE C: Account Deletion (Teardown)
    # ---------------------------------------------------------
    delete_response = client.delete("/api/users/me")
    assert delete_response.status_code == 200, f"Account deletion failed: {delete_response.text}"

    # ---------------------------------------------------------
    # PHASE D: Verify Database Wipe (GDPR / Cascade Delete Check)
    # ---------------------------------------------------------
    deleted_user = db.users.find_one({"email": test_email})
    assert deleted_user is None, "VULNERABILITY: User document was not deleted from MongoDB!"
    
    deleted_resumes = db.resumes.find_one({"user_email": test_email})
    assert deleted_resumes is None, "DATA LEAK VULNERABILITY: User's resume data was left behind after account deletion!"



def test_login_immediately_after_password_change(client):
    """Verify old-session invalidation and immediate re-login."""
    test_email = "jwt_test_user@example.com"
    initial_password = "Password123!"
    new_password = "Password456!"

    # Clear data from previous test runs.
    db.users.delete_many({"email": test_email})
    db.email_otps.delete_many({"email": test_email})

    try:
        # Register a fresh user.
        signup_response = client.post(
            "/api/auth/signup",
            json={
                "name": "JWT User",
                "email": test_email,
                "password": initial_password,
            },
        )
        assert signup_response.status_code in (200, 201), signup_response.text

        # Mark the user as verified for this test.
        db.users.update_one(
            {"email": test_email},
            {"$set": {"email_verified": True}},
        )

        # Log in with the original password.
        login_response = client.post(
            "/api/auth/login",
            json={
                "email": test_email,
                "password": initial_password,
            },
        )
        assert login_response.status_code == 200, login_response.text

        # Change the password using the authenticated session.
        change_response = client.post(
            "/api/users/me/change-password",
            json={
                "old_password": initial_password,
                "new_password": new_password,
            },
        )
        assert change_response.status_code == 200, change_response.text

        # Confirm the previous session is invalidated.
        old_session_response = client.get("/api/users/me")
        assert old_session_response.status_code == 401, (
            "The old session was still accepted after the password change."
        )

        # Verify the password-change timestamp was saved.
        user = db.users.find_one({"email": test_email})
        assert user is not None, "User was not found after password change."

        changed_at = user.get("password_changed_at")
        assert changed_at is not None, "password_changed_at was not saved."
        assert changed_at.microsecond == 0, (
            f"Timestamp contains microseconds: {changed_at.microsecond}"
        )

        # Re-login immediately with the new password.
        new_login_response = client.post(
            "/api/auth/login",
            json={
                "email": test_email,
                "password": new_password,
            },
        )
        assert new_login_response.status_code == 200, (
            f"Immediate re-login failed: {new_login_response.text}"
        )

    finally:
        # Clean up test data even if an assertion fails.
        db.users.delete_many({"email": test_email})
        db.email_otps.delete_many({"email": test_email})
