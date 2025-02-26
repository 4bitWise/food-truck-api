import pytest
from fastapi.testclient import TestClient
from bson import ObjectId
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from main import app

client = TestClient(app)

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
