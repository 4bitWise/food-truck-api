from fastapi import APIRouter, HTTPException, Depends
from typing import List
from bson import ObjectId
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError
from database import get_collections
from schemas.option import OptionCreate, OptionUpdate, OptionResponse

router = APIRouter()

# Get all options
@router.get("/", response_model=List[OptionResponse])
async def get_options(collections: dict = Depends(get_collections)):
    options_collection = collections["options"]
    options = list(options_collection.find())
    return [{**option, "id": str(option["_id"])} for option in options]

# Get a specific option by its ID
@router.get("/{option_id}", response_model=OptionResponse)
async def get_option(
    option_id: str,
    collections: dict = Depends(get_collections)
):
    options_collection = collections["options"]
    try:
        # Convert string ID to ObjectId for MongoDB query
        option = options_collection.find_one({"_id": ObjectId(option_id)})
        if not option:
            raise HTTPException(status_code=404, detail="Option not found")
        return OptionResponse(**option, id=str(option["_id"]))
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid option ID")

# Create a new option (Ensures unique name)
@router.post("/", response_model=OptionResponse)
async def create_option(
    option: OptionCreate,
    collections: dict = Depends(get_collections)
):
    options_collection = collections["options"]
    try:
        result = options_collection.insert_one(option.model_dump())
        return OptionResponse(**option.model_dump(), id=str(result.inserted_id))
    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail=f"An option with the name '{option.name}' already exists")

# Update an existing option (Using `OptionUpdate`)
@router.put("/{option_id}", response_model=OptionResponse)
async def update_option(
    option_id: str,
    updated_option: OptionUpdate,
    collections: dict = Depends(get_collections)
):
    options_collection = collections["options"]
    update_data = {k: v for k, v in updated_option.model_dump().items() if v is not None}

    if not update_data:
        raise HTTPException(status_code=400, detail="No valid fields to update")

    try:
        result = options_collection.find_one_and_update(
            {"_id": ObjectId(option_id)},
            {"$set": update_data},
            return_document=ReturnDocument.AFTER
        )

        if not result:
            raise HTTPException(status_code=404, detail="Option not found")

        return OptionResponse(**result, id=str(result["_id"]))
    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail=f"An option with the name '{updated_option.name}' already exists")
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid option ID")

# Delete an option by ID (only if not used in any menu items)
@router.delete("/{option_id}")
async def delete_option(
    option_id: str,
    collections: dict = Depends(get_collections)
):
    options_collection = collections["options"]
    menu_collection = collections["menu"]

    try:
        # Check if option is used in any menu items
        option = options_collection.find_one({"_id": ObjectId(option_id)})
        if not option:
            raise HTTPException(status_code=404, detail="Option not found")

        # Check if any menu items use this option
        menu_items_with_option = menu_collection.find_one({"options": option["name"]})
        if menu_items_with_option:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete option as it is being used in menu items"
            )

        # Delete the option if it's not being used
        result = options_collection.delete_one({"_id": ObjectId(option_id)})
        return {"message": "Option deleted successfully"}

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid option ID")
