import os
from fastapi import APIRouter, Response
from app.schemas.auth import (
    SignupRequest, SignupResponse,
    VerifyEmailRequest, ResendOtpRequest, MessageResponse,
    LoginRequest,
    ForgotPasswordRequest, VerifyResetOtpRequest, ResetTokenResponse, ResetPasswordRequest
)
from app.services.auth_service import create_user, authenticate_user, reset_password
from app.services.otp_service import create_and_send_otp, verify_otp, create_and_send_reset_otp, verify_reset_otp
router = APIRouter(prefix="/api/auth", tags=["auth"])

COOKIE_NAME = os.getenv("COOKIE_NAME", "skillbridge_auth")
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"
COOKIE_SAMESITE = os.getenv("COOKIE_SAMESITE", "lax")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", 60))


@router.post("/signup", response_model=SignupResponse)
def signup(payload: SignupRequest):
    result = create_user(payload)
    create_and_send_otp(payload.email)
    return result


@router.post("/verify-email", response_model=MessageResponse)
def verify_email(payload: VerifyEmailRequest):
    return verify_otp(payload.email, payload.otp)


@router.post("/resend-verification-otp", response_model=MessageResponse)
def resend_otp(payload: ResendOtpRequest):
    return create_and_send_otp(payload.email)


@router.post("/login", response_model=MessageResponse)
def login(payload: LoginRequest, response: Response):
    token = authenticate_user(payload.email, payload.password)

    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=JWT_EXPIRE_MINUTES * 60
    )

    return {"message": "Login successful"}
@router.post("/logout", response_model=MessageResponse)
def logout(response: Response):
    response.delete_cookie(key=COOKIE_NAME)
    return {"message": "Logged out successfully."}

@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(payload: ForgotPasswordRequest):
    return create_and_send_reset_otp(payload.email)


@router.post("/verify-reset-otp", response_model=ResetTokenResponse)
def verify_reset_otp_route(payload: VerifyResetOtpRequest):
    return verify_reset_otp(payload.email, payload.otp)


@router.post("/reset-password", response_model=MessageResponse)
def reset_password_route(payload: ResetPasswordRequest):
    return reset_password(payload.reset_token, payload.new_password)