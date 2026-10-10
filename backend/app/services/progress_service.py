from fastapi import HTTPException, status
from app.services.roadmap_service import roadmaps_collection


def update_skill_progress(user_email: str, skill: str, new_status: str) -> dict:
    roadmap_doc = roadmaps_collection.find_one({"user_email": user_email})

    if not roadmap_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No roadmap found. Please generate a roadmap first."
        )

    roadmap = roadmap_doc.get("roadmap", [])
    skill_found = False

    for item in roadmap:
        if item["skill"] == skill.strip().lower():
            item["status"] = new_status
            skill_found = True
            break

    if not skill_found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill '{skill}' not found in your roadmap."
        )

    roadmaps_collection.update_one(
        {"user_email": user_email},
        {"$set": {"roadmap": roadmap}}
    )

    return _build_progress_response(roadmap_doc["target_role"], roadmap)


def get_progress(user_email: str) -> dict:
    roadmap_doc = roadmaps_collection.find_one({"user_email": user_email})

    if not roadmap_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No roadmap found. Please generate a roadmap first."
        )

    return _build_progress_response(roadmap_doc["target_role"], roadmap_doc.get("roadmap", []))


def _build_progress_response(target_role: str, roadmap: list[dict]) -> dict:
    total = len(roadmap)
    completed = sum(1 for item in roadmap if item["status"] == "Completed")
    overall_progress = round((completed / total * 100), 2) if total > 0 else 0.0

    return {
        "target_role": target_role,
        "roadmap": roadmap,
        "overall_progress": overall_progress
    }