import pytest
from fastapi.testclient import TestClient
from bson import ObjectId
from datetime import datetime
from main import app
from database import get_collections
from schemas.option import OptionCreate, OptionUpdate
from pymongo.errors import DuplicateKeyError

# Mock data
mock_option_1 = {
    "_id": ObjectId(),
    "name": "Extra Cheese",
    "price": 1.5
}

mock_option_2 = {
    "_id": ObjectId(),
    "name": "Bacon",
    "price": 2.0
}

# Mock Collection class
class MockCollection:
    def __init__(self, data=None):
        self.data = data or []

    def find(self):
        return self.data

    def find_one(self, query):
        if "_id" in query:
            return next((item for item in self.data if item["_id"] == query["_id"]), None)
        if "name" in query:
            return next((item for item in self.data if item["name"] == query["name"]), None)
        return None

    def insert_one(self, document):
        # Check for duplicate names
        if any(item["name"] == document["name"] for item in self.data):
            raise DuplicateKeyError("Duplicate key error")
        document["_id"] = ObjectId()
        self.data.append(document)
        return type("InsertOneResult", (), {"inserted_id": document["_id"]})

    def find_one_and_update(self, query, update, return_document=None):
        item = self.find_one(query)
        if item:
            # Check for duplicate names when updating
            new_name = update["$set"].get("name")
            if new_name and any(i["name"] == new_name and i["_id"] != item["_id"] for i in self.data):
                raise DuplicateKeyError("Duplicate key error")
            item.update(update["$set"])
            return item
        return None

    def delete_one(self, query):
        initial_length = len(self.data)
        self.data = [item for item in self.data if item["_id"] != query["_id"]]
        return type("DeleteResult", (), {"deleted_count": initial_length - len(self.data)})

# Mock database dependency
def mock_get_collections():
    return {
        "options": MockCollection([mock_option_1.copy(), mock_option_2.copy()]),
        "menu": MockCollection([])  # Empty menu collection for delete validation
    }

# Setup test client
@pytest.fixture
def client():
    app.dependency_overrides[get_collections] = mock_get_collections
    return TestClient(app)

# Test cases
def test_get_options(client):
    response = client.get("/options/")
    assert response.status_code == 200
    options = response.json()
    assert len(options) == 2
    assert options[0]["name"] == "Extra Cheese"
    assert options[1]["name"] == "Bacon"

def test_get_option_by_id(client):
    option_id = str(mock_option_1["_id"])
    response = client.get(f"/options/{option_id}")
    assert response.status_code == 200
    option = response.json()
    assert option["name"] == "Extra Cheese"
    assert option["price"] == 1.5

def test_get_option_not_found(client):
    response = client.get(f"/options/{str(ObjectId())}")
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid option ID"

def test_create_option(client):
    new_option = {
        "name": "Spicy Sauce",
        "price": 0.75
    }
    response = client.post("/options/", json=new_option)
    assert response.status_code == 200
    created_option = response.json()
    assert created_option["name"] == "Spicy Sauce"
    assert created_option["price"] == 0.75
    assert "id" in created_option

def test_create_duplicate_option(client):
    duplicate_option = {
        "name": "Extra Cheese",
        "price": 1.5
    }
    response = client.post("/options/", json=duplicate_option)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]

def test_update_option(client):
    option_id = str(mock_option_1["_id"])
    update_data = {
        "price": 2.0
    }
    response = client.put(f"/options/{option_id}", json=update_data)
    assert response.status_code == 200
    updated_option = response.json()
    assert updated_option["price"] == 2.0
    assert updated_option["name"] == "Extra Cheese"  # Name should remain unchanged

def test_update_option_not_found(client):
    response = client.put(
        f"/options/{str(ObjectId())}", 
        json={"price": 2.0}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid option ID"

def test_update_option_duplicate_name(client):
    option_id = str(mock_option_1["_id"])
    update_data = {
        "name": "Bacon"  # Trying to update to an existing name
    }
    response = client.put(f"/options/{option_id}", json=update_data)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]

def test_delete_option(client):
    option_id = str(mock_option_1["_id"])
    response = client.delete(f"/options/{option_id}")
    assert response.status_code == 200
    assert response.json()["message"] == "Option deleted successfully"

def test_delete_option_not_found(client):
    response = client.delete(f"/options/{str(ObjectId())}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Option not found"
