from typing import List

from pydantic import BaseModel, Field

from app.schemas.roadmap import RoadmapItem


class UpdateProgressRequest(BaseModel):
    skill: str = Field(strict=True, min_length=1)
    status: str = Field(
        strict=True,
        pattern="^(Not Started|In Progress|Completed)$"
    )


class UpdateSubtopicProgressRequest(BaseModel):
    skill: str = Field(strict=True, min_length=1)
    subtopic: str = Field(strict=True, min_length=1)
    status: str = Field(
        strict=True,
        pattern="^(Not Started|In Progress|Completed)$"
    )


class ProgressResponse(BaseModel):
    target_role: str
    roadmap: List[RoadmapItem]
    overall_progress: float