from app.database.mongodb import db

def test_database_is_mocked(client):
    # This verifies that the app is using the fake database, not Sanya's real one
    assert db.name == "skillbridge_test"