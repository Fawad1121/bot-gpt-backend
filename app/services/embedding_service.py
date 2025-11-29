"""
Embedding service using Google Gemini API
"""
from google import genai
from typing import List
from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class EmbeddingService:
    """Service for generating embeddings using Gemini"""
    
    def __init__(self):
        # Configure Gemini API
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model = "text-embedding-004"
        logger.info(f"Initialized Gemini embedding service with model: {self.model}")
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for text
        
        Args:
            text: Text to embed
        
        Returns:
            List of floats representing the embedding vector
        """
        try:
            result = self.client.models.embed_content(
                model=self.model,
                contents=[text]  # Single text as list
            )
            
            embedding = result.embeddings[0].values
            logger.info(f"Generated embedding with dimension: {len(embedding)}")
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embedding vectors for multiple texts (batch)
        
        Args:
            texts: List of texts to embed
        
        Returns:
            List of embedding vectors
        """
        try:
            result = self.client.models.embed_content(
                model=self.model,
                contents=texts  # Batch request
            )
            
            embeddings = [emb.values for emb in result.embeddings]
            logger.info(f"Generated {len(embeddings)} embeddings with dimension: {len(embeddings[0]) if embeddings else 0}")
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            raise


# Global embedding service instance
embedding_service = EmbeddingService()
