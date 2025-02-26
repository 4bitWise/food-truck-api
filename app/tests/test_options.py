import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.fixture(autouse=True)
def cleanup_database():
    """Clean up the database after each test."""
    yield
    # Clean up all menu items
    options = client.get("/options").json()
    for opt in options:
        client.delete(f"/options/{opt['id']}")

# POST /options
def test_create_option():
    option_data = {
        "name": "Cheese",
        "price": 1.5
    }
    response = client.post("/options/", json=option_data)
    assert response.status_code == 200
    assert response.json()["name"] == "Cheese"
    assert "id" in response.json()

def test_create_option_with_duplicate_name():
    option_data = {
        "name": "Cheese",
        "price": 1.5
    }
    client.post("/options/", json=option_data)
    response = client.post("/options/", json=option_data)  # Trying to create again
    assert response.status_code == 400
    assert "Option name must be unique" in response.json()["detail"]


# PUT /options/{option_id}
def test_update_option():
    option_data = {
        "name": "Fries",
        "price": 1.5
    }
    create_response = client.post("/options/", json=option_data)
    option_id = create_response.json()["id"]

    update_data = {"price": 2.0}
    response = client.put(f"/options/{option_id}", json=update_data)
    print(response.json())
    assert response.status_code == 200
    assert response.json()["price"] == 2.0

# GET /options
def test_get_options():
    option_data = {
        "name": "Coca",
        "price": 1.5
    }
    client.post("/options/", json=option_data)
    response = client.get("/options/")
    assert response.status_code == 200
    assert len(response.json()) > 0

# DELETE /options/{option_id}
def test_delete_option():
    option_data = {
        "name": "Donut",
        "price": 1.5
    }
    create_response = client.post("/options/", json=option_data)
    option_id = create_response.json()["id"]

    delete_response = client.delete(f"/options/{option_id}")
    assert delete_response.status_code == 200
    assert delete_response.json()["message"] == "Option deleted successfully"
