

import os

from fastapi import Cookie, HTTPException, status

from app.utils.security import decode_access_token
from app.services.auth_service import users_collection

COOKIE_NAME = os.getenv("COOKIE_NAME", "skillbridge_auth")


def get_current_user(
    skillbridge_auth: str | None = Cookie(
        default=None,
        alias=COOKIE_NAME,
    ),
):
    token = skillbridge_auth

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated.",
        )

    try:
        payload = decode_access_token(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session. Please log in again.",
        )

    email = payload.get("sub")

    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session.",
        )

    user = users_collection.find_one({"email": email})

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )

    # Tokens issued before session-version support default to version 0.
    token_version = payload.get("sv", 0)
    current_version = user.get("session_version", 0)

    # Reject tokens issued before a password change or reset.
    if (
        not isinstance(token_version, int)
        or isinstance(token_version, bool)
        or not isinstance(current_version, int)
        or isinstance(current_version, bool)
        or token_version != current_version
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "Session expired due to password change. "
                "Please log in again."
            ),
        )

    return user
