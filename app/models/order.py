from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, UTC
from ..schemas.order import OrderStatus

class OrderItemModel(BaseModel):
    id: str  # MongoDB ObjectId
    menu_item_id: str
    name: str
    price: float
    quantity: int
    special_instructions: Optional[str]

class OrderModel(BaseModel):
    id: str  # MongoDB ObjectId
    order_number: str
    items: List[OrderItemModel]
    total_amount: float
    status: OrderStatus
    created_at: datetime = datetime.now(UTC)
    updated_at: datetime = datetime.now(UTC)