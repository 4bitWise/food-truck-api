from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, UTC
from schemas.order import OrderStatus

class OrderItemModel(BaseModel):
    menu_item_id: str
    quantity: int
    selected_options: List[str]
    special_instructions: Optional[str] = None
    total_price: float  # Calculated server-side

class OrderModel(BaseModel):
    id: Optional[str] = None
    order_number: str
    items: List[OrderItemModel]
    total_amount: float
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))