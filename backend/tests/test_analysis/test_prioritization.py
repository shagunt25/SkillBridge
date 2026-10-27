import jwt
from unittest.mock import patch, MagicMock
from app.database.mongodb import db
from app.utils.security import JWT_SECRET, JWT_ALGORITHM

def get_test_user_email(client):
    token = next((cookie.value for cookie in client.cookies.jar if cookie.name == "skillbridge_auth"), None)
    if not token:
        return None
    payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    return payload.get("sub")

# ---------------------------------------------------------
# 1. HAPPY PATH & DATA FORMATTING
# ---------------------------------------------------------
def test_prioritized_skills_happy_path(client, resume_token):
    """Verifies the endpoint correctly calls Gemini and formats the response."""
    user_email = get_test_user_email(client)
    db.resumes.delete_many({"user_email": user_email})
    db.targets.delete_many({"user_email": user_email})
    
    db.resumes.insert_one({"user_email": user_email, "skills": [{"name": "python"}]})
    db.targets.insert_one({"user_email": user_email, "target_role": "Python Developer", "required_skills": ["python", "fastapi"]})
    
    mock_ai = MagicMock()
    mock_ai.text = '{"target_role": "python developer", "prioritized_skills": [{"skill": "fastapi", "priority": "High"}]}'
    
    with patch("app.services.gemini_service.client.models.generate_content", return_value=mock_ai):
        response = client.get("/analysis/prioritized-skills")
        assert response.status_code == 200
        assert response.json()["prioritized_skills"][0]["skill"] == "fastapi"

def test_prioritized_skills_markdown_stripping(client, resume_token):
    """Verifies the backend correctly strips Markdown code fences from the LLM response."""
    user_email = get_test_user_email(client)
    db.resumes.insert_one({"user_email": user_email, "skills": [{"name": "python"}]})
    db.targets.insert_one({"user_email": user_email, "target_role": "Python Developer", "required_skills": ["python", "fastapi"]})
    
    mock_ai = MagicMock()
    mock_ai.text = '```json\n{"target_role": "python developer", "prioritized_skills": [{"skill": "fastapi", "priority": "High"}]}\n```'
    
    with patch("app.services.gemini_service.client.models.generate_content", return_value=mock_ai):
        response = client.get("/analysis/prioritized-skills")
        assert response.status_code == 200
        assert response.json()["prioritized_skills"][0]["skill"] == "fastapi"

    
# ---------------------------------------------------------
# 2. LLM VULNERABILITIES & API CRASHES
# ---------------------------------------------------------
def test_prioritized_skills_llm_api_crash(client, resume_token):
    """Verifies that an upstream Gemini API crash is handled gracefully (502)."""
    user_email = get_test_user_email(client)
    db.resumes.insert_one({"user_email": user_email, "skills": [{"name": "python"}]})
    db.targets.insert_one({"user_email": user_email, "target_role": "Python Developer", "required_skills": ["python", "fastapi"]})
    
    with patch("app.services.gemini_service.client.models.generate_content", side_effect=Exception("API Timeout")):
        response = client.get("/analysis/prioritized-skills")
        assert response.status_code == 502


def test_prioritized_skills_llm_invalid_json(client, resume_token):
    """Verifies that if Gemini hallucinates bad JSON, the backend catches it (502)."""
    user_email = get_test_user_email(client)
    db.resumes.insert_one({"user_email": user_email, "skills": [{"name": "python"}]})
    db.targets.insert_one({"user_email": user_email, "target_role": "Python Developer", "required_skills": ["python", "fastapi"]})
    
    mock_bad_ai = MagicMock()
    mock_bad_ai.text = "I think you should learn fastapi first."
    
    with patch("app.services.gemini_service.client.models.generate_content", return_value=mock_bad_ai):
        response = client.get("/analysis/prioritized-skills")
        assert response.status_code == 502

# ---------------------------------------------------------
# 3. STATE BOUNDARIES & SECURITY
# ---------------------------------------------------------
def test_prioritized_skills_missing_resume(client, resume_token):
    """Verifies a 404 is returned if the user hasn't uploaded a resume."""
    user_email = get_test_user_email(client)
    db.resumes.delete_many({"user_email": user_email})
    
    response = client.get("/analysis/prioritized-skills")
    assert response.status_code == 404
    assert "resume" in response.json()["detail"].lower()

def test_prioritized_skills_missing_target(client, resume_token):
    """Verifies a 404 is returned if the user hasn't set a target role."""
    user_email = get_test_user_email(client)
    db.resumes.insert_one({"user_email": user_email, "skills": [{"name": "python"}]})
    db.targets.delete_many({"user_email": user_email})
    
    response = client.get("/analysis/prioritized-skills")
    assert response.status_code == 404
    assert "target" in response.json()["detail"].lower()

def test_prioritized_skills_unauthorized(client):
    """Verifies the endpoint is strictly protected by the auth dependency."""
    client.cookies.clear()
    response = client.get("/analysis/prioritized-skills")
    assert response.status_code == 401

def test_prioritized_skills_perfect_match(client, resume_token):
    """Verifies behavior when the user has no missing skills to prioritize."""
    user_email = get_test_user_email(client)
    db.resumes.insert_one({"user_email": user_email, "skills": [{"name": "python"}, {"name": "fastapi"}]})
    db.targets.insert_one({"user_email": user_email, "target_role": "Python Developer", "required_skills": ["python", "fastapi"]})
    
    mock_ai = MagicMock()
    # If there are no missing skills, the AI should logically return an empty array
    mock_ai.text = '{"target_role": "python developer", "prioritized_skills": []}'
    
    with patch("app.services.gemini_service.client.models.generate_content", return_value=mock_ai):
        response = client.get("/analysis/prioritized-skills")
        assert response.status_code == 200
        assert len(response.json()["prioritized_skills"]) == 0

def test_prioritized_skills_schema_hallucination(client, resume_token):
    """Verifies that Pydantic correctly strips or handles extra, unrequested fields from the LLM."""
    user_email = get_test_user_email(client)
    db.resumes.insert_one({"user_email": user_email, "skills": [{"name": "python"}]})
    db.targets.insert_one({"user_email": user_email, "target_role": "Python Developer", "required_skills": ["python", "fastapi"]})
    
    mock_ai = MagicMock()
    # Simulating Gemini returning an extra "study_plan" field not in PrioritizationResponse
    mock_ai.text = '{"target_role": "python developer", "prioritized_skills": [{"skill": "fastapi", "priority": "High"}], "study_plan": "Read docs"}'
    
    with patch("app.services.gemini_service.client.models.generate_content", return_value=mock_ai):
        response = client.get("/analysis/prioritized-skills")
        # Should return 200 (stripping the field) or 502 (rejecting it), but NEVER a 500 server crash
        assert response.status_code in [200, 502]
        if response.status_code == 200:
            assert "study_plan" not in response.json()

def test_prioritized_skills_invalid_priority_enum(client, resume_token):
    """Verifies that if the LLM hallucinates an invalid priority level, the backend catches it (502)."""
    user_email = get_test_user_email(client)
    db.resumes.insert_one({"user_email": user_email, "skills": [{"name": "python"}]})
    db.targets.insert_one({"user_email": user_email, "target_role": "Python Developer", "required_skills": ["python", "fastapi"]})
    
    mock_ai = MagicMock()
    # Simulating Gemini inventing a priority level "Crucial" instead of High/Medium/Low
    mock_ai.text = '{"target_role": "python developer", "prioritized_skills": [{"skill": "fastapi", "priority": "Crucial"}]}'
    
    with patch("app.services.gemini_service.client.models.generate_content", return_value=mock_ai):
        response = client.get("/analysis/prioritized-skills")
        # Pydantic validation should fail on the backend and trigger your LLM error handling
        assert response.status_code == 502

# ---------------------------------------------------------
# 4. INFRASTRUCTURE & PROTOCOL EDGE CASES
# ---------------------------------------------------------

def test_prioritized_skills_wrong_method(client, resume_token):
    """Verifies that sending a POST request to a GET-only route is rejected (405)."""
    response = client.post("/analysis/prioritized-skills")
    assert response.status_code == 405

def test_prioritized_skills_malformed_token(client):
    """Verifies that a fake or corrupted JWT cookie is rejected (401)."""
    client.cookies.set("skillbridge_auth", "eyJhbGciOiJIUzI1NiIsIn.fake.token")
    
    response = client.get("/analysis/prioritized-skills")
    assert response.status_code == 401
    
    # Flush the poisoned cookie jar so the fake token does not leak
    client.cookies.clear()


def test_prioritized_skills_database_outage(client, resume_token):
    """Verifies that a MongoDB connection drop during data retrieval is handled gracefully."""
    user_email = get_test_user_email(client)
    db.resumes.insert_one({"user_email": user_email, "skills": [{"name": "python"}]})
    db.targets.insert_one({"user_email": user_email, "target_role": "Python Developer", "required_skills": ["python", "fastapi"]})
    
    # Force the database driver to simulate a network outage when looking up the resume
    with patch("app.services.analysis_service.db.resumes.find_one", side_effect=Exception("DB Connection Lost")):
        response = client.get("/analysis/prioritized-skills")
        
        # The backend should catch the DB exception and return a clean 500 error
        assert response.status_code == 500

