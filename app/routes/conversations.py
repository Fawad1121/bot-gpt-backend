"""
Conversation API routes
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List

from app.models.conversation import (
    ConversationCreate,
    ConversationResponse,
    ConversationWithMessages
)
from app.models.message import MessageCreate, MessageResponse
from app.services.database import db_service
from app.services.conversation_service import conversation_service
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter(prefix="/api/v1/conversations", tags=["conversations"])


@router.post("", response_model=dict, status_code=201)
async def create_conversation(conversation: ConversationCreate):
    """
    Create a new conversation with the first message
    
    Args:
        conversation: Conversation creation data
    
    Returns:
        Conversation ID and assistant's first response
    """
    try:
        conv, user_msg, assistant_msg = await conversation_service.create_conversation_with_message(
            user_id=conversation.user_id,
            message=conversation.message,
            mode=conversation.mode,
            document_ids=conversation.document_ids
        )
        
        return {
            "conversation_id": conv["_id"],
            "title": conv["title"],
            "mode": conv["mode"],
            "user_message": {
                "id": user_msg["id"],
                "content": user_msg["content"],
                "timestamp": user_msg["timestamp"]
            },
            "assistant_message": {
                "id": assistant_msg["id"],
                "content": assistant_msg["content"],
                "timestamp": assistant_msg["timestamp"]
            }
        }
    
    except Exception as e:
        logger.error(f"Failed to create conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create conversation: {str(e)}")


@router.get("", response_model=dict)
async def list_conversations(
    user_id: str = Query(..., description="User ID"),
    limit: int = Query(20, ge=1, le=100, description="Number of conversations to return"),
    offset: int = Query(0, ge=0, description="Number of conversations to skip")
):
    """
    List all conversations for a user
    
    Args:
        user_id: User ID
        limit: Maximum number of conversations to return
        offset: Number of conversations to skip (for pagination)
    
    Returns:
        List of conversations with pagination info
    """
    try:
        conversations, total = await db_service.list_conversations(user_id, limit, offset)
        
        return {
            "conversations": conversations,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total
        }
    
    except Exception as e:
        logger.error(f"Failed to list conversations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list conversations: {str(e)}")


@router.get("/{conversation_id}", response_model=dict)
async def get_conversation(conversation_id: str):
    """
    Get a conversation with full message history
    
    Args:
        conversation_id: Conversation ID
    
    Returns:
        Conversation with all messages
    """
    try:
        conversation = await db_service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        messages = await db_service.get_messages(conversation_id)
        
        return {
            "conversation": conversation,
            "messages": messages
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get conversation: {str(e)}")


@router.post("/{conversation_id}/messages", response_model=dict, status_code=201)
async def add_message(conversation_id: str, message: MessageCreate):
    """
    Add a new message to an existing conversation
    
    Args:
        conversation_id: Conversation ID
        message: Message data
    
    Returns:
        User message and assistant response
    """
    try:
        user_msg, assistant_msg = await conversation_service.add_message_to_conversation(
            conversation_id,
            message.message
        )
        
        return {
            "user_message": user_msg,
            "assistant_message": assistant_msg
        }
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to add message: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add message: {str(e)}")


@router.delete("/{conversation_id}", response_model=dict)
async def delete_conversation(conversation_id: str):
    """
    Delete a conversation and all its messages
    
    Args:
        conversation_id: Conversation ID
    
    Returns:
        Deletion confirmation
    """
    try:
        deleted = await db_service.delete_conversation(conversation_id)
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return {
            "deleted": True,
            "conversation_id": conversation_id,
            "message": "Conversation and all messages deleted successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete conversation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete conversation: {str(e)}")
