from fastapi import APIRouter, HTTPException, Depends
from typing import List
from bson import ObjectId
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError
from database import get_collections
from schemas.menu import MenuItemCreate, MenuItemUpdate, MenuItemResponse
from schemas.option import OptionResponse

router = APIRouter()

# Check if option names exist in the database
async def validate_option_names(option_names: List[str], collections: dict) -> None:
    options_collection = collections["options"]
    existing_options = options_collection.find({"name": {"$in": option_names}})
    existing_option_names = {opt["name"] for opt in existing_options}

    missing_options = [name for name in option_names if name not in existing_option_names]
    
    if missing_options:
        raise HTTPException(status_code=400, detail=f"Option(s) not found: {', '.join(missing_options)}")

# Get all menu items
@router.get("/", response_model=List[MenuItemResponse])
async def get_menu_items(collections: dict = Depends(get_collections)):
    menu_collection = collections["menu"]
    menu_items = list(menu_collection.find())
    return [{**item, "id": str(item["_id"])} for item in menu_items]

# Create a new menu item (Ensures unique name and valid option names)
@router.post("/", response_model=MenuItemResponse)
async def create_menu_item(
    menu_item: MenuItemCreate,
    collections: dict = Depends(get_collections)
):
    menu_collection = collections["menu"]
    # Validate that all options in the menu item exist
    await validate_option_names(menu_item.options, collections)

    try:
        result = menu_collection.insert_one(menu_item.model_dump())
        return MenuItemResponse(**menu_item.model_dump(), id=str(result.inserted_id))
    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail=f"A menu item with the name '{menu_item.name}' already exists")

# Update an existing menu (Validates option names)
@router.put("/{menu_item_id}", response_model=MenuItemResponse)
async def update_menu(
    menu_item_id: str,
    updated_menu_item: MenuItemUpdate,
    collections: dict = Depends(get_collections)
):
    menu_collection = collections["menu"]
    update_data = {k: v for k, v in updated_menu_item.model_dump().items() if v is not None}

    if not update_data:
        raise HTTPException(status_code=400, detail="No valid fields to update")

    if "options" in update_data:
        await validate_option_names(update_data["options"], collections)

    try:
        result = menu_collection.find_one_and_update(
            {"_id": ObjectId(menu_item_id)},
            {"$set": update_data},
            return_document=ReturnDocument.AFTER
        )

        if not result:
            raise HTTPException(status_code=404, detail="Menu not found")

        return MenuItemResponse(**result, id=str(result["_id"]))
    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail=f"A menu item with the name '{updated_menu_item.name}' already exists")
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid menu item ID")

# Get a specific menu item by ID
@router.get("/{menu_item_id}", response_model=MenuItemResponse)
async def get_menu_item(
    menu_item_id: str,
    collections: dict = Depends(get_collections)
):
    menu_collection = collections["menu"]
    try:
        menu_item = menu_collection.find_one({"_id": ObjectId(menu_item_id)})
        if not menu_item:
            raise HTTPException(status_code=404, detail="Menu item not found")
        return MenuItemResponse(**menu_item, id=str(menu_item["_id"]))
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid menu item ID")

# Delete a menu item by ID
@router.delete("/{menu_item_id}")
async def delete_menu_item(
    menu_item_id: str,
    collections: dict = Depends(get_collections)
):
    menu_collection = collections["menu"]
    try:
        result = menu_collection.delete_one({"_id": ObjectId(menu_item_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Menu item not found")
        
        return {"message": "Menu item deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid menu item ID")
