from fastapi import APIRouter, Depends
from app.schemas.analysis import SkillGapResponse
from app.services.analysis_service import calculate_skill_gap
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get("/skill-gap", response_model=SkillGapResponse)
def get_skill_gap(current_user: dict = Depends(get_current_user)):
    return calculate_skill_gap(current_user["email"])