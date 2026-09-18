import os
import secrets
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from app.database.mongodb import db
from app.utils.security import hash_password, verify_password
from app.services.auth_service import users_collection

otp_collection = db["email_otps"]

OTP_EXPIRE_MINUTES = int(os.getenv("OTP_EXPIRE_MINUTES", 10))
OTP_MAX_ATTEMPTS = int(os.getenv("OTP_MAX_ATTEMPTS", 5))
OTP_RESEND_COOLDOWN_SECONDS = int(os.getenv("OTP_RESEND_COOLDOWN_SECONDS", 60))


def generate_otp() -> str:
    return f"{secrets.randbelow(1000000):06d}"


def _check_cooldown(email: str, purpose: str):
    existing = otp_collection.find_one({"email": email, "purpose": purpose})
    if existing:
        elapsed = (datetime.utcnow() - existing["created_at"]).total_seconds()
        if elapsed < OTP_RESEND_COOLDOWN_SECONDS:
            wait_time = int(OTP_RESEND_COOLDOWN_SECONDS - elapsed)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Please wait {wait_time} seconds before requesting another code."
            )


def create_and_send_otp(email: str) -> dict:
    _check_cooldown(email, "email_verification")

    otp = generate_otp()
    otp_hash = hash_password(otp)

    otp_collection.delete_one({"email": email, "purpose": "email_verification"})

    otp_collection.insert_one({
        "email": email,
        "otp_hash": otp_hash,
        "purpose": "email_verification",
        "expires_at": datetime.utcnow() + timedelta(minutes=OTP_EXPIRE_MINUTES),
        "attempts": 0,
        "created_at": datetime.utcnow()
    })

    print(f"[DEV EMAIL] OTP for {email}: {otp}")

    return {"message": "OTP sent to your email."}


def verify_otp(email: str, submitted_otp: str) -> dict:
    record = otp_collection.find_one({"email": email, "purpose": "email_verification"})

    if not record:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No OTP found. Please request a new one.")

    if datetime.utcnow() > record["expires_at"]:
        otp_collection.delete_one({"email": email, "purpose": "email_verification"})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP expired. Please request a new one.")

    if record["attempts"] >= OTP_MAX_ATTEMPTS:
        otp_collection.delete_one({"email": email, "purpose": "email_verification"})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Too many incorrect attempts. Please request a new OTP.")

    if not verify_password(submitted_otp, record["otp_hash"]):
        otp_collection.update_one(
            {"email": email, "purpose": "email_verification"},
            {"$set": {"attempts": record["attempts"] + 1}}
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect OTP.")

    user = users_collection.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    users_collection.update_one({"email": email}, {"$set": {"email_verified": True}})
    otp_collection.delete_one({"email": email, "purpose": "email_verification"})

    return {"message": "Email verified successfully."}


def create_and_send_reset_otp(email: str) -> dict:
    user = users_collection.find_one({"email": email})
    if not user:
        return {"message": "If an account exists, a password reset OTP has been sent."}

    _check_cooldown(email, "password_reset")

    otp = generate_otp()
    otp_hash = hash_password(otp)

    otp_collection.delete_one({"email": email, "purpose": "password_reset"})

    otp_collection.insert_one({
        "email": email,
        "otp_hash": otp_hash,
        "purpose": "password_reset",
        "expires_at": datetime.utcnow() + timedelta(minutes=OTP_EXPIRE_MINUTES),
        "attempts": 0,
        "created_at": datetime.utcnow()
    })

    print(f"[DEV EMAIL] Password reset OTP for {email}: {otp}")

    return {"message": "If an account exists, a password reset OTP has been sent."}


def verify_reset_otp(email: str, submitted_otp: str) -> dict:
    record = otp_collection.find_one({"email": email, "purpose": "password_reset"})

    if not record:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No OTP found. Please request a new one.")

    if datetime.utcnow() > record["expires_at"]:
        otp_collection.delete_one({"email": email, "purpose": "password_reset"})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP expired. Please request a new one.")

    if record["attempts"] >= OTP_MAX_ATTEMPTS:
        otp_collection.delete_one({"email": email, "purpose": "password_reset"})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Too many incorrect attempts. Please request a new OTP.")

    if not verify_password(submitted_otp, record["otp_hash"]):
        otp_collection.update_one(
            {"email": email, "purpose": "password_reset"},
            {"$set": {"attempts": record["attempts"] + 1}}
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect OTP.")

    otp_collection.delete_one({"email": email, "purpose": "password_reset"})

    reset_token = secrets.token_urlsafe(32)
    reset_tokens_collection.insert_one({
        "reset_token": reset_token,
        "email": email,
        "expires_at": datetime.utcnow() + timedelta(minutes=10),
        "used": False
    })

    return {"reset_token": reset_token}


reset_tokens_collection = db["password_reset_tokens"]