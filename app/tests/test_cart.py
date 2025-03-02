from datetime import datetime, UTC
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
MOCK_MENU_ITEM_ID = str(ObjectId())
MOCK_MENU_ITEM = {
    "_id": ObjectId(MOCK_MENU_ITEM_ID),
    "name": "Test Item",
    "price": 10.0,
    "description": "Test Description",
    "options": ["Option1", "Option2"]
}

MOCK_CART_ID = str(ObjectId())
MOCK_CART = {
    "_id": ObjectId(MOCK_CART_ID),
    "items": [
        {
            "menu_item_id": MOCK_MENU_ITEM_ID,
            "quantity": 2,
            "selected_options": ["Option1"],
            "special_instructions": "Test instructions"
        }
    ]
}

@pytest.fixture
def mock_db():
    # Create mock collections
    mock_carts = MagicMock()
    mock_menu = MagicMock()
    mock_options = MagicMock()

    # Configure mock menu collection
    mock_menu.find_one.return_value = MOCK_MENU_ITEM

    # Configure mock carts collection
    mock_carts.find_one.return_value = MOCK_CART
    mock_carts.insert_one.return_value.inserted_id = ObjectId(MOCK_CART_ID)

    # Create mock database
    mock_db = MagicMock()
    mock_db.__getitem__.side_effect = {
        "carts": mock_carts,
        "menu": mock_menu,
        "options": mock_options
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

def test_add_to_cart_success(client, mock_db):
    # Test data
    cart_item = {
        "menu_item_id": MOCK_MENU_ITEM_ID,
        "quantity": 2,
        "selected_options": ["Option1"],
        "special_instructions": "Test instructions"
    }

    # Make request
    response = client.post("/cart/items", json=cart_item)

    # Assertions
    assert response.status_code == 200
    assert response.json()["items"][0]["menu_item_id"] == MOCK_MENU_ITEM_ID
    assert response.json()["items"][0]["quantity"] == 2
    assert response.json()["items"][0]["selected_options"] == ["Option1"]

def test_add_to_cart_invalid_menu_item(client, mock_db):
    # Configure mock to return None for invalid menu item
    mock_db["menu"].find_one.return_value = None

    # Test data
    cart_item = {
        "menu_item_id": str(ObjectId()),
        "quantity": 1,
        "selected_options": []
    }

    # Make request
    response = client.post("/cart/items", json=cart_item)

    # Assertions
    assert response.status_code == 404
    assert "Menu item not found" in response.json()["detail"]

def test_add_to_cart_invalid_option(client, mock_db):
    # Test data with invalid option
    cart_item = {
        "menu_item_id": MOCK_MENU_ITEM_ID,
        "quantity": 1,
        "selected_options": ["InvalidOption"]
    }

    # Make request
    response = client.post("/cart/items", json=cart_item)

    # Assertions
    assert response.status_code == 400
    assert "Invalid options" in response.json()["detail"]

def test_update_cart_item_success(client, mock_db):
    # Test data
    update_data = {
        "quantity": 3,
        "selected_options": ["Option2"],
        "special_instructions": "Updated instructions"
    }

    # Make request
    response = client.put(f"/cart/items/{MOCK_MENU_ITEM_ID}", json=update_data)

    # Assertions
    assert response.status_code == 200
    assert response.json()["items"][0]["quantity"] == 3
    assert response.json()["items"][0]["selected_options"] == ["Option2"]
    assert response.json()["items"][0]["special_instructions"] == "Updated instructions"

def test_remove_from_cart_success(client, mock_db):
    # Make request
    response = client.delete(f"/cart/items/{MOCK_MENU_ITEM_ID}")

    # Assertions
    assert response.status_code == 200
    assert response.json()["message"] == "Item removed from cart"

def test_clear_cart_success(client, mock_db):
    # Make request
    response = client.delete("/cart")

    # Assertions
    assert response.status_code == 200
    assert response.json()["message"] == "Cart cleared successfully"

def test_get_cart_success(client, mock_db):
    # Make request
    response = client.get("/cart")

    # Assertions
    assert response.status_code == 200
    assert response.json()["items"][0]["menu_item_id"] == MOCK_MENU_ITEM_ID
    assert response.json()["items"][0]["quantity"] == 2
    assert response.json()["items"][0]["selected_options"] == ["Option1"] 