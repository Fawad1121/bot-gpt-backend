"""
Document API routes for RAG functionality
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from typing import List

from app.models.document import DocumentCreate, DocumentResponse, DocumentUploadResponse
from app.services.database import db_service
from app.services.rag_service import rag_service
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


@router.post("", response_model=DocumentUploadResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    user_id: str = Form(...)
):
    """
    Upload a document for RAG
    
    Args:
        file: Document file (text, PDF, etc.)
        user_id: User ID
    
    Returns:
        Document ID and processing info
    """
    try:
        # Read file content
        content = await file.read()
        
        # Decode content (assuming text file for now)
        try:
            text_content = content.decode('utf-8')
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=400,
                detail="Only UTF-8 text files are supported currently"
            )
        
        # Chunk the document
        chunks = rag_service.chunk_document(text_content, file.filename)
        
        # Create document in database
        document_data = {
            "user_id": user_id,
            "filename": file.filename,
            "content": text_content,
            "chunks": [chunk.dict() for chunk in chunks],
            "file_size": len(content),
            "chunk_count": len(chunks),
            "metadata": {
                "content_type": file.content_type,
                "original_filename": file.filename
            }
        }
        
        document_id = await db_service.create_document(document_data)
        
        logger.info(f"Document '{file.filename}' uploaded successfully with {len(chunks)} chunks")
        
        return DocumentUploadResponse(
            document_id=document_id,
            filename=file.filename,
            chunks=len(chunks)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload document: {str(e)}")


@router.get("", response_model=dict)
async def list_documents(
    user_id: str = Query(..., description="User ID"),
    limit: int = Query(20, ge=1, le=100, description="Number of documents to return"),
    offset: int = Query(0, ge=0, description="Number of documents to skip")
):
    """
    List all documents for a user
    
    Args:
        user_id: User ID
        limit: Maximum number of documents to return
        offset: Number of documents to skip (for pagination)
    
    Returns:
        List of documents with pagination info
    """
    try:
        documents, total = await db_service.list_documents(user_id, limit, offset)
        
        # Remove content and chunks from response (too large)
        for doc in documents:
            doc.pop("content", None)
            doc.pop("chunks", None)
        
        return {
            "documents": documents,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total
        }
    
    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")


@router.get("/{document_id}", response_model=dict)
async def get_document(document_id: str, include_content: bool = Query(False)):
    """
    Get document details
    
    Args:
        document_id: Document ID
        include_content: Whether to include full content (default: False)
    
    Returns:
        Document details
    """
    try:
        document = await db_service.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Remove content and chunks unless requested
        if not include_content:
            document.pop("content", None)
            document.pop("chunks", None)
        
        return document
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get document: {str(e)}")


@router.delete("/{document_id}", response_model=dict)
async def delete_document(document_id: str):
    """
    Delete a document
    
    Args:
        document_id: Document ID
    
    Returns:
        Deletion confirmation
    """
    try:
        deleted = await db_service.delete_document(document_id)
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {
            "deleted": True,
            "document_id": document_id,
            "message": "Document deleted successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")
