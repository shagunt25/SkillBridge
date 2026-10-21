def normalize_skill_name(name: str) -> str:
    return name.strip().lower()


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