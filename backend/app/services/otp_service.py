
import logging
import os
import secrets
import smtplib
import ssl
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from email.utils import formataddr
from hashlib import sha256
import math

from fastapi import HTTPException, status

from app.database.mongodb import database_transaction, db
from app.utils.security import hash_password, verify_password
from app.services.auth_service import (
    claim_rate_limit_bucket,
    users_collection,
)
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError


logger = logging.getLogger(__name__)


def utc_now() -> datetime:
    """Return naive UTC time for compatibility with MongoDB's default datetime handling."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


otp_collection = db["email_otps"]
otp_rate_limits_collection = db["otp_rate_limits"]

OTP_EXPIRE_MINUTES = int(os.getenv("OTP_EXPIRE_MINUTES", 10))
OTP_MAX_ATTEMPTS = int(os.getenv("OTP_MAX_ATTEMPTS", 5))
OTP_RESEND_COOLDOWN_SECONDS = int(os.getenv("OTP_RESEND_COOLDOWN_SECONDS", 60))
OTP_RATE_LIMIT_WINDOW_SECONDS = int(
    os.getenv("OTP_RATE_LIMIT_WINDOW_SECONDS", 3600)
)
OTP_RATE_LIMIT_IP_MAX_REQUESTS = int(
    os.getenv("OTP_RATE_LIMIT_IP_MAX_REQUESTS", 10)
)
OTP_RATE_LIMIT_EMAIL_MAX_REQUESTS = int(
    os.getenv("OTP_RATE_LIMIT_EMAIL_MAX_REQUESTS", 5)
)
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


VERIFICATION_OTP_MESSAGE = (
    "If the account exists and needs verification, a code has been sent."
)
PASSWORD_RESET_OTP_MESSAGE = (
    "If an account exists, a password reset OTP has been sent."
)


def _otp_rate_limit_buckets(
    email: str,
    client_ip: str | None,
    now: datetime,
) -> list[tuple[str, int, datetime, bool]]:
    window_start = int(now.timestamp()) // OTP_RATE_LIMIT_WINDOW_SECONDS
    expires_at = datetime.fromtimestamp(
        (window_start + 1) * OTP_RATE_LIMIT_WINDOW_SECONDS,
        tz=timezone.utc,
    ).replace(tzinfo=None)
    email_hash = sha256(email.casefold().encode("utf-8")).hexdigest()
    ip_hash = sha256(
        (client_ip or "unknown").encode("utf-8")
    ).hexdigest()

    return [
        (
            sha256(f"otp-ip:{window_start}:{ip_hash}".encode()).hexdigest(),
            OTP_RATE_LIMIT_IP_MAX_REQUESTS,
            expires_at,
            True,
        ),
        (
            sha256(f"otp-email:{window_start}:{email_hash}".encode()).hexdigest(),
            OTP_RATE_LIMIT_EMAIL_MAX_REQUESTS,
            expires_at,
            False,
        ),
    ]


def _claim_otp_request_limits(email: str, client_ip: str | None) -> bool:
    now = utc_now()
    for bucket_id, max_requests, expires_at, is_ip_bucket in (
        _otp_rate_limit_buckets(email, client_ip, now)
    ):
        bucket = claim_rate_limit_bucket(
            otp_rate_limits_collection,
            bucket_id,
            max_requests,
            expires_at,
        )
        if bucket is None:
            if not is_ip_bucket:
                return False

            retry_after = max(
                1,
                math.ceil(
                    (
                        expires_at
                        - utc_now()
                    ).total_seconds()
                ),
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many code requests. Please try again later.",
                headers={"Retry-After": str(retry_after)},
            )

    return True


def _otp_cooldown_id(email: str, purpose: str) -> str:
    key = f"otp-cooldown:{purpose}:{email.casefold()}"
    return sha256(key.encode("utf-8")).hexdigest()


def _claim_otp_cooldown(
    email: str,
    purpose: str,
) -> datetime | None:
    now = utc_now()
    cooldown_until = now + timedelta(seconds=OTP_RESEND_COOLDOWN_SECONDS)
    cooldown_id = _otp_cooldown_id(email, purpose)

    try:
        claimed = otp_rate_limits_collection.find_one_and_update(
            {
                "_id": cooldown_id,
                "cooldown_until": {"$lte": now},
            },
            {
                "$set": {
                    "cooldown_until": cooldown_until,
                    "expires_at": cooldown_until,
                },
                "$setOnInsert": {"attempts": 0},
            },
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
    except DuplicateKeyError:
        return None

    return (
        claimed["cooldown_until"]
        if claimed is not None
        else None
    )


def _release_otp_cooldown(
    email: str,
    purpose: str,
    cooldown_until: datetime,
) -> None:
    otp_rate_limits_collection.delete_one(
        {
            "_id": _otp_cooldown_id(email, purpose),
            "cooldown_until": cooldown_until,
        }
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


def create_and_send_otp(
    email: str,
    client_ip: str | None = None,
    *,
    suppress_delivery_errors: bool = False,
) -> dict:
    request_allowed = _claim_otp_request_limits(email, client_ip)
    user = users_collection.find_one({"email": email})
    if not request_allowed or not user or user.get("email_verified", False):
        return {"message": VERIFICATION_OTP_MESSAGE}

    cooldown_until = _claim_otp_cooldown(email, "email_verification")
    if cooldown_until is None:
        return {"message": VERIFICATION_OTP_MESSAGE}

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
        _release_otp_cooldown(
            email,
            "email_verification",
            cooldown_until,
        )
        if suppress_delivery_errors:
            return {"message": VERIFICATION_OTP_MESSAGE}
        raise

    return {"message": VERIFICATION_OTP_MESSAGE}


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

    with database_transaction() as session:
        otp_result = otp_collection.delete_one(
            {
                "_id": record["_id"],
                "attempts": {"$lt": OTP_MAX_ATTEMPTS},
                "expires_at": {"$gt": utc_now()},
            },
            session=session,
        )
        if otp_result.deleted_count != 1:
            _raise_current_otp_state(email, purpose)

        user_result = users_collection.update_one(
            {"email": email},
            {"$set": {"email_verified": True}},
            session=session,
        )
        if user_result.matched_count != 1:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

    return {"message": "Email verified successfully."}


def create_and_send_reset_otp(
    email: str,
    client_ip: str | None = None,
) -> dict:
    request_allowed = _claim_otp_request_limits(email, client_ip)
    user = users_collection.find_one({"email": email})

    if not request_allowed or not user:
        return {"message": PASSWORD_RESET_OTP_MESSAGE}

    cooldown_until = _claim_otp_cooldown(email, "password_reset")
    if cooldown_until is None:
        return {"message": PASSWORD_RESET_OTP_MESSAGE}

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
        _release_otp_cooldown(email, "password_reset", cooldown_until)
        return {"message": PASSWORD_RESET_OTP_MESSAGE}

    return {"message": PASSWORD_RESET_OTP_MESSAGE}


def verify_reset_otp(email: str, submitted_otp: str) -> dict:
    purpose = "password_reset"
    record = _get_otp_record(email, purpose)

    if not verify_password(submitted_otp, record["otp_hash"]):
        _record_incorrect_otp(record, email, purpose)

    reset_token = secrets.token_urlsafe(32)
    with database_transaction() as session:
        otp_result = otp_collection.delete_one(
            {
                "_id": record["_id"],
                "attempts": {"$lt": OTP_MAX_ATTEMPTS},
                "expires_at": {"$gt": utc_now()},
            },
            session=session,
        )
        if otp_result.deleted_count != 1:
            _raise_current_otp_state(email, purpose)

        reset_tokens_collection.insert_one(
            {
                "reset_token": reset_token,
                "email": email,
                "expires_at": utc_now() + timedelta(minutes=10),
                "used": False,
            },
            session=session,
        )

    return {"reset_token": reset_token}


reset_tokens_collection = db["password_reset_tokens"]
