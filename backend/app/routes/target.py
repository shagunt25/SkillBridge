from fastapi import APIRouter, Depends
from app.schemas.target import CareerGoalRequest, JobDescriptionRequest, TargetSkillsResponse
from app.services.target_service import get_skills_for_career, get_skills_for_job_description, save_target
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/target", tags=["target"])


@router.post("/career", response_model=TargetSkillsResponse)
def submit_career_goal(payload: CareerGoalRequest, current_user: dict = Depends(get_current_user)):
    result = get_skills_for_career(payload.target_role)
    save_target(current_user["email"], result["target_role"], result["required_skills"])
    return result


@router.post("/job", response_model=TargetSkillsResponse)
def submit_job_description(payload: JobDescriptionRequest, current_user: dict = Depends(get_current_user)):
    result = get_skills_for_job_description(payload.job_description)
    save_target(current_user["email"], result["target_role"], result["required_skills"])
    return result