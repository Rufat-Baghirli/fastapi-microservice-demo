from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from typing import Optional


# Base class for all user models
class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    is_active: bool = True  # Indicates whether the user account is active


# Class for creating a new user
class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


# Class for updating user information
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    password: Optional[str] = Field(None, min_length=6)
    is_active: Optional[bool] = None


# Class for displaying user information in API responses
class UserOut(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Class for changing user password
class UserChangePassword(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6)