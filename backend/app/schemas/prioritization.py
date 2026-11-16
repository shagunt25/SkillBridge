from pydantic import BaseModel, Field
from typing import List


class PrioritizedSkill(BaseModel):
    skill: str
    priority: str
    priority_score: float = Field(ge=0, le=100)
    priority_rank: int = Field(ge=1)


class PrioritizationResponse(BaseModel):
    target_role: str
    prioritized_skills: List[PrioritizedSkill]