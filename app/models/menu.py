#!/usr/bin/env python3.12

from typing import List, Optional
from pydantic import BaseModel

    
class MenuItem(BaseModel):
    id: int
    name: str
    price: float
    available: bool = True
    options: List[str] = []