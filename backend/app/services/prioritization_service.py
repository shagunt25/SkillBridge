
from app.services.gemini_service import prioritize_missing_skills as rank_skills


def prioritize_missing_skills(target_role: str, missing_skills: list[str]) -> dict:
    return rank_skills(target_role, missing_skills)