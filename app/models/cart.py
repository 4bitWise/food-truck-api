from typing import List, Optional
from datetime import datetime, UTC
from pydantic import BaseModel, Field

class CartItemModel(BaseModel):
    menu_item_id: str
    quantity: int
    selected_options: List[str]
    special_instructions: Optional[str] = None
    total_price: float  # Calculated server-side

class CartModel(BaseModel):
    id: Optional[str] = None
    items: List[CartItemModel]
    total_amount: float
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC)) 