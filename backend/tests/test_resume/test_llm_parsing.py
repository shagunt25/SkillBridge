import json
import pytest
import httpx
from unittest.mock import patch

GEMINI_MOCK_PATH = "app.services.gemini_service.generate_resume_content"
CLIENT_MOCK_PATH = "app.services.gemini_service.client.models.generate_content"

class MockResponse:
    def __init__(self, text: str):
        self.text = text

@patch(GEMINI_MOCK_PATH)
def test_llm_malformed_json_response(mock_generate, client, resume_token, make_pdf):
    headers = {"Authorization": f"Bearer {resume_token}"}
    mock_generate.return_value = MockResponse('{"skills": [{"name": "Python", "level": "Advanced"')
    
    valid_pdf = make_pdf("Shagun Tiwari - Software Engineer - Python, FastAPI")
    files = {"file": ("test_resume.pdf", valid_pdf, "application/pdf")}
    
    response = client.post("/api/resume/upload", headers=headers, files=files)
    
    assert response.status_code == 502
    assert "invalid response" in response.json()["detail"].lower()

@patch(GEMINI_MOCK_PATH)
def test_llm_markdown_code_fence_stripping(mock_generate, client, resume_token, make_pdf):
    """Verifies that gemini_service properly strips ```json ... ``` wrappers."""
    headers = {"Authorization": f"Bearer {resume_token}"}
    fenced_json = """```json
    {
        "skills": [{"name": "FastAPI", "level": "Advanced"}],
        "education": [],
        "experience": [],
        "projects": []
    }
    ```"""
    mock_generate.return_value = MockResponse(fenced_json)
    
    valid_pdf = make_pdf("Shagun Tiwari - FastAPI Developer")
    files = {"file": ("test_resume.pdf", valid_pdf, "application/pdf")}
    
    response = client.post("/api/resume/upload", headers=headers, files=files)
    
    assert response.status_code == 200
    analysis = response.json().get("analysis", {})
    assert len(analysis["skills"]) == 1

@patch(GEMINI_MOCK_PATH)
def test_llm_empty_response(mock_generate, client, resume_token, make_pdf):
    """Verifies that an empty string from Gemini returns a 502 error."""
    headers = {"Authorization": f"Bearer {resume_token}"}
    mock_generate.return_value = MockResponse("   ")
    
    valid_pdf = make_pdf("Shagun Tiwari - Resume Content")
    files = {"file": ("test_resume.pdf", valid_pdf, "application/pdf")}
    
    response = client.post("/api/resume/upload", headers=headers, files=files)
    
    assert response.status_code == 502
    assert "empty response" in response.json()["detail"].lower()

@patch(GEMINI_MOCK_PATH)
def test_llm_non_dict_json_response(mock_generate, client, resume_token, make_pdf):
    """Verifies that valid JSON of the wrong root type (e.g., list instead of dict) is caught."""
    headers = {"Authorization": f"Bearer {resume_token}"}
    mock_generate.return_value = MockResponse('[{"skills": "Python"}]')
    
    valid_pdf = make_pdf("Shagun Tiwari - Resume Content")
    files = {"file": ("test_resume.pdf", valid_pdf, "application/pdf")}
    
    response = client.post("/api/resume/upload", headers=headers, files=files)
    
    assert response.status_code == 502
    assert "unexpected response format" in response.json()["detail"].lower()

@patch(GEMINI_MOCK_PATH)
def test_llm_schema_hallucination(mock_generate, client, resume_token, make_pdf):
    """Verifies extra hallucinated fields are stripped by Pydantic and never leaked."""
    headers = {"Authorization": f"Bearer {resume_token}"}
    hallucinated_data = {
        "skills": [{"name": "FastAPI", "level": "Intermediate"}],
        "education": [],
        "experience": [],
        "projects": [],
        "made_up_field": "Should be stripped",
        "hacker_injection": True
    }
    mock_generate.return_value = MockResponse(json.dumps(hallucinated_data))
    
    valid_pdf = make_pdf("Shagun Tiwari - FastAPI")
    files = {"file": ("test_resume.pdf", valid_pdf, "application/pdf")}
    
    response = client.post("/api/resume/upload", headers=headers, files=files)
    
    assert response.status_code == 200
    analysis_data = response.json().get("analysis", {})
    assert "skills" in analysis_data
    assert "made_up_field" not in analysis_data
    assert "hacker_injection" not in analysis_data

@patch(GEMINI_MOCK_PATH)
def test_llm_schema_validation_error(mock_generate, client, resume_token, make_pdf):
    headers = {"Authorization": f"Bearer {resume_token}"}
    
    # Omit the required 'name' field entirely. Pydantic cannot auto-coerce a missing field.
    invalid_schema_data = {
        "skills": [{"level": "Advanced"}], 
        "education": [],
        "experience": [],
        "projects": []
    }
    mock_generate.return_value = MockResponse(json.dumps(invalid_schema_data))
    
    valid_pdf = make_pdf("Shagun Tiwari - Resume Content")
    files = {"file": ("test_resume.pdf", valid_pdf, "application/pdf")}
    
    response = client.post("/api/resume/upload", headers=headers, files=files)
    
    assert response.status_code == 502
    assert "expected format" in response.json()["detail"].lower()

    
@patch(CLIENT_MOCK_PATH)
def test_llm_tenacity_retry_exhaustion(mock_client_gen, client, resume_token, make_pdf):
    """Verifies tenacity retries exactly 3 times on 503 errors before raising 502."""
    headers = {"Authorization": f"Bearer {resume_token}"}
    
    class ServiceUnavailableError(Exception):
        code = 503

    mock_client_gen.side_effect = ServiceUnavailableError("503 Service Unavailable")
    
    valid_pdf = make_pdf("Shagun Tiwari - Resume Content")
    files = {"file": ("test_resume.pdf", valid_pdf, "application/pdf")}
    
    response = client.post("/api/resume/upload", headers=headers, files=files)
    
    assert response.status_code == 502
    assert mock_client_gen.call_count == 3


@patch(CLIENT_MOCK_PATH)
def test_llm_rate_limit_handling(mock_client_gen, client, resume_token, make_pdf):
    """Verifies the backend handles 429 Too Many Requests (Quota Exceeded) from Google."""
    headers = {"Authorization": f"Bearer {resume_token}"}
    
    class RateLimitError(Exception):
        code = 429

    mock_client_gen.side_effect = RateLimitError("429 Quota Exceeded")
    
    valid_pdf = make_pdf("Shagun Tiwari - Resume Content")
    files = {"file": ("test_resume.pdf", valid_pdf, "application/pdf")}
    
    response = client.post("/api/resume/upload", headers=headers, files=files)
    
    # Asserting that your backend catches this and prevents a total crash
    assert response.status_code in [429, 500, 502, 503]

@patch(CLIENT_MOCK_PATH)
def test_llm_network_timeout(mock_client_gen, client, resume_token, make_pdf):
    """Verifies the backend does not hang indefinitely if the LLM API stalls."""
    headers = {"Authorization": f"Bearer {resume_token}"}
    
    mock_client_gen.side_effect = httpx.TimeoutException("Connection timed out")
    
    valid_pdf = make_pdf("Shagun Tiwari - Resume Content")
    files = {"file": ("test_resume.pdf", valid_pdf, "application/pdf")}
    
    response = client.post("/api/resume/upload", headers=headers, files=files)
    
    assert response.status_code in [500, 502, 504]

 