import jwt
from app.database.mongodb import db
from app.utils.security import JWT_SECRET, JWT_ALGORITHM

def get_test_user_email(client):
    """Helper to extract the test user's email from the secure cookie."""
    token = next((cookie.value for cookie in client.cookies.jar if cookie.name == "skillbridge_auth"), None)
    if not token:
        return None
    payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    return payload.get("sub")


def test_skill_gap_happy_path(client, resume_token):
    """Verifies the pure Python set math correctly calculates matched, missing, and extra skills."""
    user_email = get_test_user_email(client)
    db.resumes.delete_many({"user_email": user_email})
    db.targets.delete_many({"user_email": user_email})
    
    db.resumes.insert_one({
        "user_email": user_email, 
        "skills": [{"name": "python"}, {"name": "fastapi"}, {"name": "docker"}]
    })
    
    db.targets.insert_one({
        "user_email": user_email, 
        "target_role": "Backend Engineer", 
        "required_skills": ["python", "fastapi", "kubernetes"]
    })
    
    response = client.get("/analysis/skill-gap")
    
    assert response.status_code == 200
    data = response.json()
    assert data["target_role"] == "Backend Engineer"
    assert data["matched_skills"] == ["fastapi", "python"]
    assert data["missing_skills"] == ["kubernetes"]
    assert data["extra_skills"] == ["docker"]


def test_skill_gap_perfect_match(client, resume_token):
    """Verifies behavior when the user has exactly the skills required and nothing extra."""
    user_email = get_test_user_email(client)
    db.resumes.delete_many({"user_email": user_email})
    db.targets.delete_many({"user_email": user_email})
    
    db.resumes.insert_one({
        "user_email": user_email, 
        "skills": [{"name": "java"}, {"name": "spring"}]
    })
    
    db.targets.insert_one({
        "user_email": user_email, 
        "target_role": "Java Developer", 
        "required_skills": ["java", "spring"]
    })
    
    response = client.get("/analysis/skill-gap")
    
    assert response.status_code == 200
    data = response.json()
    assert data["matched_skills"] == ["java", "spring"]
    assert data["missing_skills"] == []
    assert data["extra_skills"] == []


def test_skill_gap_empty_resume_skills(client, resume_token):
    """Verifies math when a resume parses successfully but finds zero technical skills."""
    user_email = get_test_user_email(client)
    db.resumes.delete_many({"user_email": user_email})
    db.targets.delete_many({"user_email": user_email})
    
    db.resumes.insert_one({"user_email": user_email, "skills": []})
    db.targets.insert_one({
        "user_email": user_email, 
        "target_role": "Manager", 
        "required_skills": ["agile", "scrum"]
    })
    
    response = client.get("/analysis/skill-gap")
    
    assert response.status_code == 200
    data = response.json()
    assert data["matched_skills"] == []
    assert data["missing_skills"] == ["agile", "scrum"]
    assert data["extra_skills"] == []


def test_skill_gap_empty_target_skills(client, resume_token):
    """Verifies math when the target role requires no specific technical skills."""
    user_email = get_test_user_email(client)
    db.resumes.delete_many({"user_email": user_email})
    db.targets.delete_many({"user_email": user_email})
    
    db.resumes.insert_one({
        "user_email": user_email, 
        "skills": [{"name": "excel"}, {"name": "word"}]
    })
    
    db.targets.insert_one({
        "user_email": user_email, 
        "target_role": "Generalist", 
        "required_skills": []
    })
    
    response = client.get("/analysis/skill-gap")
    
    assert response.status_code == 200
    data = response.json()
    assert data["matched_skills"] == []
    assert data["missing_skills"] == []
    assert data["extra_skills"] == ["excel", "word"]


def test_skill_gap_missing_resume(client, resume_token):
    """Verifies a 404 is returned if the user set a target but hasn't uploaded a resume."""
    user_email = get_test_user_email(client)
    db.resumes.delete_many({"user_email": user_email})
    
    db.targets.update_one(
        {"user_email": user_email},
        {"$set": {"target_role": "Backend", "required_skills": ["python"]}},
        upsert=True
    )
    
    response = client.get("/analysis/skill-gap")
    assert response.status_code == 404
    assert "resume" in response.json()["detail"].lower()


def test_skill_gap_missing_target(client, resume_token):
    """Verifies a 404 is returned if the user uploaded a resume but hasn't set a target."""
    user_email = get_test_user_email(client)
    db.targets.delete_many({"user_email": user_email})
    
    db.resumes.update_one(
        {"user_email": user_email},
        {"$set": {"skills": [{"name": "python"}]}},
        upsert=True
    )
    
    response = client.get("/analysis/skill-gap")
    assert response.status_code == 404
    assert "target role" in response.json()["detail"].lower()


def test_skill_gap_unauthorized(client):
    """Verifies the endpoint is strictly protected by the auth dependency."""
    client.cookies.clear()
    response = client.get("/analysis/skill-gap")
    assert response.status_code == 401

def test_skill_gap_case_insensitivity(client, resume_token):
    """STRICT VULNERABILITY CHECK: Verifies the engine normalizes casing and whitespace."""
    user_email = get_test_user_email(client)
    db.resumes.delete_many({"user_email": user_email})
    db.targets.delete_many({"user_email": user_email})
    
    # Resume contains uppercase and padded whitespace
    db.resumes.insert_one({
        "user_email": user_email, 
        "skills": [{"name": "Python"}, {"name": " REST APIs "}]
    })
    
    # Target role generates clean lowercase
    db.targets.insert_one({
        "user_email": user_email, 
        "target_role": "Backend", 
        "required_skills": ["python", "rest apis"]
    })
    
    response = client.get("/analysis/skill-gap")
    assert response.status_code == 200
    data = response.json()
    
    # If the backend lacks .lower().strip(), these will incorrectly flag as missing/extra
    assert data["matched_skills"] == ["python", "rest apis"], "VULNERABILITY: Skill gap engine is case-sensitive!"
    assert data["missing_skills"] == []
    assert data["extra_skills"] == []


def test_skill_gap_corrupted_db_data(client, resume_token):
    """Verifies the engine survives missing 'name' keys in the DB without a 500 crash."""
    user_email = get_test_user_email(client)
    db.resumes.delete_many({"user_email": user_email})
    db.targets.delete_many({"user_email": user_email})
    
    # Corrupted database entry lacking the 'name' key entirely
    db.resumes.insert_one({
        "user_email": user_email, 
        "skills": [{"level": "expert"}] 
    })
    
    db.targets.insert_one({
        "user_email": user_email, 
        "target_role": "Backend", 
        "required_skills": ["python"]
    })
    
    response = client.get("/analysis/skill-gap")
    # Must skip the corrupted skill and calculate normally rather than throwing a KeyError
    assert response.status_code == 200

