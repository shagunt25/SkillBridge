import logging

from fastapi import APIRouter, Depends, HTTPException
from app.schemas.roadmap import RoadmapResponse
from app.services.analysis_service import calculate_skill_gap
from app.services.prioritization_service import prioritize_missing_skills
from app.services.roadmap_service import generate_roadmap, save_roadmap
from app.services.auth_service import reserve_ai_request
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/roadmap", tags=["roadmap"])
logger = logging.getLogger(__name__)


@router.post("/generate", response_model=RoadmapResponse)
def generate_user_roadmap(current_user: dict = Depends(get_current_user)):
    try:
        gap = calculate_skill_gap(current_user["email"])

        if gap["missing_skills"]:
            reserve_ai_request(current_user["email"])

        prioritized = prioritize_missing_skills(
            gap["target_role"],
            gap["missing_skills"]
        )

        roadmap_result = generate_roadmap(
            prioritized["target_role"],
            prioritized["prioritized_skills"]
        )

        save_roadmap(
            current_user["email"],
            roadmap_result["target_role"],
            roadmap_result["roadmap"]
        )

        return roadmap_result

    except HTTPException:
        raise

    except Exception as exc:
        logger.exception("Failed to generate or save roadmap")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate or save the roadmap due to a server error."
        ) from exc