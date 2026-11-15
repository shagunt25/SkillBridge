
import uuid
import pytest

from app.database.mongodb import db
from app.main import FRONTEND_ORIGINS


@pytest.fixture
def active_user_token(client):
    """Create a verified user and return the login token."""
    email = f"logout_{uuid.uuid4().hex[:8]}@example.com"
    password = "StrictTestPassword99!"

    client.cookies.clear()

    signup_response = client.post(
        "/api/auth/signup",
        json={
            "name": "Logout Tester",
            "email": email,
            "password": password,
        },
    )
    assert signup_response.status_code == 200

    db.users.update_one(
        {"email": email},
        {"$set": {"email_verified": True, "is_verified": True}},
    )

    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200

    token = None
    for cookie in client.cookies.jar:
        if cookie.name == "skillbridge_auth":
            token = cookie.value

    assert token, "Login did not set the authentication cookie"
    yield token
    client.cookies.clear()
    db.users.delete_one({"email": email})
    for collection_name, query in (
        ("email_otps", {"email": email}),
        ("password_reset_tokens", {"email": email}),
    ):
        db[collection_name].delete_many(query)


def test_logout_success(client, active_user_token):
    """An authenticated client can log out."""
    response = client.post("/api/auth/logout")
    assert response.status_code == 200
    assert response.json()["message"] == "Logged out successfully."


def test_logout_invalidates_token(client, active_user_token):
    """After logout, the client's authentication cookie is cleared."""
    response = client.post("/api/auth/logout")
    assert response.status_code == 200

    protected_response = client.get("/api/users/me")
    assert protected_response.status_code == 401


def test_logout_no_token(client):
    """Logout succeeds even when no authentication cookie is present."""
    client.cookies.clear()
    response = client.post("/api/auth/logout")
    assert response.status_code == 200


def test_logout_wrong_method(client):
    """GET is not supported for the logout endpoint."""
    response = client.get("/api/auth/logout")
    assert response.status_code == 405


def test_logout_malformed_token(client):
    """Logout succeeds even when the authentication cookie is malformed."""
    client.cookies.clear()
    client.cookies.set("skillbridge_auth", "not.a.real.jwt")

    response = client.post("/api/auth/logout")
    assert response.status_code == 200


def test_logout_clears_cookie(client, active_user_token):
    """Logout sends a cookie-clearing instruction."""
    response = client.post("/api/auth/logout")
    assert response.status_code == 200

    set_cookie_header = response.headers.get("set-cookie", "").lower()
    assert "skillbridge_auth=" in set_cookie_header
    assert (
        "max-age=0" in set_cookie_header
        or "expires=" in set_cookie_header
    )


def test_cors_preflight_allows_configured_frontend(client):
    origin = FRONTEND_ORIGINS[0]
    response = client.options(
        "/api/auth/login",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin
    assert response.headers["access-control-allow-credentials"] == "true"
    assert "POST" in response.headers["access-control-allow-methods"]


def test_cors_preflight_rejects_unconfigured_frontend(client):
    response = client.options(
        "/api/auth/login",
        headers={
            "Origin": "https://untrusted.example",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_csrf_origin_guard_allows_configured_origin(client):
    origin = FRONTEND_ORIGINS[0]
    response = client.post("/", headers={"Origin": origin})

    assert response.status_code == 405
    assert response.headers["access-control-allow-origin"] == origin


def test_csrf_origin_guard_allows_same_origin(client):
    response = client.post(
        "/",
        headers={"Origin": "http://testserver"},
    )

    assert response.status_code == 405


def test_csrf_origin_guard_rejects_missing_browser_metadata(client):
    response = client.post(
        "/",
        headers={"Sec-Fetch-Site": ""},
    )

    assert response.status_code == 403


@pytest.mark.parametrize(
    "headers",
    [
        {"Origin": "https://untrusted.example"},
        {"Referer": "https://untrusted.example/form"},
        {"Sec-Fetch-Site": "same-site"},
        {"Sec-Fetch-Site": "cross-site"},
    ],
)
def test_csrf_origin_guard_rejects_cross_site_mutations(client, headers):
    response = client.post("/", headers=headers)

    assert response.status_code == 403
    assert response.json()["detail"] == "Cross-origin request rejected."
