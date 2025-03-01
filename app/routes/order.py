from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime, UTC
from bson import ObjectId
from database import get_database
from schemas.order import Order, OrderStatus
from pymongo import ReturnDocument

router = APIRouter()

db = get_database()
order_collection = db["orders"]
cart_collection = db["carts"]
menu_collection = db["menu"]

def generate_order_number() -> str:
    year = datetime.now(UTC).year
    latest_order = order_collection.find_one(
        {"order_number": {"$regex": f"^FT-{year}-"}},
        sort=[("order_number", -1)]
    )
    
    if latest_order:
        last_number = int(latest_order["order_number"].split("-")[-1])
        new_number = last_number + 1
    else:
        new_number = 1
    
    return f"FT-{year}-{new_number:04d}"

@router.post("/", response_model=Order)
async def create_order():
    # Get active cart
    cart = cart_collection.find_one(sort=[("created_at", -1)])
    if not cart or not cart["items"]:
        raise HTTPException(status_code=400, detail="Cart is empty")

    # Calculate total and validate items
    total_amount = 0
    order_items = []
    current_time = datetime.now(UTC)
    
    for item in cart["items"]:
        menu_item = menu_collection.find_one({"_id": ObjectId(item["menu_item_id"])})
        if not menu_item:
            raise HTTPException(
                status_code=400,
                detail=f"Menu item {item['menu_item_id']} not found"
            )
        
        item_total = menu_item["price"] * item["quantity"]
        order_items.append({
            **item,
            "name": menu_item["name"],
            "price": menu_item["price"]
        })
        total_amount += item_total

    # Generate order number
    order_number = generate_order_number()

    # Create order
    order_data = {
        "order_number": order_number,
        "items": order_items,
        "total_amount": total_amount,
        "status": OrderStatus.PENDING,
        "created_at": current_time,
        "updated_at": current_time
    }

    result = order_collection.insert_one(order_data)
    created_order = order_collection.find_one({"_id": result.inserted_id})

    # Clear the cart after successful order creation
    cart_collection.delete_one({"_id": cart["_id"]})

    return {**created_order, "id": str(created_order["_id"])}

@router.get("/", response_model=List[Order])
async def get_all_orders():
    orders = list(order_collection.find())
    return [{**order, "id": str(order["_id"])} for order in orders]

@router.get("/order/{order_number}", response_model=Order)
async def get_order_by_number(order_number: str):
    order = order_collection.find_one({"order_number": order_number})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return {**order, "id": str(order["_id"])}

@router.put("/{order_id}/status", response_model=Order)
async def update_order_status(order_id: str, status: OrderStatus):
    try:
        order = order_collection.find_one({"_id": ObjectId(order_id)})
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Validate status transition
        if order["status"] == OrderStatus.CANCELLED:
            raise HTTPException(
                status_code=400,
                detail="Cannot update status of cancelled order"
            )
        
        result = order_collection.find_one_and_update(
            {"_id": ObjectId(order_id)},
            {
                "$set": {
                    "status": status,
                    "updated_at": datetime.now(UTC)
                }
            },
            return_document=ReturnDocument.AFTER
        )
        return {**result, "id": str(result["_id"])}
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid order ID")

@router.post("/{order_id}/cancel", response_model=Order)
async def cancel_order(order_id: str):
    try:
        order = order_collection.find_one({"_id": ObjectId(order_id)})
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        if order["status"] != OrderStatus.PENDING:
            raise HTTPException(
                status_code=400,
                detail="Can only cancel pending orders"
            )
        
        result = order_collection.find_one_and_update(
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
        raise HTTPException(status_code=400, detail="Invalid order ID")

@router.post("/{order_id}/pay", response_model=Order)
async def mark_order_as_paid(order_id: str):
    try:
        order = order_collection.find_one({"_id": ObjectId(order_id)})
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        if order["status"] != OrderStatus.PENDING:
            raise HTTPException(
                status_code=400,
                detail="Can only pay for pending orders"
            )
        
        result = order_collection.find_one_and_update(
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
        raise HTTPException(status_code=400, detail="Invalid order ID") 