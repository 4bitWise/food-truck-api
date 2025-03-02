import pytest
from httpx import AsyncClient
from bson import ObjectId
from datetime import datetime, UTC
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app
from database import get_database
from schemas.order import OrderStatus


@pytest.mark.asyncio
async def test_order_lifecycle():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Setup test data
        db = get_database()
        menu_collection = db["menu"]
        options_collection = db["options"]

        # Create test options
        cheese_option = {
            "_id": ObjectId(),
            "name": "Extra Cheese",
            "price": 1.50
        }
        bacon_option = {
            "_id": ObjectId(),
            "name": "Bacon",
            "price": 2.00
        }
        options_collection.insert_many([cheese_option, bacon_option])

        # Create test menu item
        menu_item = {
            "_id": ObjectId(),
            "name": "Classic Burger",
            "price": 9.99,
            "description": "Juicy beef patty with lettuce and tomato",
            "available": True,
            "options": [cheese_option["_id"], bacon_option["_id"]]
        }
        menu_collection.insert_one(menu_item)

        # Add item to cart with options
        test_item = {
            "menu_item_id": str(menu_item["_id"]),
            "quantity": 2,
            "selected_options": ["Extra Cheese", "Bacon"],
            "special_instructions": "Well done"
        }
        
        # Create cart with item
        response = await client.post("/cart/items", json=test_item)
        assert response.status_code == 200

        # Create order from cart
        response = await client.post("/orders/")
        assert response.status_code == 200
        order_data = response.json()
        
        # Verify order data
        assert order_data["status"] == OrderStatus.PENDING
        assert len(order_data["items"]) == 1
        item = order_data["items"][0]
        assert item["name"] == "Classic Burger"
        assert item["price"] == 9.99
        assert item["quantity"] == 2
        assert set(item["selected_options"]) == {"Extra Cheese", "Bacon"}
        assert item["special_instructions"] == "Well done"
        # Base price + options = 9.99 + 1.50 + 2.00 = 13.49 * 2 = 26.98
        assert item["total_price"] == 26.98
        assert order_data["total_amount"] == 26.98

        order_id = order_data["id"]
        order_number = order_data["order_number"]

        # Test getting order by number
        response = await client.get(f"/orders/order/{order_number}")
        assert response.status_code == 200
        assert response.json()["order_number"] == order_number

        # Test getting all orders
        response = await client.get("/orders/")
        assert response.status_code == 200
        orders = response.json()
        assert len(orders) > 0

        # Test order status flow
        # 1. Pay for order (PENDING -> IN_PREPARATION)
        response = await client.post(f"/orders/{order_id}/pay")
        assert response.status_code == 200
        assert response.json()["status"] == OrderStatus.IN_PREPARATION

        # 2. Update to READY
        response = await client.put(
            f"/orders/{order_id}/status",
            json=OrderStatus.READY
        )
        assert response.status_code == 200
        assert response.json()["status"] == OrderStatus.READY

        # 3. Update to DELIVERED
        response = await client.put(
            f"/orders/{order_id}/status",
            json=OrderStatus.DELIVERED
        )
        assert response.status_code == 200
        assert response.json()["status"] == OrderStatus.DELIVERED

        # Clean up
        menu_collection.delete_one({"_id": menu_item["_id"]})
        options_collection.delete_many({"_id": {"$in": [cheese_option["_id"], bacon_option["_id"]]}})

@pytest.mark.asyncio
async def test_order_cancellation():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Setup test data
        db = get_database()
        menu_collection = db["menu"]
        menu_item = {
            "_id": ObjectId(),
            "name": "Test Item",
            "price": 10.00,
            "description": "Test description",
            "available": True
        }
        menu_collection.insert_one(menu_item)

        # Create cart and order
        test_item = {
            "menu_item_id": str(menu_item["_id"]),
            "quantity": 1,
            "selected_options": []
        }
        
        await client.post("/cart/items", json=test_item)
        response = await client.post("/orders/")
        order_id = response.json()["id"]

        # Test cancelling order
        response = await client.post(f"/orders/{order_id}/cancel")
        assert response.status_code == 200
        assert response.json()["status"] == OrderStatus.CANCELLED

        # Verify can't update cancelled order
        response = await client.put(
            f"/orders/{order_id}/status",
            json=OrderStatus.IN_PREPARATION
        )
        assert response.status_code == 400

        # Clean up
        menu_collection.delete_one({"_id": menu_item["_id"]})

@pytest.mark.asyncio
async def test_invalid_status_transitions():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Setup test data
        db = get_database()
        menu_collection = db["menu"]
        menu_item = {
            "_id": ObjectId(),
            "name": "Test Item",
            "price": 10.00,
            "available": True
        }
        menu_collection.insert_one(menu_item)

        # Create cart and order
        test_item = {
            "menu_item_id": str(menu_item["_id"]),
            "quantity": 1,
            "selected_options": []
        }
        
        await client.post("/cart/items", json=test_item)
        response = await client.post("/orders/")
        order_id = response.json()["id"]

        # Test invalid transitions
        # Cannot go from PENDING to READY
        response = await client.put(
            f"/orders/{order_id}/status",
            json=OrderStatus.READY
        )
        assert response.status_code == 400

        # Cannot go from PENDING to DELIVERED
        response = await client.put(
            f"/orders/{order_id}/status",
            json=OrderStatus.DELIVERED
        )
        assert response.status_code == 400

        # Pay for order
        response = await client.post(f"/orders/{order_id}/pay")
        assert response.status_code == 200

        # Cannot cancel after payment
        response = await client.post(f"/orders/{order_id}/cancel")
        assert response.status_code == 400

        # Cannot go from IN_PREPARATION to DELIVERED
        response = await client.put(
            f"/orders/{order_id}/status",
            json=OrderStatus.DELIVERED
        )
        assert response.status_code == 400

        # Clean up
        menu_collection.delete_one({"_id": menu_item["_id"]})

@pytest.mark.asyncio
async def test_order_with_invalid_options():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Setup test data
        db = get_database()
        menu_collection = db["menu"]
        options_collection = db["options"]

        # Create test option
        option = {
            "_id": ObjectId(),
            "name": "Test Option",
            "price": 1.00
        }
        options_collection.insert_one(option)

        # Create menu item without options
        menu_item = {
            "_id": ObjectId(),
            "name": "Test Item",
            "price": 10.00,
            "available": True,
            "options": []  # No options available
        }
        menu_collection.insert_one(menu_item)

        # Try to add item with unavailable option
        test_item = {
            "menu_item_id": str(menu_item["_id"]),
            "quantity": 1,
            "selected_options": ["Test Option"]  # This option is not available for this item
        }
        
        response = await client.post("/cart/items", json=test_item)
        assert response.status_code == 400

        # Clean up
        menu_collection.delete_one({"_id": menu_item["_id"]})
        options_collection.delete_one({"_id": option["_id"]})

@pytest.mark.asyncio
async def test_order_error_cases():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Test creating order with empty cart
        response = await client.post("/orders/")
        assert response.status_code == 400

        # Test getting non-existent order
        response = await client.get("/orders/order/NONEXISTENT-ORDER")
        assert response.status_code == 404

        # Test updating non-existent order
        response = await client.put(
            "/orders/nonexistent_id/status",
            json=OrderStatus.IN_PREPARATION
        )
        assert response.status_code == 400

        # Test cancelling non-existent order
        response = await client.post("/orders/nonexistent_id/cancel")
        assert response.status_code == 400

        # Test paying for non-existent order
        response = await client.post("/orders/nonexistent_id/pay")
        assert response.status_code == 400

# Create a mock database
@pytest.fixture
def mock_db():
    # Create mock collections
    mock_order_collection = MagicMock()
    mock_cart_collection = MagicMock()
    mock_menu_collection = MagicMock()
    mock_options_collection = MagicMock()
    
    # Create a mock database that returns our mock collections
    mock_db = MagicMock()
    mock_db.__getitem__.side_effect = {
        "orders": mock_order_collection,
        "carts": mock_cart_collection,
        "menu": mock_menu_collection,
        "options": mock_options_collection
    }.__getitem__
    
    return mock_db

@pytest.fixture
def client(mock_db):
    # Override the get_database dependency
    app.dependency_overrides[get_database] = lambda: mock_db
    return TestClient(app)

def test_create_order_success(client, mock_db):
    # Mock data
    mock_cart = {
        "_id": ObjectId(),
        "items": [
            {
                "menu_item_id": "item123",
                "quantity": 2,
                "selected_options": ["Extra Cheese"],
                "special_instructions": "Well done"
            }
        ]
    }
    
    mock_menu_item = {
        "_id": ObjectId("item123"),
        "name": "Burger",
        "price": 10.0,
        "options": ["Extra Cheese"]
    }
    
    mock_options = [
        {
            "name": "Extra Cheese",
            "price": 2.0
        }
    ]
    
    # Setup mock responses
    mock_db["carts"].find_one.return_value = mock_cart
    mock_db["menu"].find_one.return_value = mock_menu_item
    mock_db["options"].find.return_value = mock_options
    
    # Mock the order creation response
    created_order = {
        "_id": ObjectId(),
        "order_number": "FT-2024-0001",
        "items": [
            {
                "menu_item_id": "item123",
                "quantity": 2,
                "selected_options": ["Extra Cheese"],
                "special_instructions": "Well done",
                "total_price": 24.0  # (10.0 + 2.0) * 2
            }
        ],
        "total_amount": 24.0,
        "status": "pending",
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC)
    }
    mock_db["orders"].insert_one.return_value.inserted_id = created_order["_id"]
    mock_db["orders"].find_one.return_value = created_order
    
    # Make request
    response = client.post("/orders/")
    
    # Assertions
    assert response.status_code == 200
    assert response.json()["order_number"] == "FT-2024-0001"
    assert response.json()["total_amount"] == 24.0
    assert response.json()["status"] == "pending"
    assert len(response.json()["items"]) == 1
    assert response.json()["items"][0]["total_price"] == 24.0
    
    # Verify cart was cleared
    mock_db["carts"].delete_one.assert_called_once_with({"_id": mock_cart["_id"]})

def test_create_order_empty_cart(client, mock_db):
    # Mock empty cart
    mock_db["carts"].find_one.return_value = {"items": []}
    
    # Make request
    response = client.post("/orders/")
    
    # Assertions
    assert response.status_code == 400
    assert response.json()["detail"] == "Cart is empty"

def test_create_order_invalid_options(client, mock_db):
    # Mock cart with invalid option
    mock_cart = {
        "_id": ObjectId(),
        "items": [
            {
                "menu_item_id": "item123",
                "quantity": 2,
                "selected_options": ["Invalid Option"],
                "special_instructions": "Well done"
            }
        ]
    }
    
    mock_menu_item = {
        "_id": ObjectId("item123"),
        "name": "Burger",
        "price": 10.0,
        "options": ["Extra Cheese"]
    }
    
    mock_options = [
        {
            "name": "Extra Cheese",
            "price": 2.0
        }
    ]
    
    # Setup mock responses
    mock_db["carts"].find_one.return_value = mock_cart
    mock_db["menu"].find_one.return_value = mock_menu_item
    mock_db["options"].find.return_value = mock_options
    
    # Make request
    response = client.post("/orders/")
    
    # Assertions
    assert response.status_code == 400
    assert "Option 'Invalid Option' is not available" in response.json()["detail"]

def test_update_order_status_success(client, mock_db):
    # Mock existing order
    mock_order = {
        "_id": ObjectId(),
        "order_number": "FT-2024-0001",
        "status": "pending",
        "items": [],
        "total_amount": 0
    }
    
    # Setup mock responses
    mock_db["orders"].find_one.return_value = mock_order
    mock_db["orders"].find_one_and_update.return_value = {
        **mock_order,
        "status": "en préparation"
    }
    
    # Make request
    response = client.put(f"/orders/{str(mock_order['_id'])}/status?status=en+préparation")
    
    # Assertions
    assert response.status_code == 200
    assert response.json()["status"] == "en préparation"

def test_update_order_status_invalid_transition(client, mock_db):
    # Mock existing order
    mock_order = {
        "_id": ObjectId(),
        "order_number": "FT-2024-0001",
        "status": "pending",
        "items": [],
        "total_amount": 0
    }
    
    # Setup mock responses
    mock_db["orders"].find_one.return_value = mock_order
    
    # Make request - try to go from PENDING to DELIVERED (invalid)
    response = client.put(f"/orders/{str(mock_order['_id'])}/status?status=livrée")
    
    # Assertions
    assert response.status_code == 400
    assert "Cannot transition from" in response.json()["detail"]

def test_cancel_order_success(client, mock_db):
    # Mock existing pending order
    mock_order = {
        "_id": ObjectId(),
        "order_number": "FT-2024-0001",
        "status": "pending",
        "items": [],
        "total_amount": 0
    }
    
    # Setup mock responses
    mock_db["orders"].find_one.return_value = mock_order
    mock_db["orders"].find_one_and_update.return_value = {
        **mock_order,
        "status": "annulée"
    }
    
    # Make request
    response = client.post(f"/orders/{str(mock_order['_id'])}/cancel")
    
    # Assertions
    assert response.status_code == 200
    assert response.json()["status"] == "annulée"

def test_cancel_non_pending_order(client, mock_db):
    # Mock existing non-pending order
    mock_order = {
        "_id": ObjectId(),
        "order_number": "FT-2024-0001",
        "status": "en préparation",
        "items": [],
        "total_amount": 0
    }
    
    # Setup mock responses
    mock_db["orders"].find_one.return_value = mock_order
    
    # Make request
    response = client.post(f"/orders/{str(mock_order['_id'])}/cancel")
    
    # Assertions
    assert response.status_code == 400
    assert response.json()["detail"] == "Can only cancel pending orders" 