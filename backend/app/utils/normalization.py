def normalize_skill_name(name: str) -> str:
    return name.strip().lower()


def normalize_skills(skills: list[dict]) -> list[dict]:
    seen = set()
    normalized = []

    for skill in skills:
        clean_name = normalize_skill_name(skill["name"])

        if clean_name in seen:
            continue

        seen.add(clean_name)
        normalized.append({
            "name": clean_name,
            "level": skill["level"]
        })

    return normalized