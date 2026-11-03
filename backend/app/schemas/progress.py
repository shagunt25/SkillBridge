from typing import List

from pydantic import BaseModel, Field

from app.schemas.roadmap import RoadmapItem


class UpdateProgressRequest(BaseModel):
    skill: str
    status: str = Field(
        pattern="^(Not Started|In Progress|Completed)$"
    )


class UpdateSubtopicProgressRequest(BaseModel):
    skill: str
    subtopic: str
    status: str = Field(
        pattern="^(Not Started|In Progress|Completed)$"
    )


class ProgressResponse(BaseModel):
    target_role: str
    roadmap: List[RoadmapItem]
    overall_progress: float