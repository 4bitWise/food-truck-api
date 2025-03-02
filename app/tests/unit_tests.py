import pytest
from datetime import datetime
from bson import ObjectId
from fastapi import HTTPException
from routes.order import (
    generate_order_number,
    calculate_item_total,
    validate_menu_item_and_options
)

# Mock data for tests
mock_menu_item = {
    "_id": ObjectId(),
    "name": "Test Item",
    "price": 10.0,
    "options": ["Extra Cheese", "Bacon"]
}

mock_options = [
    {"name": "Extra Cheese", "price": 1.5},
    {"name": "Bacon", "price": 2.0}
]

# Tests for generate_order_number
def test_generate_order_number_first_order():
    # Mock collections with no existing orders
    collections = {
        "orders": MockCollection([])
    }
    
    # Get current year
    current_year = datetime.now().year
    
    # Generate order number
    order_number = generate_order_number(collections)
    
    # Assert format is correct
    assert order_number == f"FT-{current_year}-0001"

def test_generate_order_number_with_existing_orders():
    current_year = datetime.now().year
    # Mock collections with existing order
    collections = {
        "orders": MockCollection([
            {"order_number": f"FT-{current_year}-0001"}
        ])
    }
    
    order_number = generate_order_number(collections)
    assert order_number == f"FT-{current_year}-0002"

# Tests for calculate_item_total
def test_calculate_item_total_no_options():
    total = calculate_item_total(10.0, 2, [], [])
    assert total == 20.0

def test_calculate_item_total_with_options():
    total = calculate_item_total(
        base_price=10.0,
        quantity=2,
        selected_options=["Extra Cheese", "Bacon"],
        available_options=mock_options
    )
    # Base price: 10.0
    # Options: Extra Cheese (1.5) + Bacon (2.0) = 3.5
    # Total per item: 13.5
    # Quantity: 2
    # Expected total: 27.0
    assert total == 27.0

def test_calculate_item_total_with_invalid_options():
    total = calculate_item_total(
        base_price=10.0,
        quantity=2,
        selected_options=["Invalid Option"],
        available_options=mock_options
    )
    # Invalid options should be ignored
    assert total == 20.0

# Tests for validate_menu_item_and_options
def test_validate_menu_item_and_options_valid():
    collections = {
        "menu": MockCollection([mock_menu_item]),
        "options": MockCollection(mock_options)
    }
    
    menu_item, available_options = validate_menu_item_and_options(
        str(mock_menu_item["_id"]),
        ["Extra Cheese"],
        collections
    )
    
    assert menu_item == mock_menu_item
    assert available_options == mock_options

def test_validate_menu_item_and_options_invalid_menu_item():
    collections = {
        "menu": MockCollection([]),
        "options": MockCollection(mock_options)
    }
    
    with pytest.raises(HTTPException) as exc_info:
        validate_menu_item_and_options(
            str(ObjectId()),
            ["Extra Cheese"],
            collections
        )
    
    assert exc_info.value.status_code == 400
    assert "not found" in str(exc_info.value.detail)

def test_validate_menu_item_and_options_invalid_option():
    collections = {
        "menu": MockCollection([mock_menu_item]),
        "options": MockCollection(mock_options)
    }
    
    with pytest.raises(HTTPException) as exc_info:
        validate_menu_item_and_options(
            str(mock_menu_item["_id"]),
            ["Invalid Option"],
            collections
        )
    
    assert exc_info.value.status_code == 400
    assert "not available" in str(exc_info.value.detail)

# Mock Collection class for testing
class MockCollection:
    def __init__(self, data):
        self.data = data

    def find_one(self, query=None, sort=None):
        if not self.data:
            return None
        
        if sort:
            # Handle sorting for order number queries
            return self.data[-1]
        
        if query and "_id" in query:
            # Handle ObjectId queries
            return next((item for item in self.data if item["_id"] == query["_id"]), None)
            
        return self.data[0]

    def find(self, query=None):
        if query and "name" in query and "$in" in query["name"]:
            # Handle options query
            valid_names = set(query["name"]["$in"])
            return [item for item in self.data if item["name"] in valid_names]
        return self.data 