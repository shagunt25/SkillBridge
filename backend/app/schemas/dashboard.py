from pydantic import BaseModel
from typing import List, Optional


class DashboardResponse(BaseModel):
    name: str
    email: str
    current_skills: List[str]
    target_role: Optional[str] = None
    required_skills: List[str] = []
    matched_skills: List[str] = []
    missing_skills: List[str] = []
    roadmap: List[dict] = []
    overall_progress: float = 0.0