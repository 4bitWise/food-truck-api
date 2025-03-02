import sys
import os
import pytest
from fastapi.testclient import TestClient
from bson import ObjectId
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from main import app
from database import get_database


# Mock data
MOCK_MENU_ITEM_ID = str(ObjectId())
MOCK_MENU_ITEM = {
    "_id": ObjectId(MOCK_MENU_ITEM_ID),
    "name": "Test Burger",
    "description": "A delicious test burger",
    "price": 10.99,
    "options": ["Cheese", "Bacon"],
    "category": "Burgers",
    "image_url": "https://example.com/burger.jpg"
}

@pytest.fixture
def mock_db():
    # Create mock collections
    mock_menu = MagicMock()
    mock_options = MagicMock()

    # Configure mock menu collection
    mock_menu.find.return_value = [MOCK_MENU_ITEM]
    mock_menu.find_one.return_value = MOCK_MENU_ITEM
    mock_menu.insert_one.return_value.inserted_id = ObjectId(MOCK_MENU_ITEM_ID)

    # Create mock database
    mock_db = MagicMock()
    mock_db.__getitem__.side_effect = {
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

@pytest.fixture(scope="module")
def setup_database():
    """Set up sample options in the mock database before tests."""
    cheese_response = client.post("/options/", json={"name": "Cheese", "price": 1.5})
    bacon_response = client.post("/options/", json={"name": "Bacon", "price": 2.0})

    assert cheese_response.status_code == 200
    assert bacon_response.status_code == 200

    cheese_id = cheese_response.json()["id"]
    bacon_id = bacon_response.json()["id"]

    yield {"cheese_id": cheese_id, "bacon_id": bacon_id}

    # Cleanup (use actual option IDs)
    client.delete(f"/options/{cheese_id}")
    client.delete(f"/options/{bacon_id}")

@pytest.fixture(autouse=True)
def cleanup_database():
    """Clean up the database after each test."""
    yield
    # Clean up all menu items
    menu_items = client.get("/menu/").json()
    for item in menu_items:
        client.delete(f"/menu/{item['id']}")


# POST /menu
def test_create_menu_item(setup_database):
    menu_item_data = {
        "name": "Burger",
        "description": "Delicious burger",
        "price": 5.0,
        "options": ["Cheese", "Bacon"],
    }
    
    response = client.post("/menu/", json=menu_item_data)

    print(response.json())
    assert response.status_code == 200
    assert response.json()["name"] == "Burger"
    assert "id" in response.json()


def test_create_menu_item_with_invalid_option():
    menu_item_data = {
        "name": "Hamburger",
        "description": "Delicious Hamburger",
        "price": 5.0,
        "options": ["NonExistentOption"],
    }
    response = client.post("/menu/", json=menu_item_data)

    assert response.status_code == 400
    assert "Option(s) not found" in response.json()["detail"]


# PUT /menu/{menu_item_id}
def test_update_menu_item(setup_database):
    """First, create a menu item, then update it."""
    menu_item_data = {
        "name": "Double Burger",
        "description": "Delicious double burger",
        "price": 5.0,
        "options": ["Cheese"],
    }
    create_response = client.post("/menu/", json=menu_item_data)
    menu_item_id = create_response.json()["id"]

    update_data = {"name": "Veggie Burger", "price": 6.0}
    response = client.put(f"/menu/{menu_item_id}", json=update_data)

    assert response.status_code == 200
    assert response.json()["name"] == "Veggie Burger"
    assert response.json()["price"] == 6.0


def test_update_menu_item_with_invalid_option(setup_database):
    """Try to update a menu item with a nonexistent option."""
    menu_item_data = {
        "name": "Double Burger",
        "description": "Delicious double burger",
        "price": 5.0,
        "options": ["Cheese"],
    }
    create_response = client.post("/menu/", json=menu_item_data)
    menu_item_id = create_response.json()["id"]

    update_data = {"options": ["NonExistentOption"]}
    response = client.put(f"/menu/{menu_item_id}", json=update_data)

    assert response.status_code == 400
    assert "Option(s) not found" in response.json()["detail"]


# GET /menu
def test_get_menu_items(setup_database):
    """Create a menu item and verify that it is returned."""
    menu_item_data = {
        "name": "Purple Burger",
        "description": "Delicious purple burger",
        "price": 5.0,
        "options": ["Cheese"],
    }
    client.post("/menu/", json=menu_item_data)

    response = client.get("/menu/")
    assert response.status_code == 200
    assert len(response.json()) > 0


# DELETE /menu/{menu_item_id}
def test_delete_menu_item(setup_database):
    """Create a menu item and delete it."""
    menu_item_data = {
        "name": "Blue Burger",
        "description": "Delicious blue burger",
        "price": 5.0,
        "options": ["Cheese"],
    }
    create_response = client.post("/menu/", json=menu_item_data)
    menu_item_id = create_response.json()["id"]

    delete_response = client.delete(f"/menu/{menu_item_id}")

    assert delete_response.status_code == 200
    assert delete_response.json()["message"] == "Menu item deleted successfully"

def test_get_menu_items_success(client, mock_db):
    # Make request
    response = client.get("/menu")

    # Assertions
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Test Burger"
    assert response.json()[0]["price"] == 10.99

def test_get_menu_item_by_id_success(client, mock_db):
    # Make request
    response = client.get(f"/menu/{MOCK_MENU_ITEM_ID}")

    # Assertions
    assert response.status_code == 200
    assert response.json()["name"] == "Test Burger"
    assert response.json()["price"] == 10.99
    assert response.json()["options"] == ["Cheese", "Bacon"]

def test_get_menu_item_by_id_not_found(client, mock_db):
    # Configure mock to return None for non-existent item
    mock_db["menu"].find_one.return_value = None

    # Make request
    response = client.get(f"/menu/{str(ObjectId())}")

    # Assertions
    assert response.status_code == 404
    assert response.json()["detail"] == "Menu item not found"

def test_create_menu_item_success(client, mock_db):
    # Test data
    new_item = {
        "name": "New Burger",
        "description": "A new delicious burger",
        "price": 12.99,
        "options": ["Cheese", "Bacon"],
        "category": "Burgers",
        "image_url": "https://example.com/new-burger.jpg"
    }

    # Configure mock for unique name check
    mock_db["menu"].find_one.return_value = None

    # Make request
    response = client.post("/menu", json=new_item)

    # Assertions
    assert response.status_code == 200
    assert response.json()["name"] == "New Burger"
    assert response.json()["price"] == 12.99
    assert "id" in response.json()

def test_create_menu_item_duplicate_name(client, mock_db):
    # Test data
    new_item = {
        "name": "Test Burger",  # Same name as existing item
        "description": "A new delicious burger",
        "price": 12.99,
        "options": ["Cheese", "Bacon"],
        "category": "Burgers",
        "image_url": "https://example.com/new-burger.jpg"
    }

    # Configure mock to return existing item for name check
    mock_db["menu"].find_one.return_value = MOCK_MENU_ITEM

    # Make request
    response = client.post("/menu", json=new_item)

    # Assertions
    assert response.status_code == 400
    assert "Menu item name must be unique" in response.json()["detail"]

def test_update_menu_item_success(client, mock_db):
    # Test data
    update_data = {
        "price": 13.99,
        "description": "Updated description"
    }

    # Configure mock for update
    updated_item = {**MOCK_MENU_ITEM, "price": 13.99, "description": "Updated description"}
    mock_db["menu"].find_one_and_update.return_value = updated_item

    # Make request
    response = client.put(f"/menu/{MOCK_MENU_ITEM_ID}", json=update_data)

    # Assertions
    assert response.status_code == 200
    assert response.json()["price"] == 13.99
    assert response.json()["description"] == "Updated description"

def test_update_menu_item_not_found(client, mock_db):
    # Configure mock to return None for update
    mock_db["menu"].find_one_and_update.return_value = None

    # Make request
    response = client.put(
        f"/menu/{str(ObjectId())}", 
        json={"price": 13.99}
    )

    # Assertions
    assert response.status_code == 404
    assert response.json()["detail"] == "Menu not found"

def test_delete_menu_item_success(client, mock_db):
    # Configure mock for successful deletion
    mock_db["menu"].delete_one.return_value.deleted_count = 1

    # Make request
    response = client.delete(f"/menu/{MOCK_MENU_ITEM_ID}")

    # Assertions
    assert response.status_code == 200
    assert response.json()["message"] == "Menu item deleted successfully"

def test_delete_menu_item_not_found(client, mock_db):
    # Configure mock for unsuccessful deletion
    mock_db["menu"].delete_one.return_value.deleted_count = 0

    # Make request
    response = client.delete(f"/menu/{str(ObjectId())}")

    # Assertions
    assert response.status_code == 404
    assert response.json()["detail"] == "Menu item not found"
