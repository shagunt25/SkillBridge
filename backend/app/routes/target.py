import logging

from fastapi import APIRouter, Depends, HTTPException

from app.schemas.target import (
    CareerGoalRequest,
    JobDescriptionRequest,
    TargetSkillsResponse,
)
from app.services.target_service import (
    get_skills_for_career,
    get_skills_for_job_description,
    save_target,
)
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/target", tags=["target"])

logger = logging.getLogger(__name__)


@router.post("/career", response_model=TargetSkillsResponse)
def submit_career_goal(
    payload: CareerGoalRequest,
    current_user: dict = Depends(get_current_user),
):
    result = get_skills_for_career(payload.target_role)

    try:
        save_target(
            current_user["email"],
            result["target_role"],
            result["required_skills"],
        )
    except Exception:
        logger.exception("Failed to save career target")
        raise HTTPException(
            status_code=500,
            detail="Failed to save career target",
        )

    return result


@router.post("/job", response_model=TargetSkillsResponse)
def submit_job_description(
    payload: JobDescriptionRequest,
    current_user: dict = Depends(get_current_user),
):
    result = get_skills_for_job_description(payload.job_description)

    try:
        save_target(
            current_user["email"],
            result["target_role"],
            result["required_skills"],
        )
    except Exception:
        logger.exception("Failed to save job description target")
        raise HTTPException(
            status_code=500,
            detail="Failed to save job description target",
        )

    return result