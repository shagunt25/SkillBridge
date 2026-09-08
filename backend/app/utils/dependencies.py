import os
from fastapi import Cookie, HTTPException, status
from app.utils.security import decode_access_token
from app.services.auth_service import users_collection

COOKIE_NAME = os.getenv("COOKIE_NAME", "skillbridge_auth")


def get_current_user(skillbridge_auth: str | None = Cookie(default=None, alias=None)):
    token = skillbridge_auth

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated."
        )

    try:
        payload = decode_access_token(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session. Please log in again."
        )

    email = payload.get("sub")
    user = users_collection.find_one({"email": email})

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found."
        )

    return user