import os
import json
import re
import math

from google import genai
from dotenv import load_dotenv
from fastapi import HTTPException, status
from pydantic import ValidationError
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential_jitter,
)

from app.schemas.resume import ResumeAnalysis


load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# Preserve the model configured in your original file.
MODEL_NAME = "gemini-3.6-flash"


EXTRACTION_PROMPT = """
You are analyzing a resume. Extract the candidate's information and return
ONLY valid JSON, no markdown, no explanation, no code fences.

Return this exact structure:
{
  "skills": [{"name": "string", "level": "Beginner|Intermediate|Advanced"}],
  "education": [{"degree": "string", "institution": "string", "year": "string"}],
  "experience": [{"role": "string", "company": "string", "duration": "string"}],
  "projects": [{"title": "string", "description": "string"}]
}

If a section has no information, return an empty list for it.
Do not invent information that isn't in the resume text.

Resume text:
"""


PRIORITIZATION_PROMPT = """
You are an expert technical career advisor.

Your task is to evaluate missing skills for a specific target job role.

Target role:
{target_role}

Missing skills:
{missing_skills}

For EACH supplied skill, assign a relevance score from 0 to 100.
The score must reflect how important that skill is for entering and performing
the selected target role.

Consider:
- Whether the skill is essential for the role.
- How commonly it appears in job descriptions for this role.
- Whether it is a foundational skill or depends on other skills.
- Its practical importance in real-world work for this role.

Rules:
1. Include every supplied skill exactly once.
2. Do not add skills that were not supplied.
3. Do not omit any supplied skill.
4. Do not give all skills identical scores unless genuinely justified.
5. Scores must be numeric values between 0 and 100.
6. Return valid JSON only. Do not include markdown or explanations.

Required JSON structure:
{{
  "prioritized_skills": [
    {{"skill": "Python", "score": 95}},
    {{"skill": "SQL", "score": 82}}
  ]
}}
"""


def is_retryable_gemini_error(exc: Exception) -> bool:
    """Retry only errors that are likely to be temporary."""
    code = getattr(exc, "code", None)

    if code is None:
        code = getattr(exc, "status_code", None)

    try:
        code = int(code)
    except (TypeError, ValueError):
        code = None

    if code in {429, 500, 502, 503, 504}:
        return True

    error_name = type(exc).__name__.lower()

    retryable_names = (
        "toomanyrequests",
        "resourceexhausted",
        "serviceunavailable",
        "internalservererror",
        "deadlineexceeded",
    )

    return any(name in error_name for name in retryable_names)


@retry(
    retry=retry_if_exception(is_retryable_gemini_error),
    stop=stop_after_attempt(3),
    wait=wait_exponential_jitter(initial=1, max=8),
    reraise=True,
)
def generate_resume_content(resume_text: str):
    """Make at most three attempts for retryable Gemini errors."""
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gemini API is not configured. Set GEMINI_API_KEY.",
        )

    return client.models.generate_content(
        model=MODEL_NAME,
        contents=EXTRACTION_PROMPT + resume_text,
    )


def _remove_code_fences(raw_text: str) -> str:
    """Remove optional Markdown JSON fences from Gemini output."""
    raw_text = (raw_text or "").strip()

    raw_text = re.sub(
        r"^\s*```(?:json)?\s*",
        "",
        raw_text,
        flags=re.IGNORECASE,
    )
    raw_text = re.sub(r"\s*```\s*$", "", raw_text)

    return raw_text.strip()


def analyze_resume_text(resume_text: str) -> dict:
    try:
        response = generate_resume_content(resume_text)

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Gemini API request failed after retries.",
        ) from exc

    raw_text = _remove_code_fences(response.text)

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

    if not isinstance(parsed, dict):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Gemini returned an unexpected response format.",
        )

    return parsed


def validate_gemini_response(raw_data: dict) -> ResumeAnalysis:
    try:
        return ResumeAnalysis(**raw_data)

    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Gemini's response didn't match the expected format.",
        ) from exc


def prioritize_missing_skills(
    target_role: str,
    missing_skills: list[str],
) -> dict:
    """
    Score missing skills for the selected target role.

    Gemini supplies scores. The backend validates the response,
    sorts skills by score, and assigns unique numerical ranks.
    """

    if not isinstance(target_role, str) or not target_role.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Target role is required.",
        )

    if not missing_skills:
        return {
            "target_role": target_role,
            "prioritized_skills": [],
        }

    if not isinstance(missing_skills, list):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing skills must be provided as a list.",
        )

    # Remove blank entries and duplicate skills while preserving order.
    cleaned_skills = []
    seen = set()

    for skill in missing_skills:
        if not isinstance(skill, str) or not skill.strip():
            continue

        normalized = skill.strip().casefold()

        if normalized not in seen:
            cleaned_skills.append(skill.strip())
            seen.add(normalized)

    if not cleaned_skills:
        return {
            "target_role": target_role,
            "prioritized_skills": [],
        }

    if client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gemini API is not configured. Set GEMINI_API_KEY.",
        )

    prompt = PRIORITIZATION_PROMPT.format(
        target_role=target_role.strip(),
        missing_skills=json.dumps(cleaned_skills),
    )

    # Call Gemini. Do not silently replace AI failure with hardcoded priorities.
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
        )

        raw_text = _remove_code_fences(response.text)

        if not raw_text:
            raise ValueError("Gemini returned an empty prioritization response.")

        parsed = json.loads(raw_text)

    except Exception as exc:
        print(
            "Gemini prioritization failed:",
            type(exc).__name__,
            str(exc),
        )

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to get valid skill prioritization from Gemini.",
        ) from exc

    # Validate the response structure.
    if not isinstance(parsed, dict):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Gemini returned an invalid prioritization response.",
        )

    returned_skills = parsed.get("prioritized_skills")

    if not isinstance(returned_skills, list):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Gemini response is missing prioritized_skills.",
        )

    # Map the original skill names to their exact spelling.
    original_names = {
        skill.casefold(): skill
        for skill in cleaned_skills
    }

    score_map = {}

    for item in returned_skills:
        if not isinstance(item, dict):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Gemini returned an invalid skill entry.",
            )

        skill_name = item.get("skill")
        score = item.get("score")

        if not isinstance(skill_name, str):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Gemini returned a skill with an invalid name.",
            )

        normalized_name = skill_name.strip().casefold()

        if normalized_name not in original_names:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Gemini returned an unexpected skill: {skill_name}.",
            )

        if normalized_name in score_map:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Gemini returned duplicate skill: {skill_name}.",
            )

        # bool is a subclass of int in Python, so reject it explicitly.
        if isinstance(score, bool) or not isinstance(score, (int, float)):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Gemini returned an invalid score for {skill_name}.",
            )

        if not math.isfinite(float(score)) or not 0 <= float(score) <= 100:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Gemini returned an out-of-range score for {skill_name}.",
            )

        score_map[normalized_name] = float(score)

    # Do not silently fill missing skills with guessed scores.
    missing_from_response = [
        skill
        for skill in cleaned_skills
        if skill.casefold() not in score_map
    ]

    if missing_from_response:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "Gemini did not prioritize every supplied skill: "
                + ", ".join(missing_from_response)
            ),
        )

    # Sort by numerical relevance, highest score first.
    ranked_skills = sorted(
        cleaned_skills,
        key=lambda skill: score_map[skill.casefold()],
        reverse=True,
    )

    prioritized_skills = []

    for rank, skill in enumerate(ranked_skills, start=1):
        score = score_map[skill.casefold()]

        if score >= 80:
            priority = "High"
        elif score >= 50:
            priority = "Medium"
        else:
            priority = "Low"

        prioritized_skills.append(
            {
                "skill": skill,
                "priority": priority,
                "priority_score": round(score, 2),
                "priority_rank": rank,
            }
        )

    return {
        "target_role": target_role,
        "prioritized_skills": prioritized_skills,
    }