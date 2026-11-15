from uuid import uuid4
from unittest.mock import patch

from fastapi import HTTPException

from app.database.mongodb import db
from app.services.roadmap_service import save_roadmap

def test_generate_roadmap_success(client, resume_token):
    """Verifies the roadmap generation endpoint securely chains the internal services."""
    
    mock_gap = {"target_role": "Backend Engineer", "missing_skills": ["docker", "aws"]}
    mock_prioritized = {
        "target_role": "Backend Engineer", 
        "prioritized_skills": [{
            "skill": "docker",
            "priority": "High",
            "priority_score": 90,
            "priority_rank": 1,
        }]
    }
    mock_roadmap_result = {
        "target_role": "Backend Engineer",
        "roadmap": [
            {
                "skill": "docker",
                "priority": "High",
                "priority_score": 90,
                "priority_rank": 1,
                "status": "Not Started",
            }
        ]
    }

    with patch("app.routes.roadmap.calculate_skill_gap", return_value=mock_gap), \
         patch("app.routes.roadmap.prioritize_missing_skills", return_value=mock_prioritized), \
         patch("app.routes.roadmap.generate_roadmap", return_value=mock_roadmap_result), \
         patch("app.routes.roadmap.save_roadmap") as mock_save:
        
        # The resume_token fixture already authenticated the client. 
        # We rely entirely on the internal cookie jar.
        response = client.post("/roadmap/generate")
        
        assert response.status_code == 200
        data = response.json()
        assert data["target_role"] == "Backend Engineer"
        assert len(data["roadmap"]) == 1
        assert data["roadmap"][0]["skill"] == "docker"
        assert data["roadmap"][0]["status"] == "Not Started"
        
        mock_save.assert_called_once()

def test_generate_roadmap_unauthorized(client):
    """Verifies unauthenticated users are blocked from generating roadmaps."""
    client.cookies.clear()
    response = client.post("/roadmap/generate")
    assert response.status_code == 401

def test_generate_roadmap_missing_data(client, resume_token):
    """Verifies that generating a roadmap before uploading a resume or target yields 404."""
    # Simulate the skill gap service aborting because the user hasn't uploaded a resume
    with patch("app.routes.roadmap.calculate_skill_gap", side_effect=HTTPException(status_code=404, detail="Resume not found")):
        response = client.post("/roadmap/generate")
        assert response.status_code == 404

def test_generate_roadmap_perfect_match(client, resume_token):
    """Verifies behavior when the user already possesses all required skills."""
    mock_gap = {"target_role": "Backend Engineer", "missing_skills": []}
    mock_prioritized = {"target_role": "Backend Engineer", "prioritized_skills": []}
    mock_roadmap_result = {"target_role": "Backend Engineer", "roadmap": []}

    with patch("app.routes.roadmap.calculate_skill_gap", return_value=mock_gap), \
         patch("app.routes.roadmap.prioritize_missing_skills", return_value=mock_prioritized), \
         patch("app.routes.roadmap.generate_roadmap", return_value=mock_roadmap_result), \
         patch("app.routes.roadmap.save_roadmap") as mock_save:
        
        response = client.post("/roadmap/generate")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["roadmap"]) == 0
        mock_save.assert_called_once()

def test_generate_roadmap_database_outage(client, resume_token):
    """Verifies that a MongoDB connection drop during the save operation is handled."""
    mock_gap = {"target_role": "Backend Engineer", "missing_skills": ["docker"]}
    mock_prioritized = {
        "target_role": "Backend Engineer",
        "prioritized_skills": [{
            "skill": "docker",
            "priority": "High",
            "priority_score": 90,
            "priority_rank": 1,
        }],
    }
    mock_roadmap_result = {
        "target_role": "Backend Engineer",
        "roadmap": [{
            "skill": "docker",
            "priority": "High",
            "priority_score": 90,
            "priority_rank": 1,
            "status": "Not Started",
        }],
    }

    with patch("app.routes.roadmap.calculate_skill_gap", return_value=mock_gap), \
         patch("app.routes.roadmap.prioritize_missing_skills", return_value=mock_prioritized), \
         patch("app.routes.roadmap.generate_roadmap", return_value=mock_roadmap_result), \
         patch("app.routes.roadmap.save_roadmap", side_effect=Exception("DB Connection Lost")):
        
        response = client.post("/roadmap/generate")
        assert response.status_code == 500

def test_generate_roadmap_wrong_method(client, resume_token):
    """Verifies that sending a GET request to a POST-only route is rejected (405)."""
    response = client.get("/roadmap/generate")
    assert response.status_code == 405

def test_generate_roadmap_malformed_token(client):
    """Verifies that a fake or corrupted JWT cookie is rejected (401)."""
    client.cookies.clear()
    client.cookies.set("skillbridge_auth", "eyJhbGciOiJIUzI1NiIsIn.fake.token")
    
    response = client.post("/roadmap/generate")
    assert response.status_code == 401

def test_generate_roadmap_missing_target(client, resume_token):
    """Verifies behavior when the user has a resume but no target role set."""
    # Simulate the skill gap service aborting due to missing target
    with patch("app.routes.roadmap.calculate_skill_gap", side_effect=HTTPException(status_code=404, detail="Target role not found")):
        response = client.post("/roadmap/generate")
        assert response.status_code == 404
        assert "target" in response.json()["detail"].lower()

def test_generate_roadmap_ai_crash(client, resume_token):
    """Verifies handling of an upstream Gemini API timeout during roadmap generation."""
    mock_gap = {"target_role": "Backend", "missing_skills": ["aws"]}
    mock_prioritized = {
        "target_role": "Backend",
        "prioritized_skills": [{
            "skill": "aws",
            "priority": "High",
            "priority_score": 90,
            "priority_rank": 1,
        }],
    }

    with patch("app.routes.roadmap.calculate_skill_gap", return_value=mock_gap), \
         patch("app.routes.roadmap.prioritize_missing_skills", return_value=mock_prioritized), \
         patch("app.routes.roadmap.generate_roadmap", side_effect=Exception("Gemini API Timeout")):
        
        response = client.post("/roadmap/generate")
        assert response.status_code in [500, 502]


def test_save_roadmap_advances_version_and_preserves_progress():
    user_email = f"roadmap_{uuid4().hex}@example.com"
    db.roadmaps.insert_one(
        {
            "user_email": user_email,
            "target_role": "Backend Engineer",
            "progress_version": 4,
            "roadmap": [
                {
                    "skill": "Python",
                    "status": "Completed",
                    "subtopics": [
                        {"title": "Basics", "status": "In Progress"},
                    ],
                },
            ],
        }
    )
    generated_roadmap = [
        {
            "skill": "Python",
            "status": "Not Started",
            "subtopics": [
                {"title": "Basics", "status": "Not Started"},
            ],
        },
    ]

    try:
        save_roadmap(
            user_email,
            "Backend Engineer",
            generated_roadmap,
        )

        saved_document = db.roadmaps.find_one({"user_email": user_email})
        saved_skill = saved_document["roadmap"][0]

        assert saved_document["progress_version"] == 5
        assert saved_skill["status"] == "Completed"
        assert saved_skill["subtopics"][0]["status"] == "In Progress"
        assert generated_roadmap[0]["status"] == "Not Started"
    finally:
        db.roadmaps.delete_one({"user_email": user_email})