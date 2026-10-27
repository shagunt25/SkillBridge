import pytest
import json
from app.database.mongodb import db
from unittest.mock import patch, MagicMock

GEMINI_MOCK_PATH = "app.services.gemini_service.generate_resume_content"
VALID_MOCK_AI_JSON = json.dumps({
    "skills": [{"name": "Python", "level": "Advanced"}, {"name": "Docker", "level": "Intermediate"}],
    "education": [{"degree": "B.Tech CSE", "institution": "PSIT", "year": "2028"}],
    "experience": [],
    "projects": [{"title": "SkillBridge", "description": "AI Resume Analyzer"}]
})

class MockResponse:
    def __init__(self, text: str = VALID_MOCK_AI_JSON):
        self.text = text

@patch(GEMINI_MOCK_PATH)
def test_full_user_registration_and_upload_journey(mock_generate, client, make_pdf):
    """
    E2E TEST: Simulates a complete user journey mapped strictly to the Swagger OAS 3.1 definitions.
    """
    test_email = "e2e_real_user@example.com"
    test_password = "SecurePassword123!"
    
    # 0. Setup: Clean state
    db.users.delete_one({"email": test_email})
    db.resumes.delete_many({"user_email": test_email})
    
    # ---------------------------------------------------------
    # PHASE A: User Registration (SignupRequest)
    # ---------------------------------------------------------
    signup_response = client.post(
        "/api/auth/signup", 
        json={
            "name": "E2E Test User", 
            "email": test_email, 
            "password": test_password
        }
    )
    assert signup_response.status_code in [200, 201], f"Signup Failed: {signup_response.text}"
    
    # Bypass the OTP email verification step by manually activating the user in the database
    db.users.update_one({"email": test_email}, {"$set": {"email_verified": True}})
    
    # ---------------------------------------------------------
    # PHASE B: User Login (LoginRequest)
    # ---------------------------------------------------------
    login_response = client.post(
        "/api/auth/login", 
        json={"email": test_email, "password": test_password}
    )
    assert login_response.status_code == 200, f"Login Failed: {login_response.text}"
    # The client now holds your secure HTTPOnly auth cookie internally!
    
    # ---------------------------------------------------------
    # PHASE C: Resume Upload (Body_upload_resume_api_resume_upload_post)
    # ---------------------------------------------------------
    mock_generate.return_value = MockResponse()
    valid_pdf = make_pdf("E2E Test User - Python, Docker")
    files = {"file": ("e2e_resume.pdf", valid_pdf, "application/pdf")}
    
    # The client automatically attaches the secure cookie from Phase B
    upload_response = client.post("/api/resume/upload", files=files)
    assert upload_response.status_code == 200, f"Upload Failed: {upload_response.text}"
    
    # ---------------------------------------------------------
    # PHASE D: Database & Relational Verification
    # ---------------------------------------------------------
    saved_resume = db.resumes.find_one({"user_email": test_email})
    
    assert saved_resume is not None, "Data was not linked to the new user in MongoDB!"
    assert "skills" in saved_resume
    
    skill_names = [s["name"].lower() for s in saved_resume["skills"]]
    assert "python" in skill_names

    # ---------------------------------------------------------
    # PHASE E: Target Skills (AI Inference)
    # ---------------------------------------------------------
    mock_target_ai = MagicMock()
    mock_target_ai.text = '{"target_role": "Backend Engineer", "required_skills": ["python", "docker", "kubernetes", "aws"]}'
    
    # Intercept the specific AI call made by the target_service
    with patch("app.services.target_service.client.models.generate_content", return_value=mock_target_ai):
        target_response = client.post("/target/career", json={"target_role": "Backend Engineer"})
        
    assert target_response.status_code == 200, f"Target Failed: {target_response.text}"
    
    saved_target = db.targets.find_one({"user_email": test_email})
    assert saved_target is not None, "Target was not linked to the user in MongoDB!"
    assert "kubernetes" in saved_target["required_skills"]

    # ---------------------------------------------------------
    # PHASE F: Skill-Gap Engine (Deterministic Analysis)
    # ---------------------------------------------------------
    # No AI mock needed here; this relies purely on the database state
    gap_response = client.get("/analysis/skill-gap")
    
    assert gap_response.status_code == 200, f"Gap Engine Failed: {gap_response.text}"
    gap_data = gap_response.json()
    assert gap_data["target_role"] == "Backend Engineer"
    assert gap_data["matched_skills"] == ["docker", "python"]
    assert gap_data["missing_skills"] == ["aws", "kubernetes"]

    # ---------------------------------------------------------
    # PHASE G: AI Skill Prioritization (The Final Step)
    # ---------------------------------------------------------
    mock_prioritization_ai = MagicMock()
    mock_prioritization_ai.text = '{"target_role": "backend engineer", "prioritized_skills": [{"skill": "kubernetes", "priority": "High"}, {"skill": "aws", "priority": "Medium"}]}'
    
    # Intercept the specific AI call made by the gemini_service for prioritization
    with patch("app.services.gemini_service.client.models.generate_content", return_value=mock_prioritization_ai):
        prioritization_response = client.get("/analysis/prioritized-skills")
        
    assert prioritization_response.status_code == 200, f"Prioritization E2E Failed: {prioritization_response.text}"
    
    prioritization_data = prioritization_response.json()
    assert prioritization_data["prioritized_skills"][0]["skill"] == "kubernetes"
    assert prioritization_data["prioritized_skills"][0]["priority"] == "High"