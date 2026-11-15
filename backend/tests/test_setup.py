import uuid

import pytest
from pymongo.errors import DuplicateKeyError

from app.database.mongodb import db, ensure_indexes
from app.main import validate_configuration


def test_database_is_mocked(client):
    # This verifies that the app is using the fake database, not Sanya's real one
    assert db.name == "skillbridge_test"


def test_unique_indexes_are_enforced(client):
    unique_field_by_collection = {
        "users": "email",
        "resumes": "user_email",
        "targets": "user_email",
        "roadmaps": "user_email",
    }

    for collection_name, field in unique_field_by_collection.items():
        value = f"index-test-{uuid.uuid4().hex}@example.com"
        collection = db[collection_name]
        collection.insert_one({field: value})

        try:
            with pytest.raises(DuplicateKeyError):
                collection.insert_one({field: value})
        finally:
            collection.delete_many({field: value})


@pytest.mark.parametrize(
    ("setting", "value"),
    [
        ("MONGODB_URI", ""),
        ("MONGODB_URI", "https://not-mongodb.example"),
        ("MONGODB_URI", "mongodb://localhost:not-a-port"),
        ("DATABASE_NAME", ""),
        ("DATABASE_NAME", "invalid/name"),
        ("JWT_SECRET", "your_jwt_secret_here"),
        ("JWT_SECRET", "short-secret"),
        ("LOGIN_RATE_LIMIT_WINDOW_SECONDS", 0),
        ("LOGIN_RATE_LIMIT_EMAIL_IP_MAX_ATTEMPTS", 0),
        ("LOGIN_RATE_LIMIT_IP_MAX_ATTEMPTS", -1),
    ],
)
def test_invalid_required_configuration_is_rejected(
    monkeypatch,
    setting,
    value,
):
    defaults = {
        "MONGODB_URI": "mongodb://localhost:27017",
        "DATABASE_NAME": "skillbridge_test",
        "JWT_SECRET": "skillbridge-test-only-secret-not-for-production",
        "LOGIN_RATE_LIMIT_WINDOW_SECONDS": 900,
        "LOGIN_RATE_LIMIT_EMAIL_IP_MAX_ATTEMPTS": 5,
        "LOGIN_RATE_LIMIT_IP_MAX_ATTEMPTS": 30,
    }
    for name, default in defaults.items():
        monkeypatch.setattr("app.main." + name, default)
    monkeypatch.setattr("app.main." + setting, value)

    with pytest.raises(RuntimeError, match=setting):
        validate_configuration()


def test_unique_index_setup_is_idempotent(client):
    ensure_indexes()


def test_roadmap_unique_index_excludes_unowned_legacy_records(client):
    index = db.roadmaps.index_information()["user_email_1"]
    assert index["partialFilterExpression"] == {
        "user_email": {"$type": "string"}
    }


def test_login_rate_limit_index_expires_old_buckets(client):
    index = db.login_rate_limits.index_information()["expires_at_1"]
    assert index["expireAfterSeconds"] == 0