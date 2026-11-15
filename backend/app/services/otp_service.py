
import logging
import os
import secrets
import smtplib
import ssl
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from email.utils import formataddr

from fastapi import HTTPException, status

from app.database.mongodb import db
from app.utils.security import hash_password, verify_password
from app.services.auth_service import users_collection


logger = logging.getLogger(__name__)


def utc_now() -> datetime:
    """Return naive UTC time for compatibility with MongoDB's default datetime handling."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


otp_collection = db["email_otps"]

OTP_EXPIRE_MINUTES = int(os.getenv("OTP_EXPIRE_MINUTES", 10))
OTP_MAX_ATTEMPTS = int(os.getenv("OTP_MAX_ATTEMPTS", 5))
OTP_RESEND_COOLDOWN_SECONDS = int(os.getenv("OTP_RESEND_COOLDOWN_SECONDS", 60))
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "smtp").strip().lower()
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com").strip()
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "").strip()
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").strip()
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "").strip()
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "SkillBridge").strip()
SMTP_TIMEOUT_SECONDS = int(os.getenv("SMTP_TIMEOUT_SECONDS", 10))


def generate_otp() -> str:
    return f"{secrets.randbelow(1000000):06d}"


def _send_otp_email(email: str, otp: str, purpose: str) -> None:
    if EMAIL_BACKEND == "console":
        label = "OTP" if purpose == "email_verification" else "Password reset OTP"
        print(f"[DEV EMAIL] {label} for {email}: {otp}")
        return

    if EMAIL_BACKEND != "smtp":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Email delivery is misconfigured.",
        )

    from_email = SMTP_FROM_EMAIL or SMTP_USERNAME
    if not all((SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD, from_email)):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SMTP email settings are incomplete.",
        )

    if purpose == "email_verification":
        subject = "Verify your SkillBridge email"
        action = "verify your email address"
    elif purpose == "password_reset":
        subject = "Your SkillBridge password reset code"
        action = "reset your password"
    else:
        raise ValueError(f"Unsupported OTP purpose: {purpose}")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = formataddr((SMTP_FROM_NAME, from_email))
    message["To"] = email
    message.set_content(
        f"Your SkillBridge code to {action} is {otp}.\n\n"
        f"This code expires in {OTP_EXPIRE_MINUTES} minutes. "
        "If you did not request it, you can ignore this email."
    )

    try:
        with smtplib.SMTP(
            SMTP_HOST,
            SMTP_PORT,
            timeout=SMTP_TIMEOUT_SECONDS,
        ) as server:
            server.ehlo()
            server.starttls(context=ssl.create_default_context())
            server.ehlo()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(message)
    except (OSError, smtplib.SMTPException) as exc:
        logger.exception("Failed to send OTP email")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Email delivery is temporarily unavailable. Please try again.",
        ) from exc


def _check_cooldown(email: str, purpose: str):
    existing = otp_collection.find_one({"email": email, "purpose": purpose})

    if existing:
        elapsed = (utc_now() - existing["created_at"]).total_seconds()

        if elapsed < OTP_RESEND_COOLDOWN_SECONDS:
            wait_time = int(OTP_RESEND_COOLDOWN_SECONDS - elapsed)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Please wait {wait_time} seconds before requesting another code."
            )


def _get_otp_record(email: str, purpose: str) -> dict:
    record = otp_collection.find_one({"email": email, "purpose": purpose})

    if not record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No OTP found. Please request a new one."
        )

    if utc_now() >= record["expires_at"]:
        otp_collection.delete_one({"_id": record["_id"]})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP expired. Please request a new one."
        )

    if record.get("attempts", 0) >= OTP_MAX_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Too many incorrect attempts. Please request a new OTP."
        )

    return record


def _raise_current_otp_state(email: str, purpose: str) -> None:
    record = otp_collection.find_one({"email": email, "purpose": purpose})

    if not record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No OTP found. Please request a new one."
        )

    if utc_now() >= record["expires_at"]:
        otp_collection.delete_one({"_id": record["_id"]})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP expired. Please request a new one."
        )

    if record.get("attempts", 0) >= OTP_MAX_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Too many incorrect attempts. Please request a new OTP."
        )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="OTP is no longer valid. Please request a new one."
    )


def _record_incorrect_otp(record: dict, email: str, purpose: str) -> None:
    result = otp_collection.update_one(
        {
            "_id": record["_id"],
            "attempts": {"$lt": OTP_MAX_ATTEMPTS},
            "expires_at": {"$gt": utc_now()},
        },
        {"$inc": {"attempts": 1}}
    )

    if result.modified_count != 1:
        _raise_current_otp_state(email, purpose)

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Incorrect OTP."
    )


def _consume_otp(record: dict, email: str, purpose: str) -> None:
    result = otp_collection.delete_one(
        {
            "_id": record["_id"],
            "attempts": {"$lt": OTP_MAX_ATTEMPTS},
            "expires_at": {"$gt": utc_now()},
        }
    )

    if result.deleted_count != 1:
        _raise_current_otp_state(email, purpose)


def create_and_send_otp(email: str) -> dict:
    _check_cooldown(email, "email_verification")

    otp = generate_otp()
    otp_hash = hash_password(otp)

    otp_collection.delete_one({
        "email": email,
        "purpose": "email_verification"
    })

    result = otp_collection.insert_one({
        "email": email,
        "otp_hash": otp_hash,
        "purpose": "email_verification",
        "expires_at": utc_now() + timedelta(minutes=OTP_EXPIRE_MINUTES),
        "attempts": 0,
        "created_at": utc_now()
    })

    try:
        _send_otp_email(email, otp, "email_verification")
    except HTTPException:
        otp_collection.delete_one({"_id": result.inserted_id})
        raise

    return {"message": "OTP sent to your email."}


def verify_otp(email: str, submitted_otp: str) -> dict:
    purpose = "email_verification"
    record = _get_otp_record(email, purpose)

    if not verify_password(submitted_otp, record["otp_hash"]):
        _record_incorrect_otp(record, email, purpose)

    user = users_collection.find_one({"email": email})

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    _consume_otp(record, email, purpose)

    users_collection.update_one(
        {"email": email},
        {"$set": {"email_verified": True}}
    )

    return {"message": "Email verified successfully."}


def create_and_send_reset_otp(email: str) -> dict:
    user = users_collection.find_one({"email": email})

    if not user:
        return {
            "message": "If an account exists, a password reset OTP has been sent."
        }

    _check_cooldown(email, "password_reset")

    otp = generate_otp()
    otp_hash = hash_password(otp)

    otp_collection.delete_one({
        "email": email,
        "purpose": "password_reset"
    })

    result = otp_collection.insert_one({
        "email": email,
        "otp_hash": otp_hash,
        "purpose": "password_reset",
        "expires_at": utc_now() + timedelta(minutes=OTP_EXPIRE_MINUTES),
        "attempts": 0,
        "created_at": utc_now()
    })

    try:
        _send_otp_email(email, otp, "password_reset")
    except HTTPException:
        otp_collection.delete_one({"_id": result.inserted_id})
        raise

    return {
        "message": "If an account exists, a password reset OTP has been sent."
    }


def verify_reset_otp(email: str, submitted_otp: str) -> dict:
    purpose = "password_reset"
    record = _get_otp_record(email, purpose)

    if not verify_password(submitted_otp, record["otp_hash"]):
        _record_incorrect_otp(record, email, purpose)

    _consume_otp(record, email, purpose)

    reset_token = secrets.token_urlsafe(32)

    reset_tokens_collection.insert_one({
        "reset_token": reset_token,
        "email": email,
        "expires_at": utc_now() + timedelta(minutes=10),
        "used": False
    })

    return {"reset_token": reset_token}


reset_tokens_collection = db["password_reset_tokens"]
