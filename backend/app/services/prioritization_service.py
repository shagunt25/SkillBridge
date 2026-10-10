import json
from fastapi import HTTPException, status
from app.services.gemini_service import client, MODEL_NAME

PRIORITIZATION_PROMPT = """
You are a career learning advisor. Given a target job role and a list of skills the person is missing, rank each skill's priority for learning.

Consider: how foundational the skill is, whether other skills depend on it, and how commonly it's required for the role.

Return ONLY valid JSON, no markdown, no explanation, no code fences, in this exact structure:
{{
  "prioritized_skills": [
    {{"skill": "skill_name", "priority": "High"}},
    {{"skill": "skill_name", "priority": "Medium"}},
    {{"skill": "skill_name", "priority": "Low"}}
  ]
}}

Priority must be exactly one of: "High", "Medium", "Low". Order the list from highest to lowest priority (most important to learn first, listed first).

Target role: {target_role}
Missing skills: {missing_skills}
"""


def prioritize_missing_skills(target_role: str, missing_skills: list[str]) -> dict:
    if not missing_skills:
        return {"target_role": target_role, "prioritized_skills": []}

    prompt = PRIORITIZATION_PROMPT.format(
        target_role=target_role,
        missing_skills=", ".join(missing_skills)
    )

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to reach Gemini API: {str(e)}"
        )

    raw_text = response.text.strip()

    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
        raw_text = raw_text.strip()

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Gemini returned an invalid response. Please try again."
        )

    return {
        "target_role": target_role,
        "prioritized_skills": parsed.get("prioritized_skills", [])
    }