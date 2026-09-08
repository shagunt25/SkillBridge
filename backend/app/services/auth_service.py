from datetime import datetime
from fastapi import HTTPException, status
from app.database.mongodb import db
from app.models.user import User
from app.schemas.auth import SignupRequest
from app.utils.security import hash_password

users_collection = db["users"]


def create_user(signup_data: SignupRequest) -> dict:
    existing_user = users_collection.find_one({"email": signup_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists."
        )

    new_user = User(
        name=signup_data.name,
        email=signup_data.email,
        password_hash=hash_password(signup_data.password),
        email_verified=False,
        auth_provider="local"
    )

    user_dict = new_user.model_dump()
    users_collection.insert_one(user_dict)

    return {"message": "Signup successful. Please verify your email.", "email": new_user.email}


from app.utils.security import verify_password, create_access_token


def authenticate_user(email: str, password: str) -> str:
    user = users_collection.find_one({"email": email})

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    if not user.get("email_verified", False):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please verify your email before logging in."
        )

    if not verify_password(password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    return create_access_token(user_id=str(user.get("email")))
def reset_password(reset_token: str, new_password: str) -> dict:
    from app.services.otp_service import reset_tokens_collection

    record = reset_tokens_collection.find_one({"reset_token": reset_token})

    if not record:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token.")

    if record["used"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This reset token has already been used.")

    if datetime.utcnow() > record["expires_at"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reset token expired. Please start over.")

    new_hash = hash_password(new_password)
    users_collection.update_one({"email": record["email"]}, {"$set": {"password_hash": new_hash}})

    reset_tokens_collection.update_one({"reset_token": reset_token}, {"$set": {"used": True}})

    return {"message": "Password reset successful. You can now log in with your new password."}