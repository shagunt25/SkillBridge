from typing import Annotated, List

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CareerGoalRequest(BaseModel):
    target_role: str = Field(..., min_length=1, max_length=100)

    @field_validator("target_role")
    @classmethod
    def validate_target_role(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Target role cannot be blank.")
        return normalized


class JobDescriptionRequest(BaseModel):
    job_description: str = Field(..., min_length=1, max_length=10000)

    @field_validator("job_description")
    @classmethod
    def validate_job_description(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Job description cannot be blank.")
        return normalized


class TargetSkillsResponse(BaseModel):
    target_role: str
    required_skills: List[str]


class GeneratedTargetSkills(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_role: str = Field(min_length=1, max_length=100)
    required_skills: list[Annotated[str, Field(min_length=1, max_length=100)]] = Field(
        min_length=1,
        max_length=50,
    )

    @field_validator("target_role")
    @classmethod
    def normalize_target_role(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Target role cannot be blank.")
        return normalized

    @field_validator("required_skills")
    @classmethod
    def normalize_required_skills(cls, skills: list[str]) -> list[str]:
        normalized = []
        seen = set()

        for skill in skills:
            name = skill.strip().lower()
            if not name:
                raise ValueError("Skills cannot be blank.")
            if name not in seen:
                normalized.append(name)
                seen.add(name)

        return normalized