
import json
import os

from dotenv import load_dotenv
from fastapi import HTTPException, status
from google import genai

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

MODEL_NAME = "gemini-3.6-flash"

PRIORITIZATION_PROMPT = """
You are a career learning advisor. Rank missing skills for the target role.
Consider foundational importance, dependencies, and common job requirements.

Return only valid JSON in this format:
{{
  "prioritized_skills": [
    {{"skill": "Python", "priority": "High"}}
  ]
}}

Priority must be exactly High, Medium, or Low.
Target role: {target_role}
Missing skills: {missing_skills}
"""


def prioritize_missing_skills(target_role: str, missing_skills: list[str]) -> dict:
    if not missing_skills:
        return {
            "target_role": target_role,
            "prioritized_skills": []
        }

    if client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gemini API is not configured. Set GEMINI_API_KEY."
        )

    prompt = PRIORITIZATION_PROMPT.format(
        target_role=target_role,
        missing_skills=", ".join(missing_skills)
    )

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        raw_text = (response.text or "").strip()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to get prioritization from Gemini."
        )

    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`").strip()
        if raw_text.startswith("json"):
            raw_text = raw_text[4:].strip()

    try:
        parsed = json.loads(raw_text)
        skills = parsed["prioritized_skills"]

        if not isinstance(skills, list):
            raise ValueError("Expected a list of skills")

        allowed_priorities = {"High", "Medium", "Low"}
        normalized = []
        seen = set()

        for item in skills:
            skill = item["skill"]
            priority = item["priority"]

            if not isinstance(skill, str):
                raise ValueError("Skill must be a string")

            if priority not in allowed_priorities:
                raise ValueError("Invalid priority")

            if skill in missing_skills and skill not in seen:
                normalized.append({
                    "skill": skill,
                    "priority": priority
                })
                seen.add(skill)

        for skill in missing_skills:
            if skill not in seen:
                normalized.append({
                    "skill": skill,
                    "priority": "Medium"
                })

    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Gemini returned an invalid prioritization response."
        )

    return {
        "target_role": target_role,
        "prioritized_skills": normalized
    }
