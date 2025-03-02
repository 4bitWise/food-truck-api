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
    quantity: int = Field(..., gt=0, description="Quantity ordered")
    selected_options: List[str] = Field(default_factory=list, description="Names of selected options")
    special_instructions: Optional[str] = None

class OrderResponse(BaseModel):
    id: str
    order_number: str
    items: List[OrderItem]
    total_amount: float
    status: OrderStatus
    created_at: datetime
    updated_at: datetime

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
                        "quantity": 2,
                        "selected_options": ["Extra Cheese", "Bacon"],
                        "special_instructions": "Well done"
                    }
                ],
                "total_amount": 25.97,
                "status": "pending"
            }
        } 