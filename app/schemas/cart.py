from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, UTC

class CartItem(BaseModel):
    menu_item_id: str = Field(..., description="ID of the menu item")
    quantity: int = Field(default=1, gt=0, description="Quantity of the item")
    selected_options: List[str] = Field(default_factory=list, description="Names of selected options")
    special_instructions: Optional[str] = Field(default=None, description="Special instructions for the item")

class Cart(BaseModel):
    id: Optional[str] = None
    items: List[CartItem] = Field(default_factory=list, description="List of items in the cart")
    total_amount: float = Field(default=0, description="Total amount of all items including options")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Config:
        json_schema_extra = {
            "example": {
                "items": [
                    {
                        "menu_item_id": "item123",
                        "quantity": 2,
                        "selected_options": ["Extra Cheese", "Bacon"],
                        "special_instructions": "Well done"
                    }
                ]
            }
        } 