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