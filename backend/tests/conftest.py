import io
import os
import uuid
import fitz
import mongomock
import pytest
from fastapi.testclient import TestClient

# Keep automated auth flows isolated from real email accounts.
os.environ["EMAIL_BACKEND"] = "console"
os.environ["MONGODB_URI"] = "mongodb://localhost:27017"
os.environ["DATABASE_NAME"] = "skillbridge_test"
os.environ["JWT_SECRET"] = "skillbridge-test-only-secret-not-for-production"
os.environ["LOGIN_RATE_LIMIT_EMAIL_IP_MAX_ATTEMPTS"] = "1000"
os.environ["LOGIN_RATE_LIMIT_IP_MAX_ATTEMPTS"] = "1000"
os.environ["OTP_RATE_LIMIT_IP_MAX_REQUESTS"] = "1000"
os.environ["OTP_RATE_LIMIT_EMAIL_MAX_REQUESTS"] = "1000"


def pytest_configure(config):
    config.addinivalue_line(
        "filterwarnings",
        "ignore:datetime\\.datetime\\.utcnow\\(\\) is deprecated:"
        "DeprecationWarning:mongomock\\.helpers",
    )

# 1. Import database module first
import app.database.mongodb as mongodb

# 2. Create the mock in-memory database
mock_client = mongomock.MongoClient()
mock_db = mock_client["skillbridge_test"]

# 3. Patch the global client and db objects
mongodb.client = mock_client
mongodb.db = mock_db

# 4. Import app after patching
from app.main import app


@pytest.fixture
def client():
    with TestClient(
        app,
        headers={"Sec-Fetch-Site": "same-origin"},
    ) as c:
        yield c


@pytest.fixture(scope="function")
def resume_token(client):
    """Provisions a verified test user and cleans up the DB record after the test."""
    unique_email = f"resume_{uuid.uuid4().hex[:8]}@example.com"
    password = "StrictTestPassword99!"

    signup_response = client.post(
        "/api/auth/signup",
        json={
            "name": "Resume Tester",
            "email": unique_email,
            "password": password,
        },
    )
    assert signup_response.status_code == 200

    verified = mock_db.users.update_one(
        {"email": unique_email},
        {"$set": {"email_verified": True, "is_verified": True}},
    )
    assert verified.matched_count == 1

    response = client.post(
        "/api/auth/login",
        json={"email": unique_email, "password": password},
    )
    assert response.status_code == 200
    token = client.cookies.get("skillbridge_auth")
    assert token

    yield token

    client.cookies.clear()
    mock_db.users.delete_one({"email": unique_email})
    for collection_name, query in (
        ("resumes", {"user_email": unique_email}),
        ("targets", {"user_email": unique_email}),
        ("roadmaps", {"user_email": unique_email}),
        ("email_otps", {"email": unique_email}),
        ("password_reset_tokens", {"email": unique_email}),
    ):
        mock_db[collection_name].delete_many(query)


@pytest.fixture
def make_pdf():
    """Helper fixture to generate real, valid in-memory PDFs using PyMuPDF."""
    def _make_pdf(text: str = "", encrypt: bool = False, password: str = "secret") -> io.BytesIO:
        doc = fitz.open()
        page = doc.new_page()
        if text:
            page.insert_text((72, 72), text)

        pdf_bytes = io.BytesIO()
        if encrypt:
            doc.save(
                pdf_bytes,
                encryption=fitz.PDF_ENCRYPT_AES_256,
                owner_pw=password,
                user_pw=password,
            )
        else:
            doc.save(pdf_bytes)
        doc.close()
        pdf_bytes.seek(0)
        return pdf_bytes

    return _make_pdf

