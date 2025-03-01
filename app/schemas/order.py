from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, UTC
from enum import Enum

class OrderStatus(str, Enum):
    PENDING = "pending"
    IN_PREPARATION = "en préparation"
    READY = "prête"
    DELIVERED = "livrée"
    CANCELLED = "annulée"

class OrderItem(BaseModel):
    menu_item_id: str = Field(..., description="ID of the menu item")
    name: str = Field(..., description="Name of the menu item")
    price: float = Field(..., description="Price of the menu item")
    quantity: int = Field(..., gt=0, description="Quantity ordered")
    special_instructions: Optional[str] = None

class Order(BaseModel):
    id: Optional[str] = None
    order_number: str = Field(..., description="Unique order number")
    items: List[OrderItem] = Field(..., description="List of items in the order")
    total_amount: float = Field(..., description="Total amount of the order")
    status: OrderStatus = Field(default=OrderStatus.PENDING)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Config:
        json_schema_extra = {
            "example": {
                "order_number": "FT-2024-0001",
                "items": [
                    {
                        "menu_item_id": "item123",
                        "name": "Burger",
                        "price": 9.99,
                        "quantity": 2,
                        "special_instructions": "No onions"
                    }
                ],
                "total_amount": 19.98,
                "status": "pending"
            }
        } 