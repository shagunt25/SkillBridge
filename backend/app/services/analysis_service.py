from fastapi import HTTPException, status
from app.database.mongodb import db
from app.utils.normalization import canonicalize_skill_set

resumes_collection = db["resumes"]
targets_collection = db["targets"]


def calculate_skill_gap(user_email: str) -> dict:
    resume = resumes_collection.find_one({"user_email": user_email})
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No resume found. Please upload your resume first."
        )

    target = targets_collection.find_one({"user_email": user_email})
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No target role found. Please set a target career or job description first."
        )

    current_skills = canonicalize_skill_set([
        skill.get("name")
        for skill in resume.get("skills", [])
        if isinstance(skill, dict)
    ])

    required_skills = canonicalize_skill_set(
        target.get("required_skills", [])
    )

    matched = sorted(current_skills & required_skills)
    missing = sorted(required_skills - current_skills)
    extra = sorted(current_skills - required_skills)

    return {
        "target_role": target.get("target_role", ""),
        "matched_skills": matched,
        "missing_skills": missing,
        "extra_skills": extra
    }
