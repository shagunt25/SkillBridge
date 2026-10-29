from fastapi import APIRouter, Depends, HTTPException
from app.schemas.progress import UpdateProgressRequest, ProgressResponse
from app.services.progress_service import update_skill_progress, get_progress
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/progress", tags=["progress"])


@router.patch("/update", response_model=ProgressResponse)
def update_progress(payload: UpdateProgressRequest, current_user: dict = Depends(get_current_user)):
    try:
        return update_skill_progress(
            current_user["email"],
            payload.skill,
            payload.status
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to update progress due to a server error."
        ) from exc


@router.get("", response_model=ProgressResponse)
def read_progress(current_user: dict = Depends(get_current_user)):
    try:
        return get_progress(current_user["email"])
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve progress due to a server error."
        ) from exc