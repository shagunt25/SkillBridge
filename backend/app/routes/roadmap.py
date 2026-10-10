from fastapi import APIRouter, Depends
from app.schemas.roadmap import RoadmapResponse
from app.services.analysis_service import calculate_skill_gap
from app.services.prioritization_service import prioritize_missing_skills
from app.services.roadmap_service import generate_roadmap, save_roadmap
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/roadmap", tags=["roadmap"])


@router.post("/generate", response_model=RoadmapResponse)
def generate_user_roadmap(current_user: dict = Depends(get_current_user)):
    gap = calculate_skill_gap(current_user["email"])
    prioritized = prioritize_missing_skills(gap["target_role"], gap["missing_skills"])
    roadmap_result = generate_roadmap(prioritized["target_role"], prioritized["prioritized_skills"])
    save_roadmap(current_user["email"], roadmap_result["target_role"], roadmap_result["roadmap"])
    return roadmap_result