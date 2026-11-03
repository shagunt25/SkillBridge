import json
import os
import re

from urllib.parse import urlparse

import httpx

from fastapi import HTTPException, status

from app.database.mongodb import db
from app.services.gemini_service import client, MODEL_NAME


ROADMAP_PROMPT = """
You are an expert technical mentor and career roadmap designer.

Create a detailed learning roadmap for the following target role.

TARGET ROLE:
{target_role}

PRIORITIZED SKILLS:
{skills_list}

IMPORTANT INSTRUCTIONS:

1. Follow the exact skill order provided in PRIORITIZED SKILLS.
2. Do not rearrange the skills.
3. Do not remove any skill.
4. Do not add any extra skills.
5. Create practical learning subtopics for every skill.
6. Keep the learning sequence beginner-friendly.
7. Include a short description for each subtopic.
8. Give realistic estimated learning hours.
9. Return valid JSON only.
10. Do not include Markdown code fences.
11. Preserve the priority, priority_score, and priority_rank
    provided for each skill.

Return JSON in this exact structure:

{{
    "roadmap": [
        {{
            "skill": "Python",
            "priority": "High",
            "priority_score": 95,
            "priority_rank": 1,
            "estimated_hours": 20,
            "subtopics": [
                {{
                    "title": "Python Basics",
                    "description": "Learn variables, data types and operators.",
                    "estimated_hours": 5
                }}
            ]
        }}
    ]
}}
"""


def _normalise_skill(skill: str) -> str:
    """
    Normalize skill names for matching.
    """
    return re.sub(
        r"\s+",
        " ",
        str(skill).strip()
    ).casefold()


def _is_valid_url(url: str) -> bool:
    """
    Check whether a resource URL is a valid HTTP or HTTPS URL.
    """
    try:
        parsed = urlparse(url)

        return (
            parsed.scheme in {"http", "https"}
            and bool(parsed.netloc)
        )

    except Exception:
        return False


def _search_learning_resources(query: str) -> list[dict]:
    """
    Search for learning resources using Tavily.

    If Tavily is not configured or the search fails,
    return an empty list rather than failing roadmap generation.
    """
    api_key = os.getenv("TAVILY_API_KEY")

    if not api_key:
        return []

    try:
        response = httpx.post(
            "https://api.tavily.com/search",
            json={
                "api_key": api_key,
                "query": query,
                "search_depth": "basic",
                "max_results": 5,
                "include_answer": False
            },
            timeout=15.0
        )

        response.raise_for_status()

        data = response.json()

        results = data.get("results", [])

        resources = []

        for result in results:

            title = result.get("title")
            url = result.get("url")

            if not title or not url:
                continue

            if not _is_valid_url(url):
                continue

            resources.append({
                "title": title.strip(),
                "url": url.strip(),
                "type": "documentation"
            })

        return resources

    except Exception as e:
        print(f"Tavily resource search error: {e}")
        return []


def _preserve_roadmap_progress(
    generated_roadmap: list[dict],
    existing_roadmap: list[dict]
) -> list[dict]:
    """
    Preserve existing skill and subtopic progress when
    a roadmap is regenerated.
    """
    existing_skills = {}

    for item in existing_roadmap:

        if not isinstance(item, dict):
            continue

        skill_name = item.get("skill")

        if not skill_name:
            continue

        existing_skills[
            _normalise_skill(skill_name)
        ] = item

    for new_item in generated_roadmap:

        skill_key = _normalise_skill(
            new_item.get("skill", "")
        )

        old_item = existing_skills.get(skill_key)

        if not old_item:
            continue

        # Preserve overall skill status.
        new_item["status"] = old_item.get(
            "status",
            "Not Started"
        )

        # Match old subtopics by title.
        old_subtopics = {}

        for old_subtopic in old_item.get("subtopics", []):

            if not isinstance(old_subtopic, dict):
                continue

            title = old_subtopic.get("title")

            if title:
                old_subtopics[
                    _normalise_skill(title)
                ] = old_subtopic

        for new_subtopic in new_item.get("subtopics", []):

            title_key = _normalise_skill(
                new_subtopic.get("title", "")
            )

            old_subtopic = old_subtopics.get(title_key)

            if old_subtopic:
                new_subtopic["status"] = old_subtopic.get(
                    "status",
                    "Not Started"
                )

    return generated_roadmap


def generate_roadmap(
    target_role: str,
    prioritized_skills: list[dict]
) -> dict:
    """
    Generate a roadmap using the already-prioritized skills.

    The backend determines the final skill order.
    Gemini only generates learning content for those skills.
    """

    if not prioritized_skills:
        return {
            "target_role": target_role,
            "roadmap": []
        }

    if client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gemini AI service is not configured."
        )

    # Prepare and validate skills.
    original_skills = {}

    for item in prioritized_skills:

        if not isinstance(item, dict):
            continue

        skill_name = item.get("skill")

        if not isinstance(skill_name, str) or not skill_name.strip():
            continue

        skill_name = skill_name.strip()

        skill_key = _normalise_skill(skill_name)

        if skill_key in original_skills:
            continue

        score = item.get("priority_score", 50)
        rank = item.get("priority_rank", len(original_skills) + 1)

        try:
            score = float(score)
            rank = int(rank)
        except (TypeError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid priority data for skill: {skill_name}"
            )

        if not 0 <= score <= 100 or rank < 1:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid priority score or rank for skill: {skill_name}"
            )

        priority = item.get("priority")

        if priority not in {"High", "Medium", "Low"}:
            if score >= 80:
                priority = "High"
            elif score >= 50:
                priority = "Medium"
            else:
                priority = "Low"

        original_skills[skill_key] = {
            "skill": skill_name,
            "priority": priority,
            "priority_score": score,
            "priority_rank": rank
        }

    if not original_skills:
        return {
            "target_role": target_role,
            "roadmap": []
        }

    # Sort by backend-assigned rank.
    sorted_skills = sorted(
        original_skills.values(),
        key=lambda item: item["priority_rank"]
    )

    # Build the prompt input in the exact backend order.
    skills_list = json.dumps(
        sorted_skills,
        ensure_ascii=False,
        indent=2
    )

    prompt = ROADMAP_PROMPT.format(
        target_role=target_role,
        skills_list=skills_list
    )

    # Generate roadmap content using Gemini.
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )

        raw_text = (response.text or "").strip()

        if not raw_text:
            raise ValueError("Gemini returned an empty response.")

    except Exception as e:
        print(f"Gemini roadmap generation error: {e}")

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to generate the learning roadmap."
        )

    # Remove Markdown code fences.
    raw_text = re.sub(
        r"^```(?:json)?\s*|\s*```$",
        "",
        raw_text,
        flags=re.IGNORECASE
    ).strip()

    # Parse Gemini response.
    try:
        parsed = json.loads(raw_text)

        if not isinstance(parsed, dict):
            raise ValueError("Invalid roadmap response.")

        generated_items = parsed.get("roadmap")

        if not isinstance(generated_items, list):
            raise ValueError("Roadmap must be a list.")

    except (json.JSONDecodeError, TypeError, ValueError) as e:
        print(f"Roadmap JSON parsing error: {e}")

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Gemini returned an invalid roadmap response."
        )

    # Index generated content by skill name.
    generated_by_name = {}

    for item in generated_items:

        if not isinstance(item, dict):
            continue

        skill_name = item.get("skill")

        if not isinstance(skill_name, str) or not skill_name.strip():
            continue

        skill_key = _normalise_skill(skill_name)

        # Ignore skills that were not requested.
        if skill_key not in original_skills:
            continue

        if skill_key in generated_by_name:
            continue

        generated_by_name[skill_key] = item

    roadmap_items = []

    # IMPORTANT:
    # Iterate through sorted_skills, not Gemini's returned order.
    # This guarantees that priority ranking is preserved.
    for skill_data in sorted_skills:

        skill_name = skill_data["skill"]
        skill_key = _normalise_skill(skill_name)

        generated_item = generated_by_name.get(
            skill_key,
            {}
        )

        generated_subtopics = generated_item.get(
            "subtopics",
            []
        )

        if not isinstance(generated_subtopics, list):
            generated_subtopics = []

        subtopics = []

        for subtopic in generated_subtopics:

            if not isinstance(subtopic, dict):
                continue

            title = subtopic.get("title")

            if not isinstance(title, str) or not title.strip():
                continue

            description = subtopic.get(
                "description",
                ""
            )

            try:
                estimated_hours = int(
                    subtopic.get("estimated_hours", 1)
                )
            except (TypeError, ValueError):
                estimated_hours = 1

            estimated_hours = max(1, estimated_hours)

            # Search for learning resources.
            resources = _search_learning_resources(
                f"{title} {skill_name} official documentation tutorial"
            )

            subtopics.append({
                "title": title.strip(),
                "description": (
                    description.strip()
                    if isinstance(description, str)
                    else ""
                ),
                "estimated_hours": estimated_hours,
                "resources": resources,
                "status": "Not Started"
            })

        # If Gemini omitted all subtopics for a skill,
        # fail rather than silently creating an incomplete roadmap.
        if not subtopics:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Gemini did not generate subtopics for {skill_name}."
            )

        try:
            estimated_hours = int(
                generated_item.get("estimated_hours", 1)
            )
        except (TypeError, ValueError):
            estimated_hours = 1

        estimated_hours = max(1, estimated_hours)

        roadmap_items.append({
            "skill": skill_name,
            "priority": skill_data["priority"],
            "priority_score": skill_data["priority_score"],
            "priority_rank": skill_data["priority_rank"],
            "status": "Not Started",
            "estimated_hours": estimated_hours,
            "subtopics": subtopics
        })

    return {
        "target_role": target_role,
        "roadmap": roadmap_items
    }


def save_roadmap(
    user_id: str,
    target_role: str,
    roadmap: list[dict]
) -> dict:
    """
    Save the generated roadmap.

    This implementation assumes your MongoDB database has
    a 'roadmaps' collection and stores one roadmap per user.
    """

    existing_document = db.roadmaps.find_one({
        "user_id": user_id
    })

    existing_roadmap = []

    if existing_document:
        existing_roadmap = existing_document.get(
            "roadmap",
            []
        )

    roadmap = _preserve_roadmap_progress(
        roadmap,
        existing_roadmap
    )

    roadmap_document = {
        "user_id": user_id,
        "target_role": target_role,
        "roadmap": roadmap
    }

    db.roadmaps.update_one(
        {"user_id": user_id},
        {"$set": roadmap_document},
        upsert=True
    )

    return roadmap_document