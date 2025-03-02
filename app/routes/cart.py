from fastapi import APIRouter, HTTPException, Depends
from typing import List
from datetime import datetime, UTC
from bson import ObjectId
from database import get_collections
from schemas.cart import Cart, CartItem
from models.cart import CartItemModel, CartModel
from pymongo import ReturnDocument

router = APIRouter()

def calculate_item_total(base_price: float, quantity: int, selected_options: List[str], menu_item_options: List[dict]) -> float:
    option_prices = {opt["name"]: opt["price"] for opt in menu_item_options}
    options_total = sum(option_prices.get(name, 0) for name in selected_options)
    return (base_price + options_total) * quantity

@router.post("/items", response_model=Cart)
async def add_to_cart(
    item: CartItem,
    collections: dict = Depends(get_collections)
):
    cart_collection = collections["carts"]
    menu_collection = collections["menu"]
    options_collection = collections["options"]

    # Verify if menu item exists and get its details
    menu_item = menu_collection.find_one({"_id": ObjectId(item.menu_item_id)})
    if not menu_item:
        raise HTTPException(status_code=404, detail="Menu item not found")

    # Check if menu item is available
    if not menu_item.get("available", True):  # Default to True if field doesn't exist
        raise HTTPException(
            status_code=400, 
            detail=f"Menu item '{menu_item.get('name', '')}' is currently not available"
        )

    # Get all available options for this menu item
    if menu_item["options"]:
        available_options = list(options_collection.find(
            {"name": {"$in": menu_item["options"]}}
        ))
        available_option_names = {opt["name"] for opt in available_options}
    else:
        available_options = []
        available_option_names = set()

    # Verify selected options exist and are available for this menu item
    for option_name in item.selected_options:
        if option_name not in available_option_names:
            raise HTTPException(
                status_code=400,
                detail=f"Option '{option_name}' is not available for this menu item"
            )

    # Create cart item model with calculated total price
    item_data = CartItemModel(
        menu_item_id=item.menu_item_id,
        quantity=item.quantity,
        selected_options=item.selected_options,
        special_instructions=item.special_instructions,
        total_price=calculate_item_total(
            menu_item["price"],
            item.quantity,
            item.selected_options,
            available_options
        )
    )

    # Get existing cart or create new one
    cart = cart_collection.find_one(sort=[("created_at", -1)])
    current_time = datetime.now(UTC)

    if not cart:
        # Create new cart
        cart_data = CartModel(
            items=[item_data],
            total_amount=item_data.total_price,
            created_at=current_time,
            updated_at=current_time
        )
        result = cart_collection.insert_one(cart_data.model_dump())
        return {**cart_data.model_dump(), "id": str(result.inserted_id)}
    
    # Update existing cart
    cart_model = CartModel(**cart)
    cart_model.items.append(item_data)
    cart_model.total_amount = sum(item.total_price for item in cart_model.items)
    cart_model.updated_at = current_time
    
    result = cart_collection.find_one_and_update(
        {"_id": cart["_id"]},
        {"$set": cart_model.model_dump(exclude={"id"})},
        return_document=ReturnDocument.AFTER
    )
    return {**result, "id": str(result["_id"])}

@router.get("/", response_model=Cart)
async def get_cart(collections: dict = Depends(get_collections)):
    cart_collection = collections["carts"]
    cart = cart_collection.find_one(sort=[("created_at", -1)])
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    return {**cart, "id": str(cart["_id"])}

@router.put("/items/{item_id}", response_model=Cart)
async def update_cart_item(
    item_id: str, 
    updated_item: CartItem,
    collections: dict = Depends(get_collections)
):
    cart_collection = collections["carts"]
    menu_collection = collections["menu"]
    options_collection = collections["options"]

    cart = cart_collection.find_one(sort=[("created_at", -1)])
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    # Find the item in the cart
    item_index = None
    for i, item in enumerate(cart["items"]):
        if item["menu_item_id"] == item_id:
            item_index = i
            break
    
    if item_index is None:
        raise HTTPException(status_code=404, detail="Item not found in cart")

    # Verify menu item and get its options
    menu_item = menu_collection.find_one({"_id": ObjectId(item_id)})
    if not menu_item:
        raise HTTPException(status_code=404, detail="Menu item not found")

    # Check if menu item is available
    if not menu_item.get("available", True):  # Default to True if field doesn't exist
        raise HTTPException(
            status_code=400, 
            detail=f"Menu item '{menu_item.get('name', '')}' is currently not available"
        )

    # Get all available options for this menu item
    if menu_item.get("options"):
        available_options = list(options_collection.find(
            {"name": {"$in": menu_item["options"]}}
        ))
        available_option_names = {opt["name"] for opt in available_options}
    else:
        available_options = []
        available_option_names = set()

    # Verify selected options exist and are available for this menu item
    for option_name in updated_item.selected_options:
        if option_name not in available_option_names:
            raise HTTPException(
                status_code=400,
                detail=f"Option '{option_name}' is not available for this menu item"
            )

    # Create updated cart item model
    item_data = CartItemModel(
        menu_item_id=updated_item.menu_item_id,
        quantity=updated_item.quantity,
        selected_options=updated_item.selected_options,
        special_instructions=updated_item.special_instructions,
        total_price=calculate_item_total(
            menu_item["price"],
            updated_item.quantity,
            updated_item.selected_options,
            available_options
        )
    )

    # Update cart
    cart_model = CartModel(**cart)
    cart_model.items[item_index] = item_data
    cart_model.total_amount = sum(item.total_price for item in cart_model.items)
    cart_model.updated_at = datetime.now(UTC)
    
    result = cart_collection.find_one_and_update(
        {"_id": cart["_id"]},
        {"$set": cart_model.model_dump(exclude={"id"})},
        return_document=ReturnDocument.AFTER
    )
    return {**result, "id": str(result["_id"])}

@router.delete("/items/{item_id}")
async def remove_from_cart(
    item_id: str,
    collections: dict = Depends(get_collections)
):
    cart_collection = collections["carts"]
    cart = cart_collection.find_one(sort=[("created_at", -1)])
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    # Remove the item from the cart
    cart_model = CartModel(**cart)
    cart_model.items = [item for item in cart_model.items if item.menu_item_id != item_id]
    cart_model.total_amount = sum(item.total_price for item in cart_model.items)
    cart_model.updated_at = datetime.now(UTC)
    
    cart_collection.find_one_and_update(
        {"_id": cart["_id"]},
        {"$set": cart_model.model_dump(exclude={"id"})}
    )
    return {"message": "Item removed from cart"}

@router.delete("/")
async def clear_cart(collections: dict = Depends(get_collections)):
    cart_collection = collections["carts"]
    cart = cart_collection.find_one(sort=[("created_at", -1)])
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
        
    result = cart_collection.delete_one({"_id": cart["_id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Cart not found")
        
    return {"message": "Cart cleared successfully"}