"""
Message model for individual chat messages
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Literal
from datetime import datetime
from bson import ObjectId


class MessageBase(BaseModel):
    """Base message model"""
    conversation_id: str
    role: Literal["user", "assistant", "system"]
    content: str
    tokens: Optional[int] = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MessageCreate(BaseModel):
    """Message creation model"""
    message: str


class MessageInDB(MessageBase):
    """Message model as stored in database"""
    id: str = Field(alias="_id")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}


class MessageResponse(BaseModel):
    """Message response model"""
    id: str
    conversation_id: str
    role: str
    content: str
    tokens: int
    timestamp: datetime
    metadata: Dict[str, Any]
    
    class Config:
        from_attributes = True
