import pytest
from fastapi.testclient import TestClient
from bson import ObjectId
from datetime import datetime, UTC
from main import app
from database import get_collections
from schemas.cart import CartItem

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
    "available": False  # This item is not available
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

mock_cart = {
    "_id": ObjectId(),
    "items": [
        {
            "menu_item_id": str(mock_menu_item_1["_id"]),
            "quantity": 2,
            "selected_options": ["Extra Cheese"],
            "special_instructions": "Extra crispy",
            "total_price": 14.49  # Base price (12.99) + Extra Cheese (1.50)
        }
    ],
    "total_amount": 28.98,  # total_price * quantity = 14.49 * 2
    "created_at": datetime.now(UTC),
    "updated_at": datetime.now(UTC)
}

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

    def find_one(self, query=None, sort=None):
        if not self.data:
            return None

        if sort:
            # Handle sorting (e.g., for getting latest cart)
            return self.data[-1]

        if query and "_id" in query:
            return next((item for item in self.data if item["_id"] == query["_id"]), None)
        return self.data[0]

    def insert_one(self, document):
        document["_id"] = ObjectId()
        # Calculate total_amount for cart
        if "items" in document:
            total = 0
            for item in document["items"]:
                menu_item = next(
                    (m for m in mock_get_collections()["menu"].data 
                     if str(m["_id"]) == item["menu_item_id"]),
                    None
                )
                if menu_item:
                    options = [
                        opt for opt in mock_get_collections()["options"].data
                        if opt["name"] in item["selected_options"]
                    ]
                    base_price = menu_item["price"]
                    options_total = sum(opt["price"] for opt in options)
                    item_total = base_price + options_total
                    item["total_price"] = item_total
                    total += item_total * item["quantity"]
            document["total_amount"] = total
        self.data.append(document)
        return type("InsertOneResult", (), {"inserted_id": document["_id"]})

    def find_one_and_update(self, query, update, return_document=None):
        item = self.find_one(query)
        if item:
            if "$set" in update:
                # Calculate total_amount for cart
                if "items" in update["$set"]:
                    total = 0
                    for cart_item in update["$set"]["items"]:
                        menu_item = next(
                            (m for m in mock_get_collections()["menu"].data 
                             if str(m["_id"]) == cart_item["menu_item_id"]),
                            None
                        )
                        if menu_item:
                            options = [
                                opt for opt in mock_get_collections()["options"].data
                                if opt["name"] in cart_item["selected_options"]
                            ]
                            base_price = menu_item["price"]
                            options_total = sum(opt["price"] for opt in options)
                            item_total = base_price + options_total
                            cart_item["total_price"] = item_total
                            total += item_total * cart_item["quantity"]
                    update["$set"]["total_amount"] = total
                item.update(update["$set"])
                # Update the item in self.data
                for i, data_item in enumerate(self.data):
                    if data_item["_id"] == item["_id"]:
                        self.data[i] = item
                        break
            return item
        return None

    def delete_one(self, query):
        initial_length = len(self.data)
        item_to_delete = None
        for i, item in enumerate(self.data):
            if item["_id"] == query["_id"]:
                item_to_delete = self.data.pop(i)
                break
        return type("DeleteResult", (), {"deleted_count": 1 if item_to_delete else 0})

# Mock database dependency
def mock_get_collections():
    return {
        "menu": MockCollection([mock_menu_item_1.copy(), mock_menu_item_2.copy()]),
        "options": MockCollection(mock_options),
        "carts": MockCollection([mock_cart.copy()])
    }

# Setup test client
@pytest.fixture
def client():
    app.dependency_overrides[get_collections] = mock_get_collections
    return TestClient(app)

# Test cases
def test_get_cart(client):
    response = client.get("/cart/")
    assert response.status_code == 200
    cart = response.json()
    assert len(cart["items"]) == 1
    assert cart["total_amount"] == pytest.approx(28.98, rel=1e-9)
    assert cart["items"][0]["menu_item_id"] == str(mock_menu_item_1["_id"])

def test_get_cart_not_found(client):
    # Override mock to return empty cart collection
    app.dependency_overrides[get_collections] = lambda: {
        "menu": MockCollection([mock_menu_item_1.copy()]),
        "options": MockCollection(mock_options),
        "carts": MockCollection([])
    }
    response = client.get("/cart/")
    assert response.status_code == 404
    assert response.json()["detail"] == "Cart not found"

def test_add_to_cart_new_cart(client):
    # Override mock to return empty cart collection
    app.dependency_overrides[get_collections] = lambda: {
        "menu": MockCollection([mock_menu_item_1.copy()]),
        "options": MockCollection(mock_options),
        "carts": MockCollection([])
    }
    
    new_item = {
        "menu_item_id": str(mock_menu_item_1["_id"]),
        "quantity": 1,
        "selected_options": ["Extra Cheese"],
        "special_instructions": "Extra crispy"
    }
    response = client.post("/cart/items", json=new_item)
    assert response.status_code == 200
    cart = response.json()
    assert len(cart["items"]) == 1
    assert cart["items"][0]["quantity"] == 1
    assert cart["total_amount"] == pytest.approx(14.49, rel=1e-9)  # 12.99 + 1.50

def test_add_to_cart_existing_cart(client):
    new_item = {
        "menu_item_id": str(mock_menu_item_1["_id"]),
        "quantity": 1,
        "selected_options": ["Bacon"],
        "special_instructions": "Well done"
    }
    response = client.post("/cart/items", json=new_item)
    assert response.status_code == 200
    cart = response.json()
    assert len(cart["items"]) == 2
    assert cart["total_amount"] == pytest.approx(43.97, rel=1e-9)  # 28.98 + (12.99 + 2.00)

def test_add_unavailable_item_to_cart(client):
    new_item = {
        "menu_item_id": str(mock_menu_item_2["_id"]),  # Unavailable item
        "quantity": 1,
        "selected_options": ["Extra Cheese"],
        "special_instructions": ""
    }
    response = client.post("/cart/items", json=new_item)
    assert response.status_code == 400
    assert "not available" in response.json()["detail"]

def test_add_item_with_invalid_option(client):
    new_item = {
        "menu_item_id": str(mock_menu_item_1["_id"]),
        "quantity": 1,
        "selected_options": ["Invalid Option"],
        "special_instructions": ""
    }
    response = client.post("/cart/items", json=new_item)
    assert response.status_code == 400
    assert "not available for this menu item" in response.json()["detail"]

def test_update_cart_item(client):
    update_data = {
        "menu_item_id": str(mock_menu_item_1["_id"]),
        "quantity": 3,
        "selected_options": ["Extra Cheese", "Bacon"],
        "special_instructions": "Very crispy"
    }
    response = client.put(f"/cart/items/{str(mock_menu_item_1['_id'])}", json=update_data)
    assert response.status_code == 200
    cart = response.json()
    updated_item = cart["items"][0]
    assert updated_item["quantity"] == 3
    assert len(updated_item["selected_options"]) == 2
    assert updated_item["special_instructions"] == "Very crispy"
    assert cart["total_amount"] == pytest.approx(49.47, rel=1e-9)  # (12.99 + 1.50 + 2.00) * 3

def test_update_cart_item_not_found(client):
    update_data = {
        "menu_item_id": str(ObjectId()),
        "quantity": 1,
        "selected_options": [],
        "special_instructions": ""
    }
    response = client.put(f"/cart/items/{str(ObjectId())}", json=update_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "Item not found in cart"
