from pydantic import BaseModel
from typing import List


class SkillGapResponse(BaseModel):
    target_role: str
    matched_skills: List[str]
    missing_skills: List[str]
    extra_skills: List[str]