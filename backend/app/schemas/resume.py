from pydantic import BaseModel
from typing import List


class Skill(BaseModel):
    name: str
    level: str


class Education(BaseModel):
    degree: str
    institution: str
    year: str


class Experience(BaseModel):
    role: str
    company: str
    duration: str


class Project(BaseModel):
    title: str
    description: str


class ResumeAnalysis(BaseModel):
    skills: List[Skill]
    education: List[Education]
    experience: List[Experience]
    projects: List[Project]


class ResumeUploadResponse(BaseModel):
    message: str
    filename: str
    size_kb: float
    analysis: ResumeAnalysis
