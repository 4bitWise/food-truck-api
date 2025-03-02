from pydantic import BaseModel

class OptionModel(BaseModel):
    id: str  # ObjectId de MongoDB
    name: str
    price: float
