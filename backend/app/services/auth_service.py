

import hashlib
import math
import os
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from pymongo import ReturnDocument
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError

from app.database.mongodb import database_transaction, db
from app.models.user import User
from app.schemas.auth import SignupRequest
from app.utils.security import (
    hash_password,
    verify_password,
    create_access_token,
)

users_collection = db["users"]
login_rate_limits_collection = db["login_rate_limits"]
ai_rate_limits_collection = db["ai_rate_limits"]

LOGIN_RATE_LIMIT_WINDOW_SECONDS = int(
    os.getenv("LOGIN_RATE_LIMIT_WINDOW_SECONDS", 900)
)
LOGIN_RATE_LIMIT_EMAIL_IP_MAX_ATTEMPTS = int(
    os.getenv("LOGIN_RATE_LIMIT_EMAIL_IP_MAX_ATTEMPTS", 5)
)
LOGIN_RATE_LIMIT_IP_MAX_ATTEMPTS = int(
    os.getenv("LOGIN_RATE_LIMIT_IP_MAX_ATTEMPTS", 30)
)
AI_RATE_LIMIT_WINDOW_SECONDS = int(
    os.getenv("AI_RATE_LIMIT_WINDOW_SECONDS", 3600)
)
AI_RATE_LIMIT_USER_MAX_REQUESTS = int(
    os.getenv("AI_RATE_LIMIT_USER_MAX_REQUESTS", 20)
)


def _login_rate_limit_buckets(
    email: str,
    client_ip: str | None,
    now: datetime | None = None,
) -> list[tuple[str, int, datetime]]:
    current_time = now or datetime.now(timezone.utc)
    window_start = (
        int(current_time.timestamp()) // LOGIN_RATE_LIMIT_WINDOW_SECONDS
    )
    expires_at = datetime.fromtimestamp(
        (window_start + 1) * LOGIN_RATE_LIMIT_WINDOW_SECONDS,
        tz=timezone.utc,
    ).replace(tzinfo=None)
    email_hash = hashlib.sha256(email.casefold().encode("utf-8")).hexdigest()
    ip_hash = hashlib.sha256(
        (client_ip or "unknown").encode("utf-8")
    ).hexdigest()

    return [
        (
            hashlib.sha256(
                f"email-ip:{window_start}:{email_hash}:{ip_hash}".encode()
            ).hexdigest(),
            LOGIN_RATE_LIMIT_EMAIL_IP_MAX_ATTEMPTS,
            expires_at,
        ),
        (
            hashlib.sha256(
                f"ip:{window_start}:{ip_hash}".encode()
            ).hexdigest(),
            LOGIN_RATE_LIMIT_IP_MAX_ATTEMPTS,
            expires_at,
        ),
    ]


def claim_rate_limit_bucket(
    collection: Collection[dict[str, Any]],
    bucket_id: str,
    max_attempts: int,
    expires_at: datetime,
) -> dict | None:
    query = {
        "_id": bucket_id,
        "attempts": {"$lt": max_attempts},
    }
    update = {
        "$inc": {"attempts": 1},
        "$setOnInsert": {"expires_at": expires_at},
    }

    try:
        return collection.find_one_and_update(
            query,
            update,
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
    except DuplicateKeyError:
        return collection.find_one_and_update(
            query,
            update,
            return_document=ReturnDocument.AFTER,
        )


def release_rate_limit_bucket(
    collection: Collection[dict[str, Any]],
    bucket_id: str,
) -> None:
    collection.update_one(
        {"_id": bucket_id, "attempts": {"$gt": 0}},
        {"$inc": {"attempts": -1}},
    )
    collection.delete_one({"_id": bucket_id, "attempts": 0})


def reserve_login_attempt(email: str, client_ip: str | None) -> list[str]:
    now = datetime.now(timezone.utc)
    buckets = _login_rate_limit_buckets(email, client_ip, now)
    claimed_buckets = []

    for bucket_id, max_attempts, expires_at in buckets:
        bucket = claim_rate_limit_bucket(
            login_rate_limits_collection,
            bucket_id,
            max_attempts,
            expires_at,
        )
        if bucket is None:
            for claimed_bucket_id in claimed_buckets:
                release_rate_limit_bucket(
                    login_rate_limits_collection,
                    claimed_bucket_id,
                )

            retry_after = max(
                1,
                math.ceil(
                    (
                        expires_at
                        - datetime.now(timezone.utc).replace(tzinfo=None)
                    ).total_seconds()
                ),
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many failed login attempts. Please try again later.",
                headers={"Retry-After": str(retry_after)},
            )

        claimed_buckets.append(bucket_id)

    return claimed_buckets


def release_login_attempt(bucket_ids: list[str]) -> None:
    for bucket_id in bucket_ids:
        release_rate_limit_bucket(login_rate_limits_collection, bucket_id)


def reserve_ai_request(user_email: str) -> None:
    now = datetime.now(timezone.utc)
    window_start = int(now.timestamp()) // AI_RATE_LIMIT_WINDOW_SECONDS
    expires_at = datetime.fromtimestamp(
        (window_start + 1) * AI_RATE_LIMIT_WINDOW_SECONDS,
        tz=timezone.utc,
    ).replace(tzinfo=None)
    user_hash = hashlib.sha256(
        user_email.casefold().encode("utf-8")
    ).hexdigest()
    bucket_id = hashlib.sha256(
        f"ai:{window_start}:{user_hash}".encode()
    ).hexdigest()

    if claim_rate_limit_bucket(
        ai_rate_limits_collection,
        bucket_id,
        AI_RATE_LIMIT_USER_MAX_REQUESTS,
        expires_at,
    ) is None:
        retry_after = max(
            1,
            math.ceil(
                (
                    expires_at
                    - datetime.now(timezone.utc).replace(tzinfo=None)
                ).total_seconds()
            ),
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="AI request limit reached. Please try again later.",
            headers={"Retry-After": str(retry_after)},
        )


def create_user(signup_data: SignupRequest) -> dict:
    existing_user = users_collection.find_one(
        {"email": signup_data.email}
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    new_user = User(
        name=signup_data.name,
        email=signup_data.email,
        password_hash=hash_password(signup_data.password),
        email_verified=False,
        auth_provider="local",
    )

    user_dict = new_user.model_dump()
    user_dict.setdefault("session_version", 0)

    try:
        users_collection.insert_one(user_dict)
    except DuplicateKeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        ) from exc

    return {
        "message": "Signup successful. Please verify your email.",
        "email": new_user.email,
    }


def authenticate_user(email: str, password: str) -> str:
    user = users_collection.find_one({"email": email})

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not user.get("email_verified", False):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please verify your email before logging in.",
        )

    if not verify_password(password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    return create_access_token(
        user_id=str(user.get("email")),
        session_version=int(user.get("session_version", 0)),
    )


def reset_password(reset_token: str, new_password: str) -> dict:
    from app.services.otp_service import (
        reset_tokens_collection,
        utc_now,
    )

    record = reset_tokens_collection.find_one(
        {"reset_token": reset_token}
    )

    if not record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token.",
        )

    if record.get("used", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This reset token has already been used.",
        )

    if utc_now() >= record["expires_at"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token expired. Please start over.",
        )

    if not users_collection.find_one({"email": record["email"]}):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    new_hash = hash_password(new_password)
    password_changed_at = datetime.now(timezone.utc).replace(
        microsecond=0
    )

    with database_transaction() as session:
        token_claim = reset_tokens_collection.update_one(
            {
                "_id": record["_id"],
                "used": False,
                "expires_at": {"$gt": utc_now()},
            },
            {"$set": {"used": True}},
            session=session,
        )

        if token_claim.modified_count != 1:
            current_record = reset_tokens_collection.find_one(
                {"_id": record["_id"]},
                session=session,
            )

            if current_record and current_record.get("used", False):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This reset token has already been used.",
                )

            if current_record and utc_now() >= current_record["expires_at"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Reset token expired. Please start over.",
                )

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token.",
            )

        password_update = users_collection.update_one(
            {"email": record["email"]},
            {
                "$set": {
                    "password_hash": new_hash,
                    "password_changed_at": password_changed_at,
                },
                "$inc": {"session_version": 1},
            },
            session=session,
        )

        if password_update.matched_count != 1:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

    return {
        "message": (
            "Password reset successful. "
            "You can now log in with your new password."
        )
    }


def change_password(
    user_email: str,
    old_password: str,
    new_password: str,
) -> dict:
    user = users_collection.find_one({"email": user_email})

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    if not verify_password(old_password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect.",
        )

    new_hash = hash_password(new_password)
    password_changed_at = datetime.now(timezone.utc).replace(
        microsecond=0
    )

    users_collection.update_one(
        {"email": user_email},
        {
            "$set": {
                "password_hash": new_hash,
                "password_changed_at": password_changed_at,
            },
            "$inc": {"session_version": 1},
        },
    )

    return {
        "message": "Password changed successfully. Please log in again."
    }


def delete_account(user_email: str) -> dict:
    with database_transaction() as session:
        result = users_collection.delete_one(
            {"email": user_email},
            session=session,
        )

        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        db.resumes.delete_many(
            {"user_email": user_email},
            session=session,
        )
        db.targets.delete_many(
            {"user_email": user_email},
            session=session,
        )
        db.roadmaps.delete_many(
            {"user_email": user_email},
            session=session,
        )
        db.email_otps.delete_many({"email": user_email}, session=session)
        db.password_reset_tokens.delete_many(
            {"email": user_email},
            session=session,
        )

    return {"message": "Account deleted successfully."}
