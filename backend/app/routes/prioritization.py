from fastapi import APIRouter, Depends
from app.schemas.prioritization import PrioritizationResponse
from app.services.analysis_service import calculate_skill_gap
from app.services.prioritization_service import prioritize_missing_skills
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get("/prioritized-skills", response_model=PrioritizationResponse)
def get_prioritized_skills(current_user: dict = Depends(get_current_user)):
    gap = calculate_skill_gap(current_user["email"])
    return prioritize_missing_skills(gap["target_role"], gap["missing_skills"])