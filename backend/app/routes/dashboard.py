from fastapi import APIRouter, Depends
from app.schemas.dashboard import DashboardResponse
from app.services.dashboard_service import get_dashboard
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardResponse)
def read_dashboard(current_user: dict = Depends(get_current_user)):
    return get_dashboard(current_user["email"])