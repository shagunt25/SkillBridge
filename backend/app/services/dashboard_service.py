from app.database.mongodb import db

users_collection = db["users"]
resumes_collection = db["resumes"]
targets_collection = db["targets"]
roadmaps_collection = db["roadmaps"]


def get_dashboard(user_email: str) -> dict:
    user = users_collection.find_one({"email": user_email})

    resume = resumes_collection.find_one({"user_email": user_email})
    current_skills = [skill["name"] for skill in resume["skills"]] if resume else []

    target = targets_collection.find_one({"user_email": user_email})
    target_role = target.get("target_role") if target else None
    required_skills = target.get("required_skills", []) if target else []

    matched_skills = sorted(set(current_skills) & set(required_skills))
    missing_skills = sorted(set(required_skills) - set(current_skills))

    roadmap_doc = roadmaps_collection.find_one({"user_email": user_email})
    roadmap = roadmap_doc.get("roadmap", []) if roadmap_doc else []

    total = len(roadmap)
    completed = sum(1 for item in roadmap if item["status"] == "Completed")
    overall_progress = round((completed / total * 100), 2) if total > 0 else 0.0

    return {
        "name": user["name"],
        "email": user["email"],
        "current_skills": current_skills,
        "target_role": target_role,
        "required_skills": required_skills,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "roadmap": roadmap,
        "overall_progress": overall_progress
    }