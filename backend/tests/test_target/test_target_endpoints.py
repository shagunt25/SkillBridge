from unittest.mock import patch, MagicMock
import jwt
from app.database.mongodb import db
from app.utils.security import JWT_SECRET, JWT_ALGORITHM

def test_submit_career_goal(client, resume_token):
    """Verifies that submitting a career goal successfully parses the AI JSON response and saves it."""
    
    # 1. Create a fake AI response matching Gemini's object structure
    mock_ai_response = MagicMock()
    mock_ai_response.text = '{"target_role": "backend developer", "required_skills": ["python", "fastapi", "docker"]}'
    
    # 2. Intercept the AI call in target_service and inject the fake response
    with patch("app.services.target_service.client.models.generate_content", return_value=mock_ai_response):
        
        # 3. Make the request to the endpoint. 
        # (The resume_token fixture already logged us in, so 'client' has the secure cookie!)
        response = client.post(
            "/target/career",
            json={"target_role": "Backend Developer"}
        )
        
        # 4. Assert the API contract and parsing logic hold up
        assert response.status_code == 200
        data = response.json()
        assert data["target_role"] == "backend developer"
        assert "fastapi" in data["required_skills"]

def test_submit_job_description(client, resume_token):
    """Verifies that submitting a full job description extracts the correct skills."""
    mock_ai_response = MagicMock()
    mock_ai_response.text = '{"target_role": "frontend developer", "required_skills": ["react", "typescript", "css"]}'
    
    with patch("app.services.target_service.client.models.generate_content", return_value=mock_ai_response):
        response = client.post(
            "/target/job",
            json={"job_description": "We are looking for a React developer proficient in TypeScript and CSS."}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["target_role"] == "frontend developer"
        assert "react" in data["required_skills"]
        assert "typescript" in data["required_skills"]


def test_target_endpoints_unauthorized(client):
    """Verifies that unauthenticated users are blocked from setting targets."""
    # Wipe the secure cookie to simulate a logged-out user
    client.cookies.clear()
    
    response_career = client.post("/target/career", json={"target_role": "Backend Developer"})
    response_job = client.post("/target/job", json={"job_description": "Some job description"})
    
    # Both endpoints should strictly block access
    assert response_career.status_code == 401
    assert response_job.status_code == 401


def test_target_endpoints_validation_error(client, resume_token):
    """Verifies that Pydantic catches missing or malformed request payloads."""
    # Sending an empty JSON object instead of the required fields
    response_career = client.post("/target/career", json={})
    
    # Expected 422 Unprocessable Entity because 'target_role' is missing
    assert response_career.status_code == 422

def test_target_llm_api_crash(client, resume_token):
    """Verifies that an upstream Gemini API crash is handled gracefully (502)."""
    # Force the mock to raise a simulated network error
    with patch("app.services.target_service.client.models.generate_content", side_effect=Exception("API Timeout")):
        response = client.post(
            "/target/career",
            json={"target_role": "Backend Developer"}
        )
        
        assert response.status_code == 502
        assert "Failed to reach Gemini API" in response.json()["detail"]


def test_target_llm_invalid_json(client, resume_token):
    """Verifies that if Gemini hallucinates bad JSON, the backend catches it (502)."""
    mock_bad_ai = MagicMock()
    # Provide plain text instead of the expected JSON dictionary
    mock_bad_ai.text = "I think a backend developer needs python and sql."
    
    with patch("app.services.target_service.client.models.generate_content", return_value=mock_bad_ai):
        response = client.post(
            "/target/career", 
            json={"target_role": "Backend Developer"}
        )
        
        assert response.status_code == 502
        assert "invalid response" in response.json()["detail"]

def test_target_markdown_stripping(client, resume_token):
    """Verifies the backend correctly strips Markdown code fences from the LLM response."""
    mock_ai = MagicMock()
    # Simulating Gemini returning a Markdown-formatted JSON block
    mock_ai.text = '```json\n{"target_role": "devops", "required_skills": ["aws", "docker"]}\n```'
    
    with patch("app.services.target_service.client.models.generate_content", return_value=mock_ai):
        response = client.post("/target/career", json={"target_role": "DevOps"})
        
        assert response.status_code == 200
        assert "aws" in response.json()["required_skills"]


def test_target_database_persistence(client, resume_token):
    """Verifies the inferred skills are successfully saved to the MongoDB targets collection."""
    mock_ai = MagicMock()
    mock_ai.text = '{"target_role": "data scientist", "required_skills": ["python", "pandas"]}'
    
    with patch("app.services.target_service.client.models.generate_content", return_value=mock_ai):
        response = client.post("/target/career", json={"target_role": "Data Scientist"})
        assert response.status_code == 200
        
        # Safely extract the token directly from the client's cookies
        token = None
        for cookie in client.cookies.jar:
            if cookie.name == "skillbridge_auth":
                token = cookie.value
                break
                
        assert token is not None, "Authentication cookie was not found in the client jar"
        
        # Decode the token to get the exact test user's email
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_email = payload.get("sub")
        
        # Query MongoDB to ensure it was saved correctly
        saved_target = db.targets.find_one({"user_email": user_email})
        
        assert saved_target is not None, "Target was not saved to MongoDB!"
        assert saved_target["target_role"] == "data scientist"
        assert "pandas" in saved_target["required_skills"]

def test_target_upsert_logic(client, resume_token):
    """Verifies that a user can only have one active target, and new submissions overwrite the old."""
    mock_ai_1 = MagicMock()
    mock_ai_1.text = '{"target_role": "frontend", "required_skills": ["react"]}'
    
    mock_ai_2 = MagicMock()
    mock_ai_2.text = '{"target_role": "backend", "required_skills": ["python"]}'
    
    # Submit first target
    with patch("app.services.target_service.client.models.generate_content", return_value=mock_ai_1):
        client.post("/target/career", json={"target_role": "Frontend Developer"})
        
    # Submit second target
    with patch("app.services.target_service.client.models.generate_content", return_value=mock_ai_2):
        client.post("/target/career", json={"target_role": "Backend Developer"})
        
    # Extract token to query database
    token = next((cookie.value for cookie in client.cookies.jar if cookie.name == "skillbridge_auth"), None)
    payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    user_email = payload.get("sub")
    
    # Verify exactly one document exists and it contains the updated backend skills
    saved_targets = list(db.targets.find({"user_email": user_email}))
    assert len(saved_targets) == 1, "VULNERABILITY: Multiple targets found for one user instead of an upsert!"
    assert saved_targets[0]["target_role"] == "backend"


def test_target_job_description_too_large(client, resume_token):
    """Verifies that massive text payloads are rejected to prevent LLM token exhaustion."""
    massive_text = "developer " * 50000  # 50,000 words
    
    response = client.post(
        "/target/job",
        json={"job_description": massive_text}
    )
    
    # The API should catch this via Pydantic length limits before hitting the AI
    assert response.status_code == 422


def test_target_database_outage(client, resume_token):
    """Verifies that a MongoDB connection drop is handled gracefully."""
    mock_ai = MagicMock()
    mock_ai.text = '{"target_role": "backend", "required_skills": ["python"]}'
    
    with patch("app.services.target_service.client.models.generate_content", return_value=mock_ai):
        # Force the database to simulate a network outage exactly when saving
        with patch("app.services.target_service.targets_collection.update_one", side_effect=Exception("DB Connection Lost")):
            response = client.post("/target/career", json={"target_role": "Backend"})
            
            # The backend should catch the error and return a 500, not crash the server
            assert response.status_code == 500

