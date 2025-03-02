from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime, UTC
from bson import ObjectId
from pymongo import ReturnDocument
from database import get_collections
from schemas.order import Order, OrderStatus, OrderResponse
from schemas.cart import CartItem

router = APIRouter()

def generate_order_number(collections: dict) -> str:
    year = datetime.now(UTC).year
    orders_collection = collections["orders"]
    latest_order = orders_collection.find_one(
        {"order_number": {"$regex": f"^FT-{year}-"}},
        sort=[("order_number", -1)]
    )
    
    if latest_order:
        last_number = int(latest_order["order_number"].split("-")[-1])
        new_number = last_number + 1
    else:
        new_number = 1
    
    return f"FT-{year}-{new_number:04d}"

def validate_menu_item_and_options(menu_item_id: str, selected_options: List[str], collections: dict) -> tuple:
    """
    Validates menu item and its options, returns (menu_item, available_options) if valid
    Raises HTTPException if invalid
    """
    menu_item = collections["menu"].find_one({"_id": ObjectId(menu_item_id)})
    if not menu_item:
        raise HTTPException(
            status_code=400,
            detail=f"Menu item {menu_item_id} not found"
        )

    # Get available options for this menu item
    if menu_item.get("options"):
        available_options = list(collections["options"].find(
            {"name": {"$in": menu_item["options"]}}
        ))
        available_option_names = {opt["name"] for opt in available_options}
    else:
        available_options = []
        available_option_names = set()

    # Verify selected options
    for option_name in selected_options:
        if option_name not in available_option_names:
            raise HTTPException(
                status_code=400,
                detail=f"Option '{option_name}' is not available for menu item '{menu_item['name']}'"
            )

    return menu_item, available_options

def calculate_item_total(base_price: float, quantity: int, selected_options: List[str], available_options: List[dict]) -> float:
    """Calculates total price for an item including options"""
    option_prices = {opt["name"]: opt["price"] for opt in available_options}
    options_total = sum(option_prices.get(name, 0) for name in selected_options)
    return (base_price + options_total) * quantity

def validate_menu_items(items: List[dict], collections: dict):
    menu_collection = collections["menu"]
    for item in items:
        menu_item = menu_collection.find_one({"_id": ObjectId(item["menu_item_id"])})
        if not menu_item:
            raise HTTPException(status_code=404, detail=f"Menu item {item['menu_item_id']} not found")
        if not all(option in menu_item["options"] for option in item["selected_options"]):
            raise HTTPException(status_code=400, detail=f"Invalid options for menu item {item['menu_item_id']}")

def calculate_total_amount(items: List[dict], collections: dict) -> float:
    menu_collection = collections["menu"]
    options_collection = collections["options"]
    total = 0.0
    for item in items:
        menu_item = menu_collection.find_one({"_id": ObjectId(item["menu_item_id"])})
        if not menu_item:
            raise HTTPException(status_code=404, detail=f"Menu item {item['menu_item_id']} not found")
        
        # Get option prices
        if item["selected_options"]:
            available_options = list(options_collection.find(
                {"name": {"$in": item["selected_options"]}}
            ))
            option_prices = {opt["name"]: opt["price"] for opt in available_options}
            options_total = sum(option_prices.get(name, 0) for name in item["selected_options"])
        else:
            options_total = 0
            
        # Calculate total including options
        item_total = (menu_item["price"] + options_total) * item["quantity"]
        total += item_total
    return total

@router.post("/", response_model=OrderResponse)
async def create_order(collections: dict = Depends(get_collections)):
    orders_collection = collections["orders"]
    carts_collection = collections["carts"]

    # Get current cart
    cart = carts_collection.find_one(sort=[("created_at", -1)])
    if not cart:
        raise HTTPException(status_code=404, detail="No active cart found")
    
    if not cart["items"]:
        raise HTTPException(status_code=400, detail="Cannot create order with empty cart")
    
    # Validate all menu items exist and have valid options
    validate_menu_items(cart["items"], collections)
    
    # Calculate total amount
    total_amount = calculate_total_amount(cart["items"], collections)
    
    # Generate order number
    order_number = generate_order_number(collections)
    
    # Create order document
    order_data = {
        "order_number": order_number,
        "items": cart["items"],
        "total_amount": total_amount,
        "status": OrderStatus.PENDING,
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC)
    }
    
    # Insert order
    result = orders_collection.insert_one(order_data)
    
    # Clear the cart after successful order creation
    carts_collection.delete_one({"_id": cart["_id"]})
    
    # Return order with string ID
    order_data["_id"] = result.inserted_id
    order_data["id"] = str(order_data.pop("_id"))
    return OrderResponse(**order_data)

@router.get("/", response_model=List[OrderResponse])
async def get_orders(
    status: Optional[OrderStatus] = None,
    collections: dict = Depends(get_collections)
):
    orders_collection = collections["orders"]
    
    # Build query based on status filter
    query = {}
    if status:
        query["status"] = status
    
    # Get orders
    orders = list(orders_collection.find(query))
    
    # Convert ObjectId to string for response
    for order in orders:
        order["id"] = str(order.pop("_id"))
    
    return orders

@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    collections: dict = Depends(get_collections)
):
    orders_collection = collections["orders"]
    
    try:
        order = orders_collection.find_one({"_id": ObjectId(order_id)})
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Convert ObjectId to string for response
        order["id"] = str(order.pop("_id"))
        return OrderResponse(**order)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid order ID")

@router.put("/{order_id}/status")
async def update_order_status(
    order_id: str,
    status: OrderStatus,
    collections: dict = Depends(get_collections)
):
    orders_collection = collections["orders"]
    
    try:
        # Update order status
        result = orders_collection.update_one(
            {"_id": ObjectId(order_id)},
            {
                "$set": {
                    "status": status,
                    "updated_at": datetime.now(UTC)
                }
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Order not found")
        
        return {"message": f"Order status updated to {status}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid order ID")

@router.post("/{order_id}/cancel", response_model=Order)
async def cancel_order(
    order_id: str,
    collections: dict = Depends(get_collections)
):
    orders_collection = collections["orders"]
    try:
        order = orders_collection.find_one({"_id": ObjectId(order_id)})
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        if order["status"] != OrderStatus.PENDING:
            raise HTTPException(
                status_code=400,
                detail="Can only cancel pending orders"
            )
        
        result = orders_collection.find_one_and_update(
            {"_id": ObjectId(order_id)},
            {
                "$set": {
                    "status": OrderStatus.CANCELLED,
                    "updated_at": datetime.now(UTC)
                }
            },
            return_document=ReturnDocument.AFTER
        )
        
        if not result:
            raise HTTPException(
                status_code=400,
                detail="Failed to cancel order"
            )
        return {**result, "id": str(result["_id"])}
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid order ID " + str(e))

@router.post("/{order_id}/pay", response_model=Order)
async def mark_order_as_paid(
    order_id: str,
    collections: dict = Depends(get_collections)
):
    orders_collection = collections["orders"]
    try:
        order = orders_collection.find_one({"_id": ObjectId(order_id)})
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        if order["status"] != OrderStatus.PENDING:
            raise HTTPException(
                status_code=400,
                detail="Can only pay for pending orders"
            )
        
        result = orders_collection.find_one_and_update(
            {"_id": ObjectId(order_id)},
            {
                "$set": {
                    "status": OrderStatus.IN_PREPARATION,
                    "updated_at": datetime.now(UTC)
                }
            },
            return_document=ReturnDocument.AFTER
        )
        return {**result, "id": str(result["_id"])}
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid order ID " + str(e)) 