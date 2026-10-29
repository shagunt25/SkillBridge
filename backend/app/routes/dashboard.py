from fastapi import APIRouter, Depends, HTTPException
from app.schemas.dashboard import DashboardResponse
from app.services.dashboard_service import get_dashboard
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardResponse)
def read_dashboard(current_user: dict = Depends(get_current_user)):
    try:
        return get_dashboard(current_user["email"])
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve the dashboard due to a server error."
        ) from exc