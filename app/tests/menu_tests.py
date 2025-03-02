import pytest
from fastapi.testclient import TestClient
from bson import ObjectId
from datetime import datetime
from pymongo.errors import DuplicateKeyError
from main import app
from database import get_collections
from schemas.menu import MenuItemCreate, MenuItemUpdate

# Mock data
mock_menu_item_1 = {
    "_id": ObjectId(),
    "name": "Margherita Pizza",
    "description": "Classic pizza with tomato sauce and mozzarella",
    "price": 12.99,
    "category": "Pizza",
    "options": ["Extra Cheese", "Bacon"],
    "available": True
}

mock_menu_item_2 = {
    "_id": ObjectId(),
    "name": "Pepperoni Pizza",
    "description": "Pizza with tomato sauce, mozzarella, and pepperoni",
    "price": 14.99,
    "category": "Pizza",
    "options": ["Extra Cheese"],
    "available": True
}

mock_options = [
    {
        "_id": ObjectId(),
        "name": "Extra Cheese",
        "price": 1.5
    },
    {
        "_id": ObjectId(),
        "name": "Bacon",
        "price": 2.0
    }
]

# Mock Collection class
class MockCollection:
    def __init__(self, data=None):
        self.data = data or []

    def find(self, query=None):
        if query and "name" in query and "$in" in query["name"]:
            # Handle options query for validation
            valid_names = set(query["name"]["$in"])
            return [item for item in self.data if item["name"] in valid_names]
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
        "menu": MockCollection([mock_menu_item_1.copy(), mock_menu_item_2.copy()]),
        "options": MockCollection(mock_options)  # Include mock options for validation
    }

# Setup test client
@pytest.fixture
def client():
    app.dependency_overrides[get_collections] = mock_get_collections
    return TestClient(app)

# Test cases
def test_get_menu_items(client):
    response = client.get("/menu/")
    assert response.status_code == 200
    menu_items = response.json()
    assert len(menu_items) == 2
    assert menu_items[0]["name"] == "Margherita Pizza"
    assert menu_items[1]["name"] == "Pepperoni Pizza"

def test_get_menu_item_by_id(client):
    menu_item_id = str(mock_menu_item_1["_id"])
    response = client.get(f"/menu/{menu_item_id}")
    assert response.status_code == 200
    menu_item = response.json()
    assert menu_item["name"] == "Margherita Pizza"
    assert menu_item["price"] == 12.99
    assert "Extra Cheese" in menu_item["options"]

def test_get_menu_item_not_found(client):
    response = client.get(f"/menu/{str(ObjectId())}")
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid menu item ID"

def test_create_menu_item(client):
    new_menu_item = {
        "name": "Vegetarian Pizza",
        "description": "Pizza with assorted vegetables",
        "price": 13.99,
        "category": "Pizza",
        "options": ["Extra Cheese"],
        "available": True
    }
    response = client.post("/menu/", json=new_menu_item)
    assert response.status_code == 200
    created_item = response.json()
    assert created_item["name"] == "Vegetarian Pizza"
    assert created_item["price"] == 13.99
    assert "id" in created_item

def test_create_menu_item_with_invalid_option(client):
    new_menu_item = {
        "name": "Invalid Pizza",
        "description": "Pizza with invalid option",
        "price": 13.99,
        "category": "Pizza",
        "options": ["Invalid Option"],
        "available": True
    }
    response = client.post("/menu/", json=new_menu_item)
    assert response.status_code == 400
    assert "Option(s) not found" in response.json()["detail"]

def test_create_duplicate_menu_item(client):
    duplicate_item = {
        "name": "Margherita Pizza",
        "description": "Duplicate pizza",
        "price": 13.99,
        "category": "Pizza",
        "options": ["Extra Cheese"],
        "available": True
    }
    response = client.post("/menu/", json=duplicate_item)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]

def test_update_menu_item(client):
    menu_item_id = str(mock_menu_item_1["_id"])
    update_data = {
        "price": 15.99,
        "description": "Updated description"
    }
    response = client.put(f"/menu/{menu_item_id}", json=update_data)
    assert response.status_code == 200
    updated_item = response.json()
    assert updated_item["price"] == 15.99
    assert updated_item["description"] == "Updated description"
    assert updated_item["name"] == "Margherita Pizza"  # Name should remain unchanged

def test_update_menu_item_with_invalid_option(client):
    menu_item_id = str(mock_menu_item_1["_id"])
    update_data = {
        "options": ["Invalid Option"]
    }
    response = client.put(f"/menu/{menu_item_id}", json=update_data)
    assert response.status_code == 400
    assert "Option(s) not found" in response.json()["detail"]

def test_update_menu_item_not_found(client):
    response = client.put(
        f"/menu/{str(ObjectId())}", 
        json={"price": 15.99}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid menu item ID"

def test_update_menu_item_duplicate_name(client):
    menu_item_id = str(mock_menu_item_1["_id"])
    update_data = {
        "name": "Pepperoni Pizza"  # Trying to update to an existing name
    }
    response = client.put(f"/menu/{menu_item_id}", json=update_data)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]

def test_delete_menu_item(client):
    menu_item_id = str(mock_menu_item_1["_id"])
    response = client.delete(f"/menu/{menu_item_id}")
    assert response.status_code == 200
    assert response.json()["message"] == "Menu item deleted successfully"

def test_delete_menu_item_not_found(client):
    response = client.delete(f"/menu/{str(ObjectId())}")
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid menu item ID" 