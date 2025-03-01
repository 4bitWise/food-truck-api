import pytest
from httpx import AsyncClient
from ..main import app

@pytest.mark.asyncio
async def test_cart_lifecycle():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Test adding item to cart
        test_item = {
            "menu_item_id": "test_menu_item",
            "quantity": 2,
            "special_instructions": "Extra spicy"
        }
        
        response = await client.post("/cart/", json=test_item)
        assert response.status_code == 200
        cart_data = response.json()
        assert len(cart_data["items"]) == 1
        assert cart_data["items"][0]["menu_item_id"] == test_item["menu_item_id"]

        # Test getting cart
        response = await client.get("/cart/")
        assert response.status_code == 200
        assert len(response.json()["items"]) == 1

        # Test removing item from cart
        response = await client.delete(f"/cart/items/{test_item['menu_item_id']}")
        assert response.status_code == 200

        # Verify cart is empty
        response = await client.get("/cart/")
        assert response.status_code == 200
        assert len(response.json()["items"]) == 0

        # Test clearing cart
        response = await client.delete("/cart/")
        assert response.status_code == 200

@pytest.mark.asyncio
async def test_cart_error_cases():
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Test getting non-existent cart
        response = await client.get("/cart/")
        assert response.status_code == 404

        # Test adding invalid menu item to cart
        test_item = {
            "menu_item_id": "nonexistent_item",
            "quantity": 1
        }
        response = await client.post("/cart/", json=test_item)
        assert response.status_code == 404 