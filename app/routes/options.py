from fastapi import APIRouter, HTTPException
from database import get_database
from schemas.option import OptionCreate, OptionUpdate, OptionResponse
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError
from bson import ObjectId  # Import ObjectId to handle MongoDB IDs
from typing import List

router = APIRouter()
db = get_database()
options_collection = db["options"]

# ✅ Ensure name uniqueness in MongoDB
options_collection.create_index("name", unique=True)

# ✅ Get all options
@router.get("/", response_model=List[OptionResponse])
async def get_options():
    options = list(options_collection.find())
    return [{**opt, "id": str(opt["_id"])} for opt in options]

# ✅ Get a specific option by its ID
@router.get("/{option_id}", response_model=OptionResponse)
async def get_option(option_id: str):
    try:
        # Convert string ID to ObjectId for MongoDB query
        option = options_collection.find_one({"_id": ObjectId(option_id)})
        if not option:
            raise HTTPException(status_code=404, detail="Option not found")
        return OptionResponse(**option, id=str(option["_id"]))
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid option ID")

# ✅ Create a new option (Ensures unique name)
@router.post("/", response_model=OptionResponse)
async def create_option(option: OptionCreate):
    try:
        result = options_collection.insert_one(option.model_dump())
        return OptionResponse(**option.model_dump(), id=str(result.inserted_id))
    except DuplicateKeyError:
        raise HTTPException(status_code=400, detail="Option name must be unique")

# ✅ Update an existing option (Using `OptionUpdate`)
@router.put("/options/{option_id}", response_model=OptionResponse)
async def update_option(option_id: str, updated_option: OptionUpdate):
    update_data = {k: v for k, v in updated_option.model_dump().items() if v is not None}

    if not update_data:
        raise HTTPException(status_code=400, detail="No valid fields to update")

    result = options_collection.find_one_and_update(
        {"_id": ObjectId(option_id)},
        {"$set": update_data},
        return_document=ReturnDocument.AFTER
    )

    if not result:
        raise HTTPException(status_code=404, detail="Option not found")

    return OptionResponse(**result, id=str(result["_id"]))

# ✅ Delete an option by ID
@router.delete("/{option_id}")
async def delete_option(option_id: str):
    try:
        # Convert string ID to ObjectId for MongoDB
        result = options_collection.delete_one({"_id": ObjectId(option_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Option not found")
        
        return {"message": "Option deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid option ID")
