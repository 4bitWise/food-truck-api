from pydantic import BaseModel, Field
from typing import Optional

class OptionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    price: float = Field(..., gt=0)

class OptionUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None

class OptionResponse(OptionCreate):
    id: str


