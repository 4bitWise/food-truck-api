from pydantic import BaseModel, Field
from typing import List, Optional

# ✅ Schema for creating a menu item (Referencing options by name)
class MenuItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    price: float = Field(..., gt=0)
    available: bool = True
    options: List[str] = []  # 🔥 Storing option names only

# ✅ Schema for updating a menu item
class MenuItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    price: Optional[float] = Field(None, gt=0)
    available: Optional[bool] = None
    options: Optional[List[str]] = None  # 🔥 Storing option names only

# ✅ Schema for responding with a menu item
class MenuItemResponse(MenuItemCreate):
    id: str