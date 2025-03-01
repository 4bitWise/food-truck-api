from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime, UTC
from bson import ObjectId
from database import get_database
from schemas.cart import Cart, CartItem
from pymongo import ReturnDocument

router = APIRouter()

db = get_database()
cart_collection = db["carts"]
menu_collection = db["menu"]

@router.post("/", response_model=Cart)
async def add_to_cart(item: CartItem):
    # Verify if menu item exists
    menu_item = menu_collection.find_one({"_id": ObjectId(item.menu_item_id)})
    if not menu_item:
        raise HTTPException(status_code=404, detail="Menu item not found")

    # Get existing cart or create new one
    cart = cart_collection.find_one(sort=[("created_at", -1)])
    current_time = datetime.now(UTC)

    if not cart:
        # Create new cart
        cart_data = {
            "items": [item.dict()],
            "created_at": current_time,
            "updated_at": current_time
        }
        result = cart_collection.insert_one(cart_data)
        return {**cart_data, "id": str(result.inserted_id)}
    
    # Update existing cart
    cart["items"].append(item.dict())
    cart["updated_at"] = current_time
    
    result = cart_collection.find_one_and_update(
        {"_id": cart["_id"]},
        {"$set": cart},
        return_document=ReturnDocument.AFTER
    )
    return {**result, "id": str(result["_id"])}

@router.get("/", response_model=Cart)
async def get_cart():
    cart = cart_collection.find_one(sort=[("created_at", -1)])
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    return {**cart, "id": str(cart["_id"])}

@router.delete("/items/{menu_item_id}")
async def remove_from_cart(menu_item_id: str):
    cart = cart_collection.find_one(sort=[("created_at", -1)])
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    # Remove the item from the cart
    cart["items"] = [item for item in cart["items"] if item["menu_item_id"] != menu_item_id]
    cart["updated_at"] = datetime.now(UTC)
    
    cart_collection.find_one_and_update(
        {"_id": cart["_id"]},
        {"$set": cart}
    )
    return {"message": "Item removed from cart"}

@router.delete("/")
async def clear_cart():
    cart = cart_collection.find_one(sort=[("created_at", -1)])
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
        
    result = cart_collection.delete_one({"_id": cart["_id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Cart not found")
        
    return {"message": "Cart cleared successfully"}