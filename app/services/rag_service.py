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
        Split document into chunks for retrieval (simple character-based)
        
        Args:
            content: Document text content
            filename: Original filename
        
        Returns:
            List of document chunks
        """
        content = content.strip()
        chunks = []
        chunk_id = 0
        start = 0
        
        while start < len(content):
            end = start + self.chunk_size
            
            # Try not to cut in the middle of a sentence
            if end < len(content):
                period_pos = content.rfind('.', start, end)
                newline_pos = content.rfind('\n', start, end)
                split_pos = max(period_pos, newline_pos)
                
                if split_pos != -1 and split_pos > start + (self.chunk_size * 0.5):
                    end = split_pos + 1
            
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
            
            start = end
        
        logger.info(f"Document '{filename}' split into {len(chunks)} chunks")
        return chunks
    
    async def load_and_chunk_from_file_async(self, file_path: str) -> List[DocumentChunk]:
        """
        Load document from disk and chunk it (async, non-blocking)
        
        Args:
            file_path: Path to document file on disk
        
        Returns:
            List of document chunks
        """
        import asyncio
        
        # Run blocking file I/O and chunking in thread pool
        loop = asyncio.get_running_loop()
        chunks = await loop.run_in_executor(
            None,
            self._load_and_chunk_sync,
            file_path
        )
        return chunks
    
    def _load_and_chunk_sync(self, file_path: str) -> List[DocumentChunk]:
        """
        Synchronous helper to load and chunk file (runs in thread pool)
        
        Args:
            file_path: Path to document file on disk
        
        Returns:
            List of document chunks
        """
        try:
            # Read file from disk
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Get filename from path
            import os
            filename = os.path.basename(file_path)
            
            # Chunk the content
            chunks = self.chunk_document(content, filename)
            
            logger.info(f"Loaded and chunked file from disk: {file_path} ({len(chunks)} chunks)")
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to load and chunk file {file_path}: {e}")
            return []
    
    def vector_similarity_search(
        self,
        query_embedding: List[float],
        document_chunks: List[Dict],
        max_chunks: Optional[int] = None
    ) -> List[Dict]:
        """
        Find most similar chunks using vector similarity (cosine similarity)
        
        Args:
            query_embedding: Query embedding vector
            document_chunks: List of chunks with embeddings
            max_chunks: Maximum number of chunks to return
        
        Returns:
            List of most similar chunks
        """
        import numpy as np
        
        if not document_chunks:
            return []
        
        max_chunks = max_chunks or self.max_chunks_per_query
        
        # Calculate cosine similarity for each chunk
        scored_chunks = []
        query_vec = np.array(query_embedding)
        query_norm = np.linalg.norm(query_vec)
        
        for chunk in document_chunks:
            if "embedding" not in chunk:
                continue
            
            chunk_vec = np.array(chunk["embedding"])
            chunk_norm = np.linalg.norm(chunk_vec)
            
            # Cosine similarity
            if query_norm > 0 and chunk_norm > 0:
                similarity = np.dot(query_vec, chunk_vec) / (query_norm * chunk_norm)
                scored_chunks.append((similarity, chunk))
        
        # Sort by similarity (highest first)
        scored_chunks.sort(reverse=True, key=lambda x: x[0])
        
        # Return top chunks
        relevant_chunks = [chunk for score, chunk in scored_chunks[:max_chunks]]
        
        logger.info(f"Retrieved {len(relevant_chunks)} chunks using vector similarity")
        return relevant_chunks
    
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
            logger.warning("No chunks provided to build_rag_context!")
            return f"No relevant information found in the documents.\n\nQuestion: {query}"
        
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
                "content": (
                    "You are an AI assistant specialized in answering questions based on provided documents. "
                    "Your task is to:\n"
                    "1. Carefully read the document excerpts provided\n"
                    "2. Answer the user's question using ONLY information from these excerpts\n"
                    "3. Be precise and cite specific information from the documents\n"
                    "4. If the answer is not found in the provided excerpts, clearly state: "
                    "'I cannot find this information in the provided documents.'\n"
                    "5. Do not make assumptions or add information not present in the documents\n"
                    "6. Keep your answers concise and relevant"
                )
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
