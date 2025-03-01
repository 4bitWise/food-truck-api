from typing import Optional
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr = Field(..., description="User's email address")
    full_name: str = Field(..., description="User's full name")
    phone_number: str = Field(..., description="User's phone number")

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="User's password")

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(UserBase):
    id: Optional[str] = None
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "full_name": "John Doe",
                "phone_number": "+33612345678",
                "is_active": True
            }
        }

class UserResponse(User):
    """User model returned to clients (without sensitive data)"""
    pass 