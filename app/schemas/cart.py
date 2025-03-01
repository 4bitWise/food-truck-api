from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class CartItem(BaseModel):
    menu_item_id: str = Field(..., description="ID of the menu item")
    quantity: int = Field(default=1, gt=0, description="Quantity of the item")
    special_instructions: Optional[str] = Field(default=None, description="Special instructions for the item")

class Cart(BaseModel):
    id: Optional[str] = None
    items: List[CartItem] = Field(default_factory=list, description="List of items in the cart")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "items": [
                    {
                        "menu_item_id": "item123",
                        "quantity": 2,
                        "special_instructions": "Extra spicy"
                    }
                ]
            }
        } 