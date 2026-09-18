from fastapi import APIRouter, Depends
from app.schemas.auth import UserResponse, ChangePasswordRequest, MessageResponse
from app.services.auth_service import change_password, delete_account
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: dict = Depends(get_current_user)):
    return current_user


@router.post("/me/change-password", response_model=MessageResponse)
def change_my_password(payload: ChangePasswordRequest, current_user: dict = Depends(get_current_user)):
    return change_password(current_user["email"], payload.old_password, payload.new_password)


@router.delete("/me", response_model=MessageResponse)
def delete_my_account(current_user: dict = Depends(get_current_user)):
    return delete_account(current_user["email"])