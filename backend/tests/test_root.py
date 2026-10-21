def test_read_root(client):
    """Verify that GET / returns a 200 OK and expected response payload."""
    response = client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, dict)
    # Check that a standard message or status key exists
    assert "message" in data or "status" in data


def test_read_root_method_not_allowed(client):
    """Verify that sending a POST request to GET / returns 405 Method Not Allowed."""
    response = client.post("/")
    assert response.status_code == 405