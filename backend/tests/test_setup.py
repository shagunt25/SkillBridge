import os
import uuid

import pytest
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

from app.database import mongodb
from app.database.mongodb import database_transaction, db, ensure_indexes
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
        ("OTP_RATE_LIMIT_WINDOW_SECONDS", 0),
        ("OTP_RATE_LIMIT_IP_MAX_REQUESTS", 0),
        ("OTP_RATE_LIMIT_EMAIL_MAX_REQUESTS", -1),
        ("OTP_RESEND_COOLDOWN_SECONDS", 0),
        ("OTP_EXPIRE_MINUTES", 0),
        ("OTP_MAX_ATTEMPTS", -1),
        ("JWT_EXPIRE_MINUTES", 0),
        ("AI_RATE_LIMIT_WINDOW_SECONDS", 0),
        ("AI_RATE_LIMIT_USER_MAX_REQUESTS", -1),
        ("COOKIE_NAME", ""),
        ("COOKIE_SAMESITE", "invalid"),
        ("COOKIE_SECURE_VALUE_VALID", False),
        ("EMAIL_BACKEND", "unknown"),
        ("SMTP_TIMEOUT_SECONDS", 0),
        ("SMTP_PORT", 70000),
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
        "OTP_RATE_LIMIT_WINDOW_SECONDS": 3600,
        "OTP_RATE_LIMIT_IP_MAX_REQUESTS": 10,
        "OTP_RATE_LIMIT_EMAIL_MAX_REQUESTS": 5,
        "OTP_RESEND_COOLDOWN_SECONDS": 60,
        "OTP_EXPIRE_MINUTES": 10,
        "OTP_MAX_ATTEMPTS": 5,
        "JWT_EXPIRE_MINUTES": 60,
        "AI_RATE_LIMIT_WINDOW_SECONDS": 3600,
        "AI_RATE_LIMIT_USER_MAX_REQUESTS": 20,
        "COOKIE_NAME": "skillbridge_auth",
        "COOKIE_SAMESITE": "lax",
        "COOKIE_SECURE": True,
        "COOKIE_SECURE_VALUE_VALID": True,
        "EMAIL_BACKEND": "console",
        "SMTP_TIMEOUT_SECONDS": 10,
        "SMTP_PORT": 587,
        "SMTP_HOST": "",
        "SMTP_USERNAME": "",
        "SMTP_PASSWORD": "",
        "SMTP_FROM_EMAIL": "",
    }
    for name, default in defaults.items():
        monkeypatch.setattr("app.main." + name, default)
    monkeypatch.setattr("app.main." + setting, value)

    expected_setting = setting.replace("_VALUE_VALID", "")
    with pytest.raises(RuntimeError, match=expected_setting):
        validate_configuration()


def test_unique_index_setup_is_idempotent(client):
    ensure_indexes()


def test_cross_site_cookie_requires_secure_flag(monkeypatch):
    monkeypatch.setattr("app.main.COOKIE_SAMESITE", "none")
    monkeypatch.setattr("app.main.COOKIE_SECURE", False)

    with pytest.raises(RuntimeError, match="COOKIE_SECURE"):
        validate_configuration()


def test_smtp_backend_requires_credentials(monkeypatch):
    monkeypatch.setattr("app.main.EMAIL_BACKEND", "smtp")
    monkeypatch.setattr("app.main.SMTP_HOST", "")
    monkeypatch.setattr("app.main.SMTP_USERNAME", "")
    monkeypatch.setattr("app.main.SMTP_PASSWORD", "")
    monkeypatch.setattr("app.main.SMTP_FROM_EMAIL", "")

    with pytest.raises(RuntimeError, match="SMTP_"):
        validate_configuration()


@pytest.mark.skipif(
    not os.getenv("MONGODB_INTEGRATION_URI"),
    reason="Set MONGODB_INTEGRATION_URI to run MongoDB transaction integration.",
)
def test_database_transaction_rolls_back_on_replica_set(monkeypatch):
    integration_client = MongoClient(
        os.environ["MONGODB_INTEGRATION_URI"],
        serverSelectionTimeoutMS=5000,
    )
    test_database_name = f"skillbridge_transaction_test_{uuid.uuid4().hex}"
    test_database = integration_client[test_database_name]

    try:
        monkeypatch.setattr(mongodb, "client", integration_client)
        with pytest.raises(RuntimeError, match="force rollback"):
            with database_transaction() as session:
                test_database.transaction_probe.insert_one(
                    {"probe": "rollback"},
                    session=session,
                )
                raise RuntimeError("force rollback")

        assert test_database.transaction_probe.count_documents({}) == 0
    finally:
        integration_client.drop_database(test_database_name)
        integration_client.close()


def test_roadmap_unique_index_excludes_unowned_legacy_records(client):
    index = db.roadmaps.index_information()["user_email_1"]
    assert index["partialFilterExpression"] == {
        "user_email": {"$type": "string"}
    }


def test_login_rate_limit_index_expires_old_buckets(client):
    index = db.login_rate_limits.index_information()["expires_at_1"]
    assert index["expireAfterSeconds"] == 0


def test_otp_rate_limit_index_expires_old_buckets(client):
    index = db.otp_rate_limits.index_information()["expires_at_1"]
    assert index["expireAfterSeconds"] == 0


@pytest.mark.parametrize(
    "collection_name",
    ["email_otps", "password_reset_tokens", "ai_rate_limits"],
)
def test_expiring_records_have_ttl_indexes(client, collection_name):
    index = db[collection_name].index_information()["expires_at_1"]
    assert index["expireAfterSeconds"] == 0