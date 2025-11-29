"""
RAG (Retrieval-Augmented Generation) service for document-based conversations
"""
from typing import List, Dict, Any, Optional
import re

from app.config import settings
from app.utils.logger import setup_logger
from app.utils.token_counter import count_tokens
from app.models.document import DocumentChunk

logger = setup_logger(__name__)


class RAGService:
    """Service for RAG operations"""
    
    def __init__(self):
        self.chunk_size = settings.CHUNK_SIZE
        self.chunk_overlap = settings.CHUNK_OVERLAP
        self.max_chunks_per_query = settings.MAX_CHUNKS_PER_QUERY
    
    def chunk_document(self, content: str, filename: str) -> List[DocumentChunk]:
        """
        Split document into chunks for retrieval
        
        Args:
            content: Document text content
            filename: Original filename
        
        Returns:
            List of document chunks
        """
        # Simple chunking by character count with overlap
        chunks = []
        chunk_id = 0
        start = 0
        
        while start < len(content):
            end = min(start + self.chunk_size, len(content))
            
            # Try to break at sentence boundary
            if end < len(content):
                # Look for sentence ending
                sentence_end = content.rfind('.', start, end)
                if sentence_end > start + self.chunk_size // 2:
                    end = sentence_end + 1
            
            chunk_text = content[start:end].strip()
            
            if chunk_text:
                chunk = DocumentChunk(
                    chunk_id=chunk_id,
                    content=chunk_text,
                    start_char=start,
                    end_char=end,
                    tokens=count_tokens(chunk_text)
                )
                chunks.append(chunk)
                chunk_id += 1
            
            # Move start position with overlap
            start = end - self.chunk_overlap
            if start >= len(content):
                break
        
        logger.info(f"Document '{filename}' split into {len(chunks)} chunks")
        return chunks
    
    def retrieve_relevant_chunks(
        self,
        query: str,
        document_chunks: List[DocumentChunk],
        max_chunks: Optional[int] = None
    ) -> List[DocumentChunk]:
        """
        Retrieve relevant chunks for a query using simple keyword matching
        
        Args:
            query: User query
            document_chunks: List of document chunks
            max_chunks: Maximum number of chunks to return
        
        Returns:
            List of relevant chunks sorted by relevance
        """
        if not document_chunks:
            return []
        
        max_chunks = max_chunks or self.max_chunks_per_query
        
        # Simple keyword-based retrieval
        query_words = set(re.findall(r'\w+', query.lower()))
        
        # Score each chunk
        scored_chunks = []
        for chunk in document_chunks:
            chunk_words = set(re.findall(r'\w+', chunk.content.lower()))
            
            # Calculate overlap score
            overlap = len(query_words & chunk_words)
            score = overlap / len(query_words) if query_words else 0
            
            scored_chunks.append((score, chunk))
        
        # Sort by score and return top chunks
        scored_chunks.sort(reverse=True, key=lambda x: x[0])
        relevant_chunks = [chunk for score, chunk in scored_chunks[:max_chunks] if score > 0]
        
        logger.info(f"Retrieved {len(relevant_chunks)} relevant chunks for query")
        return relevant_chunks
    
    def build_rag_context(
        self,
        query: str,
        chunks: List[DocumentChunk]
    ) -> str:
        """
        Build context string from retrieved chunks
        
        Args:
            query: User query
            chunks: Retrieved document chunks
        
        Returns:
            Formatted context string
        """
        if not chunks:
            return ""
        
        context_parts = ["Here is relevant information from the documents:\n"]
        
        for i, chunk in enumerate(chunks, 1):
            context_parts.append(f"\n[Document Excerpt {i}]")
            context_parts.append(chunk.content)
            context_parts.append("")
        
        context_parts.append("\nBased on the above information, please answer the following question:")
        context_parts.append(query)
        
        return "\n".join(context_parts)
    
    def create_rag_messages(
        self,
        query: str,
        chunks: List[DocumentChunk],
        conversation_history: List[Dict[str, str]] = None
    ) -> List[Dict[str, str]]:
        """
        Create message list for RAG-based conversation
        
        Args:
            query: User query
            chunks: Retrieved document chunks
            conversation_history: Previous conversation messages
        
        Returns:
            List of messages for LLM
        """
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant that answers questions based on the provided document excerpts. "
                          "Always cite the information from the documents when answering. "
                          "If the answer is not in the documents, say so clearly."
            }
        ]
        
        # Add conversation history if available
        if conversation_history:
            messages.extend(conversation_history)
        
        # Add RAG context
        rag_context = self.build_rag_context(query, chunks)
        messages.append({
            "role": "user",
            "content": rag_context
        })
        
        return messages


# Global RAG service instance
rag_service = RAGService()
