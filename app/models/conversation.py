"""
Conversation model for managing chat sessions
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from bson import ObjectId


class ConversationBase(BaseModel):
    """Base conversation model"""
    user_id: str
    title: Optional[str] = None
    mode: Literal["open_chat", "rag_mode"] = "open_chat"
    document_ids: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConversationCreate(BaseModel):
    """Conversation creation model"""
    user_id: str
    message: str
    mode: Literal["open_chat", "rag_mode"] = "open_chat"
    document_ids: Optional[List[str]] = Field(default_factory=list)


class ConversationInDB(ConversationBase):
    """Conversation model as stored in database"""
    id: str = Field(alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    message_count: int = 0
    total_tokens: int = 0
    
    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}


class ConversationResponse(BaseModel):
    """Conversation response model"""
    id: str
    user_id: str
    title: Optional[str]
    mode: str
    document_ids: List[str]
    created_at: datetime
    updated_at: datetime
    message_count: int
    total_tokens: int
    metadata: Dict[str, Any]
    
    class Config:
        from_attributes = True


class ConversationWithMessages(ConversationResponse):
    """Conversation with full message history"""
    messages: List[Any] = Field(default_factory=list)  # Will be List[MessageResponse]
