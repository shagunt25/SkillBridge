import io
import uuid
import fitz
import mongomock
import pytest
from fastapi.testclient import TestClient

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


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="function")
def resume_token(client):
    """Provisions a verified test user and cleans up the DB record after the test."""
    unique_email = f"resume_{uuid.uuid4().hex[:8]}@example.com"
    password = "StrictTestPassword99!"

    client.post(
        "/api/auth/signup",
        json={
            "name": "Resume Tester",
            "email": unique_email,
            "password": password,
        },
    )

    # Use mock_db directly instead of undefined 'db'
    mock_db.users.update_one(
        {"email": unique_email},
        {"$set": {"email_verified": True, "is_verified": True}},
    )

    response = client.post(
        "/api/auth/login",
        json={"email": unique_email, "password": password},
    )
    token = response.json().get("access_token") or response.json().get("token")

    yield token

    # Teardown
    mock_db.users.delete_one({"email": unique_email})


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

