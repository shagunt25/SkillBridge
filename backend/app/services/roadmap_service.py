import json
from fastapi import HTTPException, status
from app.database.mongodb import db
from app.services.gemini_service import client, MODEL_NAME

roadmaps_collection = db["roadmaps"]

ROADMAP_PROMPT = """
You are a career learning advisor. Given a target job role and a prioritized list of skills the person needs to learn, arrange them into a logical learning sequence — skills that are prerequisites for others should come first.

Return ONLY valid JSON, no markdown, no explanation, no code fences, in this exact structure:
{{
  "roadmap": [
    {{"skill": "skill_name", "priority": "High"}},
    {{"skill": "skill_name", "priority": "Medium"}}
  ]
}}

Keep the same skills and priorities given to you — only reorder them into the best learning sequence. Do not add or remove skills.

Target role: {target_role}
Prioritized skills (in priority order, not necessarily learning order): {skills_list}
"""


def generate_roadmap(target_role: str, prioritized_skills: list[dict]) -> dict:
    if not prioritized_skills:
        return {"target_role": target_role, "roadmap": []}

    skills_list = ", ".join(f"{s['skill']} ({s['priority']})" for s in prioritized_skills)

    prompt = ROADMAP_PROMPT.format(target_role=target_role, skills_list=skills_list)

    try:
        response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
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

    roadmap_items = [
        {"skill": item["skill"], "priority": item["priority"], "status": "Not Started"}
        for item in parsed.get("roadmap", [])
    ]

    return {"target_role": target_role, "roadmap": roadmap_items}


def save_roadmap(user_email: str, target_role: str, roadmap: list[dict]) -> None:
    roadmaps_collection.update_one(
        {"user_email": user_email},
        {"$set": {"user_email": user_email, "target_role": target_role, "roadmap": roadmap}},
        upsert=True
    )