from unittest.mock import patch
from fastapi import HTTPException

# A perfect dashboard where the user has completed the entire journey
mock_full_dashboard = {
    "name": "Shagun Tiwari",
    "email": "resume_test@example.com",
    "current_skills": ["python", "docker"],
    "target_role": "Backend Engineer",
    "required_skills": ["python", "docker", "aws"],
    "matched_skills": ["python", "docker"],
    "missing_skills": ["aws"],
    "roadmap": [{"skill": "aws", "priority": "High", "status": "In Progress"}],
    "overall_progress": 50.0
}

# A partial dashboard where the user just signed up and uploaded a resume
mock_partial_dashboard = {
    "name": "Shagun Tiwari",
    "email": "resume_test@example.com",
    "current_skills": ["python", "docker"],
    "target_role": None,
    "required_skills": [],
    "matched_skills": [],
    "missing_skills": [],
    "roadmap": [],
    "overall_progress": 0.0
}

def test_read_dashboard_success(client, resume_token):
    """Verifies successful retrieval of a fully populated dashboard."""
    with patch("app.routes.dashboard.get_dashboard", return_value=mock_full_dashboard):
        response = client.get("/dashboard")
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "Shagun Tiwari"
        assert data["target_role"] == "Backend Engineer"
        assert len(data["roadmap"]) == 1

def test_read_dashboard_partial_state(client, resume_token):
    """Verifies the dashboard safely handles users who haven't set a target role yet."""
    with patch("app.routes.dashboard.get_dashboard", return_value=mock_partial_dashboard):
        response = client.get("/dashboard")
        assert response.status_code == 200
        
        data = response.json()
        assert data["target_role"] is None
        assert data["overall_progress"] == 0.0
        assert len(data["current_skills"]) == 2

def test_read_dashboard_unauthorized(client):
    """Verifies unauthenticated users cannot view a dashboard."""
    client.cookies.clear()
    response = client.get("/dashboard")
    assert response.status_code == 401

def test_read_dashboard_malformed_token(client):
    """Verifies fake or corrupted JWT cookies are blocked (401)."""
    client.cookies.clear()
    client.cookies.set("skillbridge_auth", "eyJhbGciOiJIUzI1NiIsIn.fake.token")
    
    response = client.get("/dashboard")
    assert response.status_code == 401

def test_read_dashboard_wrong_method(client, resume_token):
    """Verifies that sending a POST request to a GET-only route is rejected (405)."""
    response = client.post("/dashboard")
    assert response.status_code == 405

def test_read_dashboard_not_found(client, resume_token):
    """Verifies behavior if the dashboard service cannot find the user."""
    with patch("app.routes.dashboard.get_dashboard", side_effect=HTTPException(status_code=404, detail="User not found")):
        response = client.get("/dashboard")
        assert response.status_code == 404

def test_read_dashboard_database_outage(client, resume_token):
    """Verifies handling of a MongoDB connection drop during aggregation."""
    with patch("app.routes.dashboard.get_dashboard", side_effect=Exception("DB Connection Lost")):
        response = client.get("/dashboard")
        # If there is no try...except block in dashboard.py, this will raise 500
        assert response.status_code == 500

def test_read_dashboard_perfect_completion(client, resume_token):
    """Verifies the dashboard safely handles a user who has completed 100% of their roadmap."""
    mock_completed_dashboard = {
        "name": "Shagun Tiwari",
        "email": "resume_test@example.com",
        "current_skills": ["python", "docker", "aws"],
        "target_role": "Backend Engineer",
        "required_skills": ["python", "docker", "aws"],
        "matched_skills": ["python", "docker", "aws"],
        "missing_skills": [],  # Empty list constraint
        "roadmap": [{"skill": "aws", "priority": "High", "status": "Completed"}],
        "overall_progress": 100.0
    }
    
    with patch("app.routes.dashboard.get_dashboard", return_value=mock_completed_dashboard):
        response = client.get("/dashboard")
        assert response.status_code == 200
        
        data = response.json()
        assert data["overall_progress"] == 100.0
        assert len(data["missing_skills"]) == 0
        assert data["roadmap"][0]["status"] == "Completed"

