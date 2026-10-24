from pydantic import BaseModel, Field
from typing import List


class CareerGoalRequest(BaseModel):
    target_role: str = Field(..., min_length=1, max_length=100)


class JobDescriptionRequest(BaseModel):
    job_description: str = Field(..., min_length=1, max_length=10000)


class TargetSkillsResponse(BaseModel):
    target_role: str
    required_skills: List[str]