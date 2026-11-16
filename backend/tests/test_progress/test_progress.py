from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Lock
from uuid import uuid4
from unittest.mock import patch

from fastapi import HTTPException
import jwt

from app.database.mongodb import db
from app.services import progress_service
from app.utils.security import JWT_ALGORITHM, JWT_SECRET

mock_progress_data = {
    "target_role": "Backend Engineer",
    "roadmap": [
        {
            "skill": "docker",
            "priority": "High",
            "priority_score": 90,
            "priority_rank": 1,
            "status": "In Progress",
        }
    ],
    "overall_progress": 50.0
}

def test_read_progress_success(client, resume_token):
    """Verifies successful retrieval of the user's progress."""
    with patch("app.routes.progress.get_progress", return_value=mock_progress_data):
        response = client.get("/progress")
        assert response.status_code == 200
        data = response.json()
        assert data["overall_progress"] == 50.0
        assert len(data["roadmap"]) == 1

def test_read_progress_unauthorized(client):
    """Verifies unauthenticated users are blocked from reading progress."""
    client.cookies.clear()
    response = client.get("/progress")
    assert response.status_code == 401

def test_read_progress_not_found(client, resume_token):
    """Verifies behavior when the user has not generated a roadmap yet."""
    with patch("app.routes.progress.get_progress", side_effect=HTTPException(status_code=404, detail="Roadmap not found")):
        response = client.get("/progress")
        assert response.status_code == 404

def test_update_progress_success(client, resume_token):
    """Verifies successful status update for a valid skill."""
    with patch("app.routes.progress.update_skill_progress", return_value=mock_progress_data) as mock_update:
        response = client.patch("/progress/update", json={"skill": "docker", "status": "In Progress"})
        assert response.status_code == 200
        mock_update.assert_called_once()

def test_update_progress_schema_validation(client, resume_token):
    """Verifies Pydantic strict regex pattern blocks invalid statuses."""
    # "Finished" is not in the allowed regex: ^(Not Started|In Progress|Completed)$
    response = client.patch("/progress/update", json={"skill": "docker", "status": "Finished"})
    
    assert response.status_code == 422
    data = response.json()
    assert data["detail"][0]["type"] == "string_pattern_mismatch"

def test_update_progress_missing_payload(client, resume_token):
    """Verifies 422 error when the request body is missing."""
    response = client.patch("/progress/update")
    assert response.status_code == 422

def test_update_progress_unauthorized(client):
    """Verifies unauthenticated users are blocked from updating progress."""
    client.cookies.clear()
    response = client.patch("/progress/update", json={"skill": "docker", "status": "Completed"})
    assert response.status_code == 401


def test_update_subtopic_progress_unauthorized(client):
    client.cookies.clear()
    response = client.patch(
        "/api/progress/subtopic/update",
        json={
            "skill": "Python",
            "subtopic": "Basics",
            "status": "Completed",
        },
    )

    assert response.status_code == 401

def test_read_progress_wrong_method(client, resume_token):
    """Verifies that sending a POST request to a GET-only route is rejected (405)."""
    response = client.post("/progress")
    assert response.status_code == 405

def test_update_progress_wrong_method(client, resume_token):
    """Verifies that sending a GET request to a PATCH-only route is rejected (405)."""
    response = client.get("/progress/update")
    assert response.status_code == 405

def test_progress_malformed_token(client):
    """Verifies that a fake or corrupted JWT cookie is rejected (401)."""
    client.cookies.clear()
    client.cookies.set("skillbridge_auth", "eyJhbGciOiJIUzI1NiIsIn.fake.token")
    
    response_get = client.get("/progress")
    assert response_get.status_code == 401
    
    response_patch = client.patch("/progress/update", json={"skill": "docker", "status": "Completed"})
    assert response_patch.status_code == 401

def test_update_progress_skill_not_found(client, resume_token):
    """Verifies a 404 error when attempting to update a skill not in the user's roadmap."""
    with patch("app.routes.progress.update_skill_progress", side_effect=HTTPException(status_code=404, detail="Skill not found")):
        response = client.patch("/progress/update", json={"skill": "unknown_skill", "status": "In Progress"})
        assert response.status_code == 404

def test_read_progress_database_outage(client, resume_token):
    """Verifies that a database connection drop during progress retrieval is exposed."""
    with patch("app.routes.progress.get_progress", side_effect=Exception("DB Connection Lost")):
        response = client.get("/progress")
        assert response.status_code == 500

def test_update_progress_database_outage(client, resume_token):
    """Verifies that a database connection drop during a status update is exposed."""
    with patch("app.routes.progress.update_skill_progress", side_effect=Exception("DB Connection Lost")):
        response = client.patch("/progress/update", json={"skill": "docker", "status": "Completed"})
        assert response.status_code == 500

def test_update_progress_empty_skill(client, resume_token):
    """Verifies behavior when the frontend sends an empty string for the skill."""
    # The service layer should reject an empty string as a non-existent skill
    with patch("app.routes.progress.update_skill_progress", side_effect=HTTPException(status_code=404, detail="Skill not found")):
        response = client.patch("/progress/update", json={"skill": "", "status": "Completed"})
        assert response.status_code == 422

def test_update_progress_invalid_data_type(client, resume_token):
    """Verifies Pydantic handles invalid data types safely without crashing (500)."""
    # Sending a boolean and an integer instead of strings
    response = client.patch("/progress/update", json={"skill": True, "status": 123})
    
    assert response.status_code == 422

def test_update_progress_extra_payload_fields(client, resume_token):
    """Verifies Pydantic safely strips unrequested/malicious fields from the payload."""
    with patch("app.routes.progress.update_skill_progress", return_value=mock_progress_data) as mock_update:
        # Injecting a fake "admin_bypass" field
        response = client.patch(
            "/progress/update", 
            json={"skill": "docker", "status": "Completed", "admin_bypass": True}
        )
        
        assert response.status_code == 200
        mock_update.assert_called_once()

def test_read_progress_100_percent_completion(client, resume_token):
    """Verifies the response structure mathematically handles 100% completion."""
    perfect_mock = {
        "target_role": "Backend Engineer",
        "roadmap": [{
            "skill": "docker",
            "priority": "High",
            "priority_score": 90,
            "priority_rank": 1,
            "status": "Completed",
        }],
        "overall_progress": 100.0
    }
    with patch("app.routes.progress.get_progress", return_value=perfect_mock):
        response = client.get("/progress")
        assert response.status_code == 200
        assert response.json()["overall_progress"] == 100.0


def test_concurrent_skill_progress_updates_are_not_lost(monkeypatch):
    user_email = f"progress_{uuid4().hex}@example.com"
    db.roadmaps.insert_one(
        {
            "user_email": user_email,
            "target_role": "Backend Engineer",
            "roadmap": [
                {"skill": "Python", "status": "Not Started", "subtopics": []},
                {"skill": "Docker", "status": "Not Started", "subtopics": []},
            ],
        }
    )

    original_get_roadmap_document = progress_service._get_roadmap_document
    initial_reads_barrier = Barrier(2)
    read_lock = Lock()
    initial_read_count = 0

    def synchronized_get_roadmap_document(email):
        nonlocal initial_read_count
        roadmap_document = original_get_roadmap_document(email)

        with read_lock:
            should_wait = initial_read_count < 2
            initial_read_count += 1

        if should_wait:
            initial_reads_barrier.wait(timeout=5)

        return roadmap_document

    monkeypatch.setattr(
        progress_service,
        "_get_roadmap_document",
        synchronized_get_roadmap_document,
    )

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            updates = [
                executor.submit(
                    progress_service.update_skill_progress,
                    user_email,
                    "Python",
                    "Completed",
                ),
                executor.submit(
                    progress_service.update_skill_progress,
                    user_email,
                    "Docker",
                    "Completed",
                ),
            ]
            for update in updates:
                update.result(timeout=10)

        saved_roadmap = db.roadmaps.find_one({"user_email": user_email})
        statuses = {
            item["skill"]: item["status"]
            for item in saved_roadmap["roadmap"]
        }

        assert statuses == {
            "Python": "Completed",
            "Docker": "Completed",
        }
        assert saved_roadmap["progress_version"] == 2
    finally:
        db.roadmaps.delete_one({"user_email": user_email})


def test_subtopic_progress_endpoint_updates_parent_status_and_percentage(
    client,
    resume_token,
):
    user_email = jwt.decode(
        resume_token,
        JWT_SECRET,
        algorithms=[JWT_ALGORITHM],
    )["sub"]
    db.roadmaps.insert_one({
        "user_email": user_email,
        "target_role": "Backend Engineer",
        "roadmap": [{
            "skill": "Python",
            "priority": "High",
            "priority_score": 90,
            "priority_rank": 1,
            "status": "Not Started",
            "subtopics": [
                {"title": "Basics", "status": "Not Started"},
                {"title": "Testing", "status": "Not Started"},
            ],
        }],
    })

    try:
        first = client.patch(
            "/api/progress/subtopic/update",
            json={
                "skill": "python",
                "subtopic": "basics",
                "status": "Completed",
            },
        )
        assert first.status_code == 200
        assert first.json()["roadmap"][0]["status"] == "In Progress"
        assert first.json()["overall_progress"] == 50

        second = client.patch(
            "/api/progress/subtopic/update",
            json={
                "skill": "Python",
                "subtopic": "Testing",
                "status": "Completed",
            },
        )
        assert second.status_code == 200
        assert second.json()["roadmap"][0]["status"] == "Completed"
        assert second.json()["overall_progress"] == 100

        reset = client.patch(
            "/api/progress/subtopic/update",
            json={
                "skill": "Python",
                "subtopic": "Basics",
                "status": "Not Started",
            },
        )
        assert reset.status_code == 200
        assert reset.json()["roadmap"][0]["status"] == "In Progress"
        assert reset.json()["overall_progress"] == 50

        missing_subtopic = client.patch(
            "/api/progress/subtopic/update",
            json={
                "skill": "Python",
                "subtopic": "Unknown",
                "status": "Completed",
            },
        )
        assert missing_subtopic.status_code == 404

        invalid_status = client.patch(
            "/api/progress/subtopic/update",
            json={
                "skill": "Python",
                "subtopic": "Basics",
                "status": "Finished",
            },
        )
        assert invalid_status.status_code == 422
    finally:
        db.roadmaps.delete_one({"user_email": user_email})

    