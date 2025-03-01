from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, UTC

class CartItemModel(BaseModel):
    id: str  # MongoDB ObjectId
    menu_item_id: str
    quantity: int
    special_instructions: Optional[str]

class CartModel(BaseModel):
    id: str  # MongoDB ObjectId
    items: List[CartItemModel]
    created_at: datetime = datetime.now(UTC)
    updated_at: datetime = datetime.now(UTC) 