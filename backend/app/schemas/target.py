from pydantic import BaseModel
from typing import List


class CareerGoalRequest(BaseModel):
    target_role: str


class JobDescriptionRequest(BaseModel):
    job_description: str


class TargetSkillsResponse(BaseModel):
    target_role: str
    required_skills: List[str]