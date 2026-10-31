from fastapi import HTTPException, status

from app.services.roadmap_service import roadmaps_collection


VALID_STATUSES = {
    "Not Started",
    "In Progress",
    "Completed",
}


def _normalise(value: str) -> str:
    return value.strip().casefold() if isinstance(value, str) else ""


def _get_roadmap_document(user_email: str) -> dict:
    roadmap_doc = roadmaps_collection.find_one(
        {"user_email": user_email}
    )

    if not roadmap_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No roadmap found. Please generate a roadmap first.",
        )

    return roadmap_doc


def _validate_status(new_status: str) -> None:
    if new_status not in VALID_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid progress status.",
        )


def _save_roadmap(user_email: str, roadmap: list[dict]) -> None:
    roadmaps_collection.update_one(
        {"user_email": user_email},
        {"$set": {"roadmap": roadmap}},
    )


def update_skill_progress(
    user_email: str,
    skill: str,
    new_status: str,
) -> dict:
    _validate_status(new_status)

    roadmap_doc = _get_roadmap_document(user_email)
    roadmap = roadmap_doc.get("roadmap", [])

    selected_skill = next(
        (
            item
            for item in roadmap
            if _normalise(item.get("skill", "")) == _normalise(skill)
        ),
        None,
    )

    if selected_skill is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill '{skill}' not found in your roadmap.",
        )

    selected_skill["status"] = new_status

    # Updating a whole skill also updates its subtopics.
    for subtopic in selected_skill.get("subtopics", []):
        subtopic["status"] = new_status

    _save_roadmap(user_email, roadmap)

    return _build_progress_response(
        roadmap_doc.get("target_role", ""),
        roadmap,
    )


def update_subtopic_progress(
    user_email: str,
    skill: str,
    subtopic: str,
    new_status: str,
) -> dict:
    _validate_status(new_status)

    roadmap_doc = _get_roadmap_document(user_email)
    roadmap = roadmap_doc.get("roadmap", [])

    selected_skill = next(
        (
            item
            for item in roadmap
            if _normalise(item.get("skill", "")) == _normalise(skill)
        ),
        None,
    )

    if selected_skill is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill '{skill}' not found in your roadmap.",
        )

    subtopics = selected_skill.get("subtopics", [])

    selected_subtopic = next(
        (
            item
            for item in subtopics
            if _normalise(item.get("title", "")) == _normalise(subtopic)
        ),
        None,
    )

    if selected_subtopic is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subtopic '{subtopic}' not found for skill '{skill}'.",
        )

    selected_subtopic["status"] = new_status

    if subtopics and all(
        item.get("status", "Not Started") == "Completed"
        for item in subtopics
    ):
        selected_skill["status"] = "Completed"
    elif any(
        item.get("status", "Not Started") != "Not Started"
        for item in subtopics
    ):
        selected_skill["status"] = "In Progress"
    else:
        selected_skill["status"] = "Not Started"

    _save_roadmap(user_email, roadmap)

    return _build_progress_response(
        roadmap_doc.get("target_role", ""),
        roadmap,
    )


def get_progress(user_email: str) -> dict:
    roadmap_doc = _get_roadmap_document(user_email)

    return _build_progress_response(
        roadmap_doc.get("target_role", ""),
        roadmap_doc.get("roadmap", []),
    )


def calculate_overall_progress(roadmap: list[dict]) -> float:
    """
    Use subtopics as the denominator whenever subtopics exist.
    Fall back to skills for older roadmaps without subtopics.
    """
    subtopics = [
        subtopic
        for item in roadmap
        for subtopic in item.get("subtopics", [])
    ]

    if subtopics:
        total = len(subtopics)
        completed = sum(
            1
            for item in subtopics
            if item.get("status", "Not Started") == "Completed"
        )
    else:
        total = len(roadmap)
        completed = sum(
            1
            for item in roadmap
            if item.get("status", "Not Started") == "Completed"
        )

    if total == 0:
        return 0.0

    return round(completed / total * 100, 2)


def _build_progress_response(
    target_role: str,
    roadmap: list[dict],
) -> dict:
    return {
        "target_role": target_role,
        "roadmap": roadmap,
        "overall_progress": calculate_overall_progress(roadmap),
    }