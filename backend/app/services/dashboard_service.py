
from fastapi import HTTPException

from app.database.mongodb import db
from app.services.progress_service import calculate_overall_progress
from app.utils.normalization import (
    canonicalize_skill_name,
    canonicalize_skill_set,
)


users_collection = db["users"]
resumes_collection = db["resumes"]
targets_collection = db["targets"]
roadmaps_collection = db["roadmaps"]


def get_dashboard(user_email: str) -> dict:
    # Get user
    user = users_collection.find_one({"email": user_email})

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found."
        )

    # Get resume skills
    resume = resumes_collection.find_one({"user_email": user_email})

    current_skills = [
        skill["name"].strip()
        for skill in (resume.get("skills", []) if resume else [])
        if isinstance(skill, dict)
        and isinstance(skill.get("name"), str)
        and skill["name"].strip()
    ]

    # Get target role and required skills
    target = targets_collection.find_one({"user_email": user_email})

    target_role = target.get("target_role") if target else None
    required_skills = target.get("required_skills", []) if target else []

    # Match current skills with required skills
    current_skill_set = canonicalize_skill_set(current_skills)

    matched_skills = []
    missing_skills = []
    seen_required_skills = set()

    for skill in required_skills:
        normalized = canonicalize_skill_name(skill)
        if not normalized or normalized in seen_required_skills:
            continue

        seen_required_skills.add(normalized)
        if normalized in current_skill_set:
            matched_skills.append(normalized)
        else:
            missing_skills.append(normalized)

    # Roadmap and progress
    roadmap_doc = roadmaps_collection.find_one(
        {"user_email": user_email}
    )

    roadmap = roadmap_doc.get("roadmap", []) if roadmap_doc else []

    # Use the same calculation as the /progress endpoint
    overall_progress = calculate_overall_progress(roadmap)

    return {
        "name": user.get("name", ""),
        "email": user_email,
        "current_skills": current_skills,
        "target_role": target_role,
        "required_skills": required_skills,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "roadmap": roadmap,
        "overall_progress": overall_progress
    }
