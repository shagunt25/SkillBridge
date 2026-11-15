import logging
import json
from fastapi import HTTPException, status
from pydantic import ValidationError

from app.schemas.target import GeneratedTargetSkills
from app.services.gemini_service import (
    MODEL_NAME,
    client,
    remove_code_fences,
)

logger = logging.getLogger(__name__)

CAREER_PROMPT = """
You are a career skills advisor. Given a job title/career goal, return the most important, commonly required technical and professional skills for that role today.

Return ONLY valid JSON, no markdown, no explanation, no code fences, in this exact structure:
{
  "target_role": "string",
  "required_skills": ["skill1", "skill2", "skill3"]
}

List between 5 and 12 of the most relevant skills, in lowercase, single words or short phrases (e.g. "python", "rest apis", "sql").

Job title / career goal:
"""

JOB_DESCRIPTION_PROMPT = """
You are analyzing a job description. Extract the required or preferred skills mentioned or implied.

Return ONLY valid JSON, no markdown, no explanation, no code fences, in this exact structure:
{
  "target_role": "string (infer a short job title from the description)",
  "required_skills": ["skill1", "skill2", "skill3"]
}

List the skills in lowercase, single words or short phrases. Do not invent skills not mentioned or clearly implied in the text.

Job description:
"""


def _call_gemini_for_skills(prompt: str, input_text: str) -> dict:
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gemini API is not configured. Set GEMINI_API_KEY.",
        )

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt + input_text
        )
    except Exception as exc:
        logger.exception("Gemini failed to generate target skills")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to reach Gemini API.",
        ) from exc

    raw_text = remove_code_fences(getattr(response, "text", None))
    if not raw_text:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Gemini returned an empty response. Please try again.",
        )

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Gemini returned an invalid response. Please try again.",
        ) from exc

    try:
        validated = GeneratedTargetSkills.model_validate(parsed)
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Gemini response did not match the expected target skills format.",
        ) from exc

    return validated.model_dump()


def get_skills_for_career(target_role: str) -> dict:
    return _call_gemini_for_skills(CAREER_PROMPT, target_role)


def get_skills_for_job_description(job_description: str) -> dict:
    return _call_gemini_for_skills(JOB_DESCRIPTION_PROMPT, job_description)

from app.database.mongodb import db

targets_collection = db["targets"]


def save_target(user_email: str, target_role: str, required_skills: list[str]) -> None:
    targets_collection.update_one(
        {"user_email": user_email},
        {"$set": {
            "user_email": user_email,
            "target_role": target_role,
            "required_skills": required_skills
        }},
        upsert=True
    )