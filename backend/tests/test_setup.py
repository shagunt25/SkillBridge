import uuid

import pytest
from pymongo.errors import DuplicateKeyError

from app.database.mongodb import db, ensure_indexes


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


def test_unique_index_setup_is_idempotent(client):
    ensure_indexes()


def test_roadmap_unique_index_excludes_unowned_legacy_records(client):
    index = db.roadmaps.index_information()["user_email_1"]
    assert index["partialFilterExpression"] == {
        "user_email": {"$type": "string"}
    }