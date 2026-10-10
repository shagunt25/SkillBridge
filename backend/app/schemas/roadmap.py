from pydantic import BaseModel
from typing import List


class RoadmapItem(BaseModel):
    skill: str
    priority: str
    status: str = "Not Started"


class RoadmapResponse(BaseModel):
    target_role: str
    roadmap: List[RoadmapItem]