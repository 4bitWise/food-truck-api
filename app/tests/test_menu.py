import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

#POST /menu

@pytest.fixture(scope="module")
def setup_database():
    # Add sample options to the mock database before tests
    client.post("/options/", json={"name": "Cheese", "price": 1.5})
    client.post("/options/", json={"name": "Bacon", "price": 2.0})
    yield
    # Clean up the database after tests
    client.delete("/options/Cheese")
    client.delete("/options/Bacon")

def test_create_menu_item(setup_database):
    menu_item_data = {
        "name": "Burger",
        "description": "Delicious burger",
        "price": 5.0,
        "options": ["Cheese", "Bacon"]
    }
    response = client.post("/menu/", json=menu_item_data)
    assert response.status_code == 200
    assert response.json()["name"] == "Burger"
    assert "id" in response.json()

def test_create_menu_item_with_invalid_option(setup_database):
    menu_item_data = {
        "name": "Burger",
        "description": "Delicious burger",
        "price": 5.0,
        "options": ["NonExistentOption"]
    }
    response = client.post("/menu/", json=menu_item_data)
    assert response.status_code == 400
    assert "Option(s) not found" in response.json()["detail"]


#PUT /menu/{menu_item_id}
def test_update_menu_item(setup_database):
    # First, create a menu item
    menu_item_data = {
        "name": "Burger",
        "description": "Delicious burger",
        "price": 5.0,
        "options": ["Cheese"]
    }
    create_response = client.post("/menu/", json=menu_item_data)
    menu_item_id = create_response.json()["id"]

    # Now, update the menu item
    update_data = {"name": "Veggie Burger", "price": 6.0}
    response = client.put(f"/menu/{menu_item_id}", json=update_data)
    assert response.status_code == 200
    assert response.json()["name"] == "Veggie Burger"
    assert response.json()["price"] == 6.0

def test_update_menu_item_with_invalid_option(setup_database):
    # First, create a menu item
    menu_item_data = {
        "name": "Burger",
        "description": "Delicious burger",
        "price": 5.0,
        "options": ["Cheese"]
    }
    create_response = client.post("/menu/", json=menu_item_data)
    menu_item_id = create_response.json()["id"]

    # Update the menu item with an invalid option
    update_data = {"options": ["NonExistentOption"]}
    response = client.put(f"/menu/{menu_item_id}", json=update_data)
    assert response.status_code == 400
    assert "Option(s) not found" in response.json()["detail"]


# GET /menu 
def test_get_menu_items(setup_database):
    menu_item_data = {
        "name": "Burger",
        "description": "Delicious burger",
        "price": 5.0,
        "options": ["Cheese"]
    }
    client.post("/menu/", json=menu_item_data)
    response = client.get("/menu/")
    assert response.status_code == 200
    assert len(response.json()) > 0


# DELETE /menu/{menu_item_id}
def test_delete_menu_item(setup_database):
    menu_item_data = {
        "name": "Burger",
        "description": "Delicious burger",
        "price": 5.0,
        "options": ["Cheese"]
    }
    create_response = client.post("/menu/", json=menu_item_data)
    menu_item_id = create_response.json()["id"]

    delete_response = client.delete(f"/menu/{menu_item_id}")
    assert delete_response.status_code == 200
    assert delete_response.json()["message"] == "Menu item deleted successfully"

