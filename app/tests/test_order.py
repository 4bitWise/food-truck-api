import pytest
from httpx import AsyncClient
from ..main import app
from ..schemas.order import OrderStatus

@pytest.mark.asyncio
async def test_order_lifecycle():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # First, create a cart with items
        test_item = {
            "menu_item_id": "test_menu_item",
            "quantity": 2,
            "special_instructions": "Extra spicy"
        }
        
        await client.post("/cart/items", json=test_item)

        # Create order from cart
        response = await client.post("/orders/")
        assert response.status_code == 200
        order_data = response.json()
        assert order_data["status"] == OrderStatus.PENDING
        order_id = order_data["id"]

        # Test getting order by number
        order_number = order_data["order_number"]
        response = await client.get(f"/orders/order/{order_number}")
        assert response.status_code == 200
        assert response.json()["order_number"] == order_number

        # Test getting all orders
        response = await client.get("/orders/")
        assert response.status_code == 200
        orders = response.json()
        assert len(orders) > 0

        # Test paying for order (should change status to IN_PREPARATION)
        response = await client.post(f"/orders/{order_id}/pay")
        assert response.status_code == 200
        assert response.json()["status"] == OrderStatus.IN_PREPARATION

        # Test updating order to READY
        response = await client.put(
            f"/orders/{order_id}/status",
            json=OrderStatus.READY
        )
        assert response.status_code == 200
        assert response.json()["status"] == OrderStatus.READY

        # Test updating order to DELIVERED
        response = await client.put(
            f"/orders/{order_id}/status",
            json=OrderStatus.DELIVERED
        )
        assert response.status_code == 200
        assert response.json()["status"] == OrderStatus.DELIVERED

@pytest.mark.asyncio
async def test_order_cancellation():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create a cart and order
        test_item = {
            "menu_item_id": "test_menu_item",
            "quantity": 1
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

@pytest.mark.asyncio
async def test_invalid_status_transitions():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create a cart and order
        test_item = {
            "menu_item_id": "test_menu_item",
            "quantity": 1
        }
        
        await client.post("/cart/items", json=test_item)
        response = await client.post("/orders/")
        order_id = response.json()["id"]

        # Test can't mark as READY before payment
        response = await client.put(
            f"/orders/{order_id}/status",
            json=OrderStatus.READY
        )
        assert response.status_code == 400

        # Pay for order
        response = await client.post(f"/orders/{order_id}/pay")
        assert response.status_code == 200

        # Test can't cancel after payment
        response = await client.post(f"/orders/{order_id}/cancel")
        assert response.status_code == 400

        # Test can't pay again
        response = await client.post(f"/orders/{order_id}/pay")
        assert response.status_code == 400 