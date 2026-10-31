import json
import os
import re
from urllib.parse import urlparse

import httpx
from fastapi import HTTPException, status

from app.database.mongodb import db
from app.services.gemini_service import client, MODEL_NAME


roadmaps_collection = db["roadmaps"]

TAVILY_API_URL = "https://api.tavily.com/search"
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

MAX_SEARCHES_PER_ROADMAP = 16
MAX_RESULTS_PER_SEARCH = 5


ROADMAP_PROMPT = """
You are an expert career learning advisor.

Create a detailed learning roadmap for the target job role using ONLY
the skills supplied below.

Arrange skills in a logical learning order. Prerequisites must come first.
For each skill, create 2 to 5 practical subtopics in a useful learning order.
Include a concise description and a realistic estimated number of study hours
for each subtopic.

Return ONLY valid JSON. Do not use Markdown or code fences.

Use exactly this structure:
{{
  "roadmap": [
    {{
      "skill": "Python",
      "priority": "High",
      "estimated_hours": 12,
      "subtopics": [
        {{
          "title": "Python fundamentals",
          "description": "Learn variables, data types, conditions and loops.",
          "estimated_hours": 3
        }},
        {{
          "title": "Functions and modules",
          "description": "Write reusable functions and organize Python code.",
          "estimated_hours": 4
        }}
      ]
    }}
  ]
}}

Rules:
- Keep every supplied skill and its original priority.
- Do not add unrelated skills or remove supplied skills.
- You may reorder the skills to create a sensible learning sequence.
- Subtopics must be specific, practical and relevant to the skill.
- Use positive integer values for estimated hours.
- Do not generate URLs or learning resource links.
- The backend handles learning resource search.

Target role: {target_role}

Prioritized skills:
{skills_list}
"""


def _normalise_name(value: str) -> str:
    """Normalize names to make matching tolerant of case and whitespace."""
    if not isinstance(value, str):
        return ""

    return re.sub(r"\s+", " ", value.strip()).casefold()


def _positive_hours(value, default: int = 1) -> int:
    """Return a safe positive integer for estimated study hours."""
    try:
        hours = int(value)
        return max(1, min(hours, 500))

    except (TypeError, ValueError, OverflowError):
        return default


def _is_relevant_learning_resource(
    title: str,
    url: str,
    skill: str,
    subtopic: str,
    content: str = "",
) -> bool:
    """
    Reject job listings, directories and unrelated search results.

    Relevance is checked using the skill and subtopic keywords
    against the result title, URL and Tavily content.
    """

    if not isinstance(url, str) or not url.strip():
        return False

    parsed_url = urlparse(url.strip())

    # Only allow HTTPS resources.
    if parsed_url.scheme.casefold() != "https":
        return False

    domain = (parsed_url.hostname or "").casefold()

    if not domain:
        return False

    # Block known job/recruitment and business-directory domains.
    blocked_domains = {
        "indeed.com",
        "leadiq.com",
    }

    if any(
        domain == blocked or domain.endswith("." + blocked)
        for blocked in blocked_domains
    ):
        return False

    title_lower = title.casefold()
    url_lower = url.casefold()
    content_lower = content.casefold()

    # Reject job listings, recruitment pages and directories.
    blocked_url_terms = {
        "/jobs",
        "/job/",
        "/careers",
        "/recruitment",
        "job-listing",
        "company-directory",
        "business-directory",
    }

    if any(term in url_lower for term in blocked_url_terms):
        return False

    blocked_title_terms = {
        "jobs hiring",
        "job openings",
        "companies directory",
        "company directory",
        "top companies",
        "salary guide",
        "job description",
    }

    if any(term in title_lower for term in blocked_title_terms):
        return False

    # Words that do not meaningfully identify a learning topic.
    stop_words = {
        "the",
        "and",
        "for",
        "with",
        "from",
        "into",
        "your",
        "you",
        "are",
        "was",
        "were",
        "this",
        "that",
        "these",
        "those",
        "learn",
        "learning",
        "course",
        "tutorial",
        "guide",
        "beginner",
        "advanced",
        "introduction",
        "basics",
        "basic",
        "official",
        "documentation",
        "docs",
        "how",
        "what",
        "why",
        "using",
        "use",
        "complete",
        "best",
    }

    # Extract meaningful keywords from the skill and subtopic.
    topic_text = f"{skill} {subtopic}".casefold()

    topic_words = {
        word
        for word in re.findall(r"[a-z0-9+#.]+", topic_text)
        if len(word) > 1 and word not in stop_words
    }

    if not topic_words:
        return False

    # Search across all available Tavily result information.
    searchable_text = (
        f"{title_lower} {url_lower} {content_lower}"
    )

    # Token-based matching avoids accidental substring matches.
    searchable_words = set(
        re.findall(r"[a-z0-9+#.]+", searchable_text)
    )

    matched_keywords = topic_words.intersection(searchable_words)

    # Require at least two matching topic keywords when possible.
    # If only one meaningful keyword exists, require that one.
    required_matches = min(2, len(topic_words))

    if len(matched_keywords) < required_matches:
        return False

    return True


def _search_tavily(
    query: str,
    skill: str = "",
    subtopic: str = "",
) -> list[dict]:
    """Search Tavily and return filtered, deduplicated HTTPS resources."""

    api_key = os.getenv("TAVILY_API_KEY") or TAVILY_API_KEY

    if not api_key:
        return []

    try:
        response = httpx.post(
            TAVILY_API_URL,
            json={
                "api_key": api_key,
                "query": query,
                "search_depth": "basic",
                "max_results": MAX_RESULTS_PER_SEARCH,
                "include_answer": False,
            },
            timeout=8.0,
        )

        response.raise_for_status()
        data = response.json()

    except (httpx.HTTPError, ValueError):
        return []

    if not isinstance(data, dict):
        return []

    results = data.get("results", [])

    if not isinstance(results, list):
        return []

    resources = []
    seen_urls = set()

    for item in results:
        if not isinstance(item, dict):
            continue

        title = item.get("title")
        url = item.get("url")
        content = item.get("content", "")

        if not isinstance(title, str) or not isinstance(url, str):
            continue

        if not isinstance(content, str):
            content = ""

        title = title.strip()
        url = url.strip()
        content = content.strip()

        if not title or not url:
            continue

        # Apply the stricter relevance filter.
        if not _is_relevant_learning_resource(
            title=title,
            url=url,
            skill=skill,
            subtopic=subtopic,
            content=content,
        ):
            continue

        # Normalize URL for duplicate detection.
        normalized_url = url.rstrip("/").casefold()

        if normalized_url in seen_urls:
            continue

        seen_urls.add(normalized_url)

        resources.append(
            {
                "title": title,
                "url": url,
                "type": "learning_resource",
            }
        )

    return resources


def _clean_gemini_json(raw_text: str) -> dict:
    """Parse Gemini JSON, including responses wrapped in code fences."""

    raw_text = raw_text.strip()

    if raw_text.startswith("```"):
        raw_text = re.sub(
            r"^```(?:json)?\s*",
            "",
            raw_text,
            count=1,
            flags=re.IGNORECASE,
        )

        raw_text = re.sub(r"\s*```$", "", raw_text)

    try:
        parsed = json.loads(raw_text)

    except (json.JSONDecodeError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Gemini returned an invalid roadmap. Please try again.",
        )

    if (
        not isinstance(parsed, dict)
        or not isinstance(parsed.get("roadmap"), list)
    ):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "Gemini returned an invalid roadmap structure. "
                "Please try again."
            ),
        )

    return parsed


def generate_roadmap(
    target_role: str,
    prioritized_skills: list[dict],
) -> dict:
    """Generate a roadmap and attach relevant learning resources."""

    if not prioritized_skills:
        return {
            "target_role": target_role,
            "roadmap": [],
        }

    if client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gemini API is not configured. Set GEMINI_API_KEY.",
        )

    original_skills = {}

    for skill in prioritized_skills:
        name = str(skill.get("skill", "")).strip()

        if not name:
            continue

        original_skills[_normalise_name(name)] = {
            "skill": name,
            "priority": str(skill.get("priority", "Medium")),
        }

    if not original_skills:
        return {
            "target_role": target_role,
            "roadmap": [],
        }

    skills_list = "\n".join(
        f"- {item['skill']} (Priority: {item['priority']})"
        for item in original_skills.values()
    )

    prompt = ROADMAP_PROMPT.format(
        target_role=target_role,
        skills_list=skills_list,
    )

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
        )

    except Exception as exc:
        print("Roadmap generation failed:", type(exc).__name__)

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to reach Gemini API. Please try again later.",
        ) from exc

    raw_text = getattr(response, "text", None)

    if not raw_text:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Gemini returned an empty roadmap. Please try again.",
        )

    parsed = _clean_gemini_json(raw_text)

    generated_by_name = {}

    for item in parsed["roadmap"]:
        if not isinstance(item, dict):
            continue

        name = str(item.get("skill", "")).strip()
        normalized = _normalise_name(name)

        # Do not accept skills Gemini added independently.
        if normalized not in original_skills:
            continue

        generated_by_name.setdefault(normalized, item)

    # Keep Gemini's learning order while retaining all supplied skills.
    ordered_names = [
        _normalise_name(str(item.get("skill", "")))
        for item in parsed["roadmap"]
        if isinstance(item, dict)
        and _normalise_name(str(item.get("skill", "")))
        in original_skills
    ]

    ordered_names = list(dict.fromkeys(ordered_names))

    for normalized in original_skills:
        if normalized not in ordered_names:
            ordered_names.append(normalized)

    roadmap_items = []
    searches_used = 0

    for normalized in ordered_names:
        original = original_skills[normalized]
        generated = generated_by_name.get(normalized, {})

        raw_subtopics = generated.get("subtopics", [])

        if not isinstance(raw_subtopics, list):
            raw_subtopics = []

        subtopics = []

        for raw_subtopic in raw_subtopics:
            if not isinstance(raw_subtopic, dict):
                continue

            title = str(raw_subtopic.get("title", "")).strip()

            if not title:
                continue

            description = str(
                raw_subtopic.get("description", "")
            ).strip()

            hours = _positive_hours(
                raw_subtopic.get("estimated_hours", 1)
            )

            resources = []

            if searches_used < MAX_SEARCHES_PER_ROADMAP:
                query = (
                    f'"{original["skill"]}" "{title}" '
                    "official documentation tutorial"
                )

                resources = _search_tavily(
                    query=query,
                    skill=original["skill"],
                    subtopic=title,
                )

                searches_used += 1

            subtopics.append(
                {
                    "title": title,
                    "description": description,
                    "estimated_hours": hours,
                    "resources": resources,
                    "status": "Not Started",
                }
            )

        if subtopics:
            skill_hours = sum(
                item["estimated_hours"] for item in subtopics
            )

        else:
            skill_hours = _positive_hours(
                generated.get("estimated_hours", 1)
            )

        roadmap_items.append(
            {
                "skill": original["skill"],
                "priority": original["priority"],
                "status": "Not Started",
                "estimated_hours": skill_hours,
                "subtopics": subtopics,
            }
        )

    return {
        "target_role": target_role,
        "roadmap": roadmap_items,
    }


def _preserve_roadmap_progress(
    new_roadmap: list[dict],
    old_roadmap: list[dict],
) -> list[dict]:
    """Retain statuses for skills and subtopics that still match."""

    old_skills = {
        _normalise_name(item.get("skill", "")): item
        for item in old_roadmap
        if isinstance(item, dict)
    }

    for new_skill in new_roadmap:
        old_skill = old_skills.get(
            _normalise_name(new_skill.get("skill", ""))
        )

        if not old_skill:
            continue

        old_subtopics = {
            _normalise_name(item.get("title", "")): item
            for item in old_skill.get("subtopics", [])
            if isinstance(item, dict)
        }

        for new_subtopic in new_skill.get("subtopics", []):
            old_subtopic = old_subtopics.get(
                _normalise_name(new_subtopic.get("title", ""))
            )

            if old_subtopic:
                new_subtopic["status"] = old_subtopic.get(
                    "status",
                    "Not Started",
                )

        # Derive skill status from its current subtopics where possible.
        new_subtopics = new_skill.get("subtopics", [])

        if new_subtopics:
            statuses = [
                item.get("status", "Not Started")
                for item in new_subtopics
            ]

            if all(value == "Completed" for value in statuses):
                new_skill["status"] = "Completed"

            elif any(value != "Not Started" for value in statuses):
                new_skill["status"] = "In Progress"

            else:
                new_skill["status"] = "Not Started"

        else:
            new_skill["status"] = old_skill.get(
                "status",
                "Not Started",
            )

    return new_roadmap


def save_roadmap(
    user_email: str,
    target_role: str,
    roadmap: list[dict],
) -> None:
    """Save a roadmap while preserving progress for matching topics."""

    existing = roadmaps_collection.find_one(
        {"user_email": user_email}
    )

    if existing:
        old_roadmap = existing.get("roadmap", [])

        if isinstance(old_roadmap, list):
            roadmap = _preserve_roadmap_progress(
                new_roadmap=roadmap,
                old_roadmap=old_roadmap,
            )

    roadmaps_collection.update_one(
        {"user_email": user_email},
        {
            "$set": {
                "user_email": user_email,
                "target_role": target_role,
                "roadmap": roadmap,
            }
        },
        upsert=True,
    )