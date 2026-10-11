from datetime import datetime, timezone
from app.database.mongodb import db
from app.schemas.resume import ResumeAnalysis

resumes_collection = db["resumes"]

def save_resume_analysis(user_email: str, analysis: ResumeAnalysis) -> dict:
    resume_document = {
        "user_email": user_email,
        "skills": [skill.model_dump() for skill in analysis.skills],
        "education": [edu.model_dump() for edu in analysis.education],
        "experience": [exp.model_dump() for exp in analysis.experience],
        "projects": [proj.model_dump() for proj in analysis.projects],
        "updated_at": datetime.now(timezone.utc)
    }

    resumes_collection.update_one(
        {"user_email": user_email},
        {"$set": resume_document},
        upsert=True
    )

    return resume_document
