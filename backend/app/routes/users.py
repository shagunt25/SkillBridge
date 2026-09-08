from fastapi import APIRouter, Depends
from app.schemas.auth import UserResponse
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: dict = Depends(get_current_user)):
    return current_user