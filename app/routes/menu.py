# app/routes/menu.py
from fastapi import APIRouter, HTTPException, status
from typing import List
from models.menu import MenuItem


import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database import AtlasClient
from config import Settings

router = APIRouter()
atlas_client = AtlasClient.get_instance(
    atlas_uri=Settings.ATLAS_URI,
    dbname=Settings.DB_NAME
)

@router.get("/", response_model=List[MenuItem])
def read_menu():
    items = atlas_client.find(collection_name="menu")
    return items

# @router.get("/{item_id}", response_model=MenuItemResponse)
# async def read_menu_item(item_id: str):
#     item = await get_menu_item_by_id(item_id)
#     if not item:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
#     return item

# @router.post("/", response_model=MenuItemResponse)
# async def add_menu_item(item: MenuItemCreate):
#     new_item = await create_menu_item(item.dict())
#     return new_item

# @router.put("/{item_id}", response_model=MenuItemResponse)
# async def update_menu_item_endpoint(item_id: str, item: MenuItemUpdate):
#     updated_item = await update_menu_item(item_id, item.dict())
#     if not updated_item:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
#     return updated_item

# @router.delete("/{item_id}")
# async def delete_menu_item_endpoint(item_id: str):
#     deleted_count = await delete_menu_item(item_id)
#     if not deleted_count:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
#     return {"message": "Item deleted successfully"}
