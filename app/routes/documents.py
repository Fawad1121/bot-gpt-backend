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
    Upload a document for RAG - saves to disk and starts background processing
    
    Args:
        file: Document file (text, PDF, etc.)
        user_id: User ID
    
    Returns:
        Document ID and file info
    """
    try:
        import os
        from pathlib import Path
        from bson import ObjectId
        from app.services.vectorization_queue import vectorization_queue
        
        # Generate document ID
        document_id = str(ObjectId())
        
        # Create upload directory structure: uploads/{user_id}/{document_id}/
        upload_dir = Path("uploads") / user_id / document_id
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Save file to disk
        file_path = upload_dir / file.filename
        
        logger.info(f"Saving file to: {file_path}")
        
        # Read and save file
        content = await file.read()
        file_size = len(content)
        
        # Write to disk
        with open(file_path, "wb") as f:
            f.write(content)
        
        logger.info(f"File saved successfully: {file_path} ({file_size} bytes)")
        
        # Store document metadata (chunking will happen in background)
        document_data = {
            "_id": ObjectId(document_id),
            "user_id": user_id,
            "filename": file.filename,
            "file_path": str(file_path),
            "file_size": file_size,
            "content_type": file.content_type,
            "total_chunks": 0,  # Will be set after chunking
            "vectorized_chunks": 0,
            "is_vectorized": False,
            "metadata": {
                "original_filename": file.filename,
                "upload_status": "completed",
                "processing_status": "pending"  # chunking + vectorization
            }
        }
        
        await db_service.db.documents.insert_one(document_data)
        
        logger.info(f"Document metadata saved to DB with ID: {document_id}")
        
        # Start background processing (chunking + vectorization)
        vectorization_queue.start_vectorization(document_id)
        logger.info(f"Started background processing for document: {document_id}")
        
        # Return immediately - processing happens in background
        return DocumentUploadResponse(
            document_id=document_id,
            filename=file.filename,
            chunks=0  # Will be set after chunking
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
