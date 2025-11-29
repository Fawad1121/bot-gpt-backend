"""
Conversation management service
"""
from typing import List, Dict, Any, Optional, Tuple

from app.services.database import db_service
from app.services.llm_service import llm_service
from app.services.rag_service import rag_service
from app.utils.logger import setup_logger
from app.models.message import MessageResponse
from app.models.conversation import ConversationResponse

logger = setup_logger(__name__)


class ConversationService:
    """Service for managing conversations and message flow"""
    
    async def create_conversation_with_message(
        self,
        user_id: str,
        message: str,
        mode: str = "open_chat",
        document_ids: Optional[List[str]] = None
    ) -> Tuple[ConversationResponse, MessageResponse, MessageResponse]:
        """
        Create a new conversation with the first message and get LLM response
        
        Args:
            user_id: User ID
            message: First user message
            mode: Conversation mode ('open_chat' or 'rag_mode')
            document_ids: List of document IDs for RAG mode
        
        Returns:
            Tuple of (conversation, user_message, assistant_message)
        """
        # Generate conversation title
        title = await llm_service.generate_title(message)
        
        # Create conversation
        conversation_data = {
            "user_id": user_id,
            "title": title,
            "mode": mode,
            "document_ids": document_ids or [],
            "metadata": {}
        }
        
        conversation_id = await db_service.create_conversation(conversation_data)
        logger.info(f"Created conversation {conversation_id} for user {user_id}")
        
        # Add user message and get response
        user_msg, assistant_msg = await self.add_message_to_conversation(
            conversation_id,
            message
        )
        
        # Get full conversation
        conversation = await db_service.get_conversation(conversation_id)
        
        return conversation, user_msg, assistant_msg
    
    async def add_message_to_conversation(
        self,
        conversation_id: str,
        message: str
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Add a user message to conversation and get LLM response
        
        Args:
            conversation_id: Conversation ID
            message: User message
        
        Returns:
            Tuple of (user_message, assistant_message)
        """
        # Get conversation
        conversation = await db_service.get_conversation(conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        # Get conversation history
        history_messages = await db_service.get_messages(conversation_id)
        
        # Create user message
        user_message_data = {
            "conversation_id": conversation_id,
            "role": "user",
            "content": message,
            "tokens": 0,  # Will be calculated
            "metadata": {}
        }
        
        user_message_id = await db_service.create_message(user_message_data)
        user_message = await self._get_message_dict(user_message_id)
        
        # Prepare messages for LLM
        llm_messages = await self._prepare_llm_messages(
            conversation,
            history_messages,
            message
        )
        
        # Get LLM response
        try:
            response_text, total_tokens = await llm_service.generate_response(llm_messages)
            
            # Create assistant message
            assistant_message_data = {
                "conversation_id": conversation_id,
                "role": "assistant",
                "content": response_text,
                "tokens": total_tokens,
                "metadata": {
                    "model": llm_service.model,
                    "mode": conversation["mode"]
                }
            }
            
            assistant_message_id = await db_service.create_message(assistant_message_data)
            assistant_message = await self._get_message_dict(assistant_message_id)
            
            logger.info(f"Added message pair to conversation {conversation_id}")
            
            return user_message, assistant_message
            
        except Exception as e:
            logger.error(f"Failed to generate LLM response: {e}")
            
            # Create error message
            error_message_data = {
                "conversation_id": conversation_id,
                "role": "assistant",
                "content": "I apologize, but I'm temporarily unable to respond. Please try again in a moment.",
                "tokens": 0,
                "metadata": {"error": str(e)}
            }
            
            error_message_id = await db_service.create_message(error_message_data)
            error_message = await self._get_message_dict(error_message_id)
            
            return user_message, error_message
    
    async def _prepare_llm_messages(
        self,
        conversation: Dict[str, Any],
        history_messages: List[Dict[str, Any]],
        current_message: str
    ) -> List[Dict[str, str]]:
        """
        Prepare messages for LLM based on conversation mode
        
        Args:
            conversation: Conversation data
            history_messages: Previous messages
            current_message: Current user message
        
        Returns:
            List of messages for LLM
        """
        mode = conversation["mode"]
        
        if mode == "rag_mode":
            # RAG mode: use vector similarity search
            document_ids = conversation.get("document_ids", [])
            
            logger.info(f"RAG Mode: Processing with {len(document_ids)} documents")
            
            if document_ids:
                # Check if all documents are vectorized
                all_chunks = []
                for doc_id in document_ids:
                    document = await db_service.get_document(doc_id)
                    if not document:
                        logger.warning(f"Document not found: {doc_id}")
                        continue
                    
                    logger.info(f"Document {doc_id}: is_vectorized={document.get('is_vectorized', False)}, "
                               f"total_chunks={document.get('total_chunks', 0)}, "
                               f"vectorized_chunks={document.get('vectorized_chunks', 0)}")
                    
                    # Check vectorization status
                    if not document.get("is_vectorized", False):
                        raise ValueError(
                            "Please try again after some time, we are processing your file. "
                            "Document vectorization is in progress."
                        )
                    
                    # Get vectorized chunks from chunks collection
                    chunks_cursor = db_service.db.chunks.find({
                        "document_id": doc_id,
                        "is_vectorized": True
                    })
                    chunks = await chunks_cursor.to_list(length=None)
                    
                    logger.info(f"Retrieved {len(chunks)} vectorized chunks for document {doc_id}")
                    
                    if chunks:
                        all_chunks.extend(chunks)
                
                logger.info(f"Total chunks retrieved: {len(all_chunks)}")
                
                if not all_chunks:
                    raise ValueError("No vectorized chunks found in documents")
                
                # Generate query embedding
                from app.services.embedding_service import embedding_service
                logger.info(f"Generating query embedding for: {current_message[:100]}...")
                query_embedding = embedding_service.generate_embedding(current_message)
                logger.info(f"Query embedding generated: {len(query_embedding)} dimensions")
                
                # Find most similar chunks using vector similarity
                relevant_chunks = rag_service.vector_similarity_search(
                    query_embedding,
                    all_chunks
                )
                
                logger.info(f"Selected {len(relevant_chunks)} most relevant chunks")
                logger.info("=" * 80)
                logger.info("CHUNKS BEING SENT TO LLM:")
                for i, chunk in enumerate(relevant_chunks):
                    logger.info(f"\n[Chunk {i+1}]")
                    logger.info(f"Content: {chunk['content'][:200]}...")
                logger.info("=" * 80)
                
                # Build conversation history
                history = [
                    {"role": msg["role"], "content": msg["content"]}
                    for msg in history_messages[-10:]  # Keep last 10 messages
                ]
                
                # Create RAG messages with relevant chunks
                from app.models.document import DocumentChunk
                chunk_objects = [
                    DocumentChunk(
                        chunk_id=c["chunk_id"],
                        content=c["content"],
                        start_char=c.get("start_char", 0),
                        end_char=c.get("end_char", 0),
                        tokens=c.get("tokens", 0)
                    )
                    for c in relevant_chunks
                ]
                
                return rag_service.create_rag_messages(
                    current_message,
                    chunk_objects,
                    history
                )
        
        # Open chat mode: standard conversation
        messages = [
            {
                "role": "system",
                "content": "You are a helpful, friendly AI assistant. Provide clear, accurate, and helpful responses."
            }
        ]
        
        # Add conversation history
        for msg in history_messages[-10:]:  # Keep last 10 messages
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # Add current message
        messages.append({
            "role": "user",
            "content": current_message
        })
        
        return messages
    
    async def _get_message_dict(self, message_id: str) -> Dict[str, Any]:
        """Get message as dictionary"""
        from bson import ObjectId
        message = await db_service.db.messages.find_one({"_id": ObjectId(message_id)})
        if message:
            message["_id"] = str(message["_id"])
            message["id"] = message["_id"]
        return message


# Global conversation service instance
conversation_service = ConversationService()
