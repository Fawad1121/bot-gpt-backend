"""
User model for authentication and user management
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any
from datetime import datetime
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic"""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")


class UserBase(BaseModel):
    """Base user model"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class UserCreate(UserBase):
    """User creation model"""
    pass


class UserInDB(UserBase):
    """User model as stored in database"""
    id: str = Field(alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}


class UserResponse(BaseModel):
    """User response model"""
    id: str
    username: str
    email: str
    created_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        from_attributes = True
