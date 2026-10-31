from pydantic import BaseModel, Field
from typing import List


class LearningResource(BaseModel):
    title: str
    url: str
    type: str = "documentation"


class RoadmapSubtopic(BaseModel):
    title: str
    description: str = ""
    estimated_hours: int = 1
    resources: List[LearningResource] = Field(default_factory=list)
    status: str = "Not Started"


class RoadmapItem(BaseModel):
    skill: str
    priority: str
    status: str = "Not Started"
    estimated_hours: int = 1
    subtopics: List[RoadmapSubtopic] = Field(default_factory=list)


class RoadmapResponse(BaseModel):
    target_role: str
    roadmap: List[RoadmapItem]