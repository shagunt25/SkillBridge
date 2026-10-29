from pydantic import BaseModel, Field
from typing import List


class UpdateProgressRequest(BaseModel):
    skill: str
    status: str = Field(pattern="^(Not Started|In Progress|Completed)$")


class RoadmapItemWithProgress(BaseModel):
    skill: str
    priority: str
    status: str


class ProgressResponse(BaseModel):
    target_role: str
    roadmap: List[RoadmapItemWithProgress]
    overall_progress: float