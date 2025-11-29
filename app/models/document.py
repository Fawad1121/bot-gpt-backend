"""
Document model for RAG (Retrieval-Augmented Generation)
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId


class DocumentChunk(BaseModel):
    """Individual document chunk"""
    chunk_id: int
    content: str
    start_char: int
    end_char: int
    tokens: int = 0


class DocumentBase(BaseModel):
    """Base document model"""
    user_id: str
    filename: str
    content: str
    chunks: List[DocumentChunk] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DocumentCreate(BaseModel):
    """Document creation model"""
    user_id: str
    filename: str
    content: str


class DocumentInDB(DocumentBase):
    """Document model as stored in database"""
    id: str = Field(alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    file_size: int = 0
    chunk_count: int = 0
    
    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}


class DocumentResponse(BaseModel):
    """Document response model"""
    id: str
    user_id: str
    filename: str
    created_at: datetime
    file_size: int
    chunk_count: int
    metadata: Dict[str, Any]
    
    class Config:
        from_attributes = True


class DocumentUploadResponse(BaseModel):
    """Response after document upload"""
    document_id: str
    filename: str
    chunks: int
    message: str = "Document uploaded and processed successfully"
