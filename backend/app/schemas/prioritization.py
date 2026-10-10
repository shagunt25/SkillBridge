from pydantic import BaseModel
from typing import List


class PrioritizedSkill(BaseModel):
    skill: str
    priority: str


class PrioritizationResponse(BaseModel):
    target_role: str
    prioritized_skills: List[PrioritizedSkill]