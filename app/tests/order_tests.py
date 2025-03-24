import pytest
from fastapi.testclient import TestClient
from bson import ObjectId
from datetime import datetime, UTC
from main import app
from database import get_collections
from schemas.order import OrderStatus

# Get current year for order numbers
CURRENT_YEAR = datetime.now(UTC).year

# Reuse mock data from cart tests
mock_menu_item_1 = {
    "_id": ObjectId(),
    "name": "Margherita Pizza",
    "description": "Classic pizza with tomato sauce and mozzarella",
    "price": 12.99,
    "category": "Pizza",
    "options": ["Extra Cheese", "Bacon"],
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

mock_order = {
    "_id": ObjectId(),
    "order_number": f"FT-{CURRENT_YEAR}-0001",
    "items": mock_cart["items"],
    "total_amount": mock_cart["total_amount"],
    "status": "pending",
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
        if query and "status" in query:
            # Handle status filter for orders
            return [item for item in self.data if item["status"] == query["status"]]
        if query and "order_number" in query and "$regex" in query["order_number"]:
            # Handle order number regex for latest order
            pattern = query["order_number"]["$regex"]
            return [item for item in self.data if item["order_number"].startswith(pattern[1:])]
        return self.data

    def find_one(self, query=None, sort=None):
        if not self.data:
            return None

        if sort:
            # Handle sorting
            if sort[0][0] == "created_at":
                return self.data[-1]
            if sort[0][0] == "order_number":
                return sorted(self.data, key=lambda x: x["order_number"])[-1]

        if query and "_id" in query:
            return next((item for item in self.data if item["_id"] == query["_id"]), None)
        return self.data[0]

    def insert_one(self, document):
        document["_id"] = ObjectId()
        self.data.append(document)
        return type("InsertOneResult", (), {"inserted_id": document["_id"]})

    def find_one_and_update(self, query, update, return_document=None):
        item = self.find_one(query)
        if item:
            if "$set" in update:
                # Create a new copy of the item with updates
                updated_item = {**item, **update["$set"]}
                # Update the item in self.data
                for i, data_item in enumerate(self.data):
                    if data_item["_id"] == item["_id"]:
                        self.data[i] = updated_item
                        break
                return updated_item
            return item
        return None

    def update_one(self, query, update):
        item = self.find_one(query)
        if item:
            if "$set" in update:
                # Create a new copy of the item with updates
                updated_item = {**item, **update["$set"]}
                # Update the item in self.data
                for i, data_item in enumerate(self.data):
                    if data_item["_id"] == item["_id"]:
                        self.data[i] = updated_item
                        break
            return type("UpdateResult", (), {"modified_count": 1})
        return type("UpdateResult", (), {"modified_count": 0})

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
        "menu": MockCollection([mock_menu_item_1.copy()]),
        "options": MockCollection(mock_options),
        "carts": MockCollection([mock_cart.copy()]),
        "orders": MockCollection([mock_order.copy()])
    }

# Setup test client
@pytest.fixture
def client():
    app.dependency_overrides[get_collections] = mock_get_collections
    return TestClient(app)

# Test cases
def test_create_order(client):
    response = client.post("/orders/")
    assert response.status_code == 200
    order = response.json()
    assert order["order_number"].startswith(f"FT-{CURRENT_YEAR}-")
    assert len(order["items"]) == 1
    assert order["total_amount"] == pytest.approx(28.98, rel=1e-9)
    assert order["status"] == "pending"

def test_create_order_no_cart(client):
    # Override mock to return empty cart collection
    app.dependency_overrides[get_collections] = lambda: {
        "menu": MockCollection([mock_menu_item_1.copy()]),
        "options": MockCollection(mock_options),
        "carts": MockCollection([]),
        "orders": MockCollection([])
    }
    response = client.post("/orders/")
    assert response.status_code == 404
    assert response.json()["detail"] == "No active cart found"

def test_create_order_empty_cart(client):
    # Override mock with empty cart
    empty_cart = {**mock_cart, "items": []}
    app.dependency_overrides[get_collections] = lambda: {
        "menu": MockCollection([mock_menu_item_1.copy()]),
        "options": MockCollection(mock_options),
        "carts": MockCollection([empty_cart]),
        "orders": MockCollection([])
    }
    response = client.post("/orders/")
    assert response.status_code == 400
    assert response.json()["detail"] == "Cannot create order with empty cart"

def test_get_orders(client):
    response = client.get("/orders/")
    assert response.status_code == 200
    orders = response.json()
    assert len(orders) == 1
    assert orders[0]["order_number"] == f"FT-{CURRENT_YEAR}-0001"

def test_get_orders_with_status(client):
    response = client.get("/orders/?status=pending")
    assert response.status_code == 200
    orders = response.json()
    assert len(orders) == 1
    assert all(order["status"] == "pending" for order in orders)

def test_get_order_by_id(client):
    order_id = str(mock_order["_id"])
    response = client.get(f"/orders/{order_id}")
    assert response.status_code == 200
    order = response.json()
    assert order["order_number"] == f"FT-{CURRENT_YEAR}-0001"
    assert order["status"] == "pending"

def test_get_order_not_found(client):
    response = client.get(f"/orders/{str(ObjectId())}")
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid order ID"

def test_update_order_status_not_found(client):
    response = client.put(f"/orders/{str(ObjectId())}/status?status=en préparation")
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid order ID"

def test_cancel_order(client):
    order_id = str(mock_order["_id"])
    response = client.post(f"/orders/{order_id}/cancel")
    assert response.status_code == 200
    order = response.json()
    assert order["status"] == "annulée"

def test_pay_order(client):
    order_id = str(mock_order["_id"])
    response = client.post(f"/orders/{order_id}/pay")
    assert response.status_code == 200
    order = response.json()
    assert order["status"] == "en préparation"
