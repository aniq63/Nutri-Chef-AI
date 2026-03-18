from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import List, Optional
from datetime import datetime


#---------- User Authentication-------------
class UserCreate(BaseModel):
    """Schema for user registration."""
    name: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=6)
    email: EmailStr


class LoginUser(BaseModel):
    """Schema for user login."""
    name: str
    password: str

class UserResponse(BaseModel):
    """Response model for user data."""
    user_id: int
    name: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """Response model for login token."""
    access_token: str
    token_type: str



