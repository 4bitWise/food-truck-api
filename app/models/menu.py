from pydantic import BaseModel
from typing import List, Optional

class MenuItemModel(BaseModel):
    id: str  # ObjectId de MongoDB
    name: str
    description: Optional[str]
    price: float
    available: bool
    options: List[str]  # Liste des ObjectId des options
