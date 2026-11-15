import re
import unicodedata


_SKILL_ALIASES = {
    "js": "javascript",
    "java script": "javascript",
    "ts": "typescript",
    "node js": "node.js",
    "nodejs": "node.js",
    "react js": "react",
    "reactjs": "react",
    "rest api": "rest apis",
    "c sharp": "c#",
    "c plus plus": "c++",
    "postgres": "postgresql",
    "postgres sql": "postgresql",
    "dot net": "dotnet",
    "asp dotnet": "asp.net",
}


def normalize_skill_name(name: str) -> str:
    return name.strip().lower()


def canonicalize_skill_name(name: object) -> str:
    if not isinstance(name, str):
        return ""

    normalized = unicodedata.normalize("NFKC", name).casefold()
    normalized = normalized.replace(".net", " dotnet ")
    normalized = re.sub(r"[_./-]+", " ", normalized)
    normalized = re.sub(r"[^\w+#]+", " ", normalized)
    normalized = " ".join(normalized.split())

    return _SKILL_ALIASES.get(normalized, normalized)


def canonicalize_skill_set(skills: object) -> set[str]:
    if not isinstance(skills, list):
        raise TypeError("Skills must be provided as a list.")

    return {
        normalized
        for skill in skills
        if (normalized := canonicalize_skill_name(skill))
    }


def normalize_skills(skills: list[dict]) -> list[dict]:
    
    if not isinstance(skills, list):
        return skills
    
    seen = set()
    normalized = []

    for skill in skills:

        if not isinstance(skill, dict) or "name" not in skill:
            normalized.append(skill)
            continue

        clean_name = normalize_skill_name(str(skill["name"]))

        if clean_name in seen:
            continue

        seen.add(clean_name)
        normalized.append({
            "name": clean_name,
            "level": skill.get("level")
        })

    return normalized