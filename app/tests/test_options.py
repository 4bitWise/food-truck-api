import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from bson import ObjectId

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app
from database import get_database

# Mock data
MOCK_OPTION_ID = str(ObjectId())
MOCK_OPTION = {
    "_id": ObjectId(MOCK_OPTION_ID),
    "name": "Extra Cheese",
    "description": "Add extra cheese to your item",
    "price": 1.50,
    "category": "Add-ons"
}

MOCK_MENU_ITEM = {
    "_id": ObjectId(),
    "name": "Test Burger",
    "options": ["Extra Cheese"]
}

@pytest.fixture
def mock_db():
    # Create mock collections
    mock_options = MagicMock()
    mock_menu = MagicMock()

    # Configure mock options collection
    mock_options.find.return_value = [MOCK_OPTION]
    mock_options.find_one.return_value = MOCK_OPTION
    mock_options.insert_one.return_value.inserted_id = ObjectId(MOCK_OPTION_ID)

    # Configure mock menu collection
    mock_menu.find_one.return_value = None  # Default to no menu items using the option

    # Create mock database
    mock_db = MagicMock()
    mock_db.__getitem__.side_effect = {
        "options": mock_options,
        "menu": mock_menu
    }.__getitem__

    return mock_db

@pytest.fixture
def client(mock_db):
    def override_get_database():
        return mock_db

    app.dependency_overrides[get_database] = override_get_database
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

def test_get_options_success(client, mock_db):
    # Make request
    response = client.get("/options")

    # Assertions
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Extra Cheese"
    assert response.json()[0]["price"] == 1.50

def test_get_option_by_id_success(client, mock_db):
    # Make request
    response = client.get(f"/options/{MOCK_OPTION_ID}")

    # Assertions
    assert response.status_code == 200
    assert response.json()["name"] == "Extra Cheese"
    assert response.json()["price"] == 1.50
    assert response.json()["category"] == "Add-ons"

def test_get_option_by_id_not_found(client, mock_db):
    # Configure mock to return None for non-existent option
    mock_db["options"].find_one.return_value = None

    # Make request
    response = client.get(f"/options/{str(ObjectId())}")

    # Assertions
    assert response.status_code == 404
    assert response.json()["detail"] == "Option not found"

def test_create_option_success(client, mock_db):
    # Test data
    new_option = {
        "name": "Extra Bacon",
        "description": "Add extra bacon to your item",
        "price": 2.00,
        "category": "Add-ons"
    }

    # Configure mock for unique name check
    mock_db["options"].find_one.return_value = None

    # Make request
    response = client.post("/options", json=new_option)

    # Assertions
    assert response.status_code == 200
    assert response.json()["name"] == "Extra Bacon"
    assert response.json()["price"] == 2.00
    assert "id" in response.json()

def test_create_option_duplicate_name(client, mock_db):
    # Test data
    new_option = {
        "name": "Extra Cheese",  # Same name as existing option
        "description": "Add extra cheese to your item",
        "price": 1.50,
        "category": "Add-ons"
    }

    # Configure mock to return existing option for name check
    mock_db["options"].find_one.return_value = MOCK_OPTION

    # Make request
    response = client.post("/options", json=new_option)

    # Assertions
    assert response.status_code == 400
    assert "Option name must be unique" in response.json()["detail"]

def test_update_option_success(client, mock_db):
    # Test data
    update_data = {
        "price": 2.00,
        "description": "Updated description"
    }

    # Configure mock for update
    updated_option = {**MOCK_OPTION, "price": 2.00, "description": "Updated description"}
    mock_db["options"].find_one_and_update.return_value = updated_option

    # Make request
    response = client.put(f"/options/{MOCK_OPTION_ID}", json=update_data)

    # Assertions
    assert response.status_code == 200
    assert response.json()["price"] == 2.00
    assert response.json()["description"] == "Updated description"

def test_update_option_not_found(client, mock_db):
    # Configure mock to return None for update
    mock_db["options"].find_one_and_update.return_value = None

    # Make request
    response = client.put(
        f"/options/{str(ObjectId())}", 
        json={"price": 2.00}
    )

    # Assertions
    assert response.status_code == 404
    assert response.json()["detail"] == "Option not found"

def test_delete_option_success(client, mock_db):
    # Configure mock for successful deletion
    mock_db["menu"].find_one.return_value = None  # No menu items using the option
    mock_db["options"].delete_one.return_value.deleted_count = 1

    # Make request
    response = client.delete(f"/options/{MOCK_OPTION_ID}")

    # Assertions
    assert response.status_code == 200
    assert response.json()["message"] == "Option deleted successfully"

def test_delete_option_not_found(client, mock_db):
    # Configure mock for unsuccessful deletion
    mock_db["options"].find_one.return_value = None

    # Make request
    response = client.delete(f"/options/{str(ObjectId())}")

    # Assertions
    assert response.status_code == 404
    assert response.json()["detail"] == "Option not found"

def test_delete_option_in_use(client, mock_db):
    # Configure mock to show option is in use
    mock_db["menu"].find_one.return_value = MOCK_MENU_ITEM

    # Make request
    response = client.delete(f"/options/{MOCK_OPTION_ID}")

    # Assertions
    assert response.status_code == 400
    assert "Cannot delete option as it is being used in menu items" in response.json()["detail"]
