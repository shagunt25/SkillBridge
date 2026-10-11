import pytest
import mongomock
from fastapi.testclient import TestClient

# 1. Import your database module FIRST
import app.database.mongodb as mongodb

# 2. Create the mock in-memory database
mock_client = mongomock.MongoClient()
mock_db = mock_client["skillbridge_test"]

# 3. Overwrite the global variables in your mongodb.py file
mongodb.client = mock_client
mongodb.db = mock_db

# 4. NOW import your main app. 
# Any route that imports 'db' will now silently get the mock_db instead of the real one.
from app.main import app 

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c