"""
Configuration management using Pydantic Settings
"""
from pydantic_settings import BaseSettings
from typing import List
import json


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # MongoDB Configuration
    MONGODB_URI: str
    DATABASE_NAME: str = "bot_gpt_db"
    
    # Groq API Configuration
    GROQ_API_KEY: str
    
    # Application Settings
    APP_NAME: str = "BOT GPT Backend"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CORS Settings
    CORS_ORIGINS: str = '["http://localhost:3000","http://localhost:8000"]'
    
    # LLM Settings
    DEFAULT_MODEL: str = "llama-3.3-70b-versatile"
    MAX_TOKENS: int = 2048
    TEMPERATURE: float = 0.7
    CONTEXT_WINDOW_SIZE: int = 6000
    
    # Gemini Embedding Settings
    GEMINI_API_KEY: str
    GEMINI_EMBEDDING_MODEL: str = "text-embedding-004"
    EMBEDDING_DIMENSION: int = 768  # text-embedding-004 dimension
    
    # RAG Settings
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    MAX_CHUNKS_PER_QUERY: int = 3  # Top 3 most relevant chunks
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from JSON string"""
        try:
            return json.loads(self.CORS_ORIGINS)
        except:
            return ["http://localhost:3000", "http://localhost:8000"]


# Global settings instance
settings = Settings()
