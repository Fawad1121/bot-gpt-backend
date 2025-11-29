"""
MongoDB database service for async operations
"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional, List, Dict, Any
from bson import ObjectId
from datetime import datetime

from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class DatabaseService:
    """MongoDB database service with async operations"""
    
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None
    
    @classmethod
    async def connect(cls):
        """Connect to MongoDB"""
        try:
            cls.client = AsyncIOMotorClient(settings.MONGODB_URI)
            cls.db = cls.client[settings.DATABASE_NAME]
            
            # Test connection
            await cls.client.admin.command('ping')
            logger.info(f"Connected to MongoDB database: {settings.DATABASE_NAME}")
            
            # Create indexes
            await cls.create_indexes()
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    @classmethod
    async def disconnect(cls):
        """Disconnect from MongoDB"""
        if cls.client:
            cls.client.close()
            logger.info("Disconnected from MongoDB")
    
    @classmethod
    async def create_indexes(cls):
        """Create database indexes for better performance"""
        try:
            # Conversations indexes
            await cls.db.conversations.create_index("user_id")
            await cls.db.conversations.create_index([("updated_at", -1)])
            
            # Messages indexes
            await cls.db.messages.create_index("conversation_id")
            await cls.db.messages.create_index([("timestamp", 1)])
            
            # Documents indexes
            await cls.db.documents.create_index("user_id")
            await cls.db.documents.create_index("is_vectorized")
            
            # Chunks indexes (NEW)
            await cls.db.chunks.create_index("document_id")
            await cls.db.chunks.create_index("is_vectorized")
            await cls.db.chunks.create_index([("document_id", 1), ("is_vectorized", 1)])
            
            # Users indexes
            await cls.db.users.create_index("email", unique=True)
            await cls.db.users.create_index("username", unique=True)
            
            logger.info("Database indexes created successfully")
        except Exception as e:
            logger.warning(f"Error creating indexes: {e}")
    
    # User operations
    @classmethod
    async def create_user(cls, user_data: Dict[str, Any]) -> str:
        """Create a new user"""
        result = await cls.db.users.insert_one(user_data)
        return str(result.inserted_id)
    
    @classmethod
    async def get_user(cls, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        user = await cls.db.users.find_one({"_id": ObjectId(user_id)})
        if user:
            user["_id"] = str(user["_id"])
        return user
    
    @classmethod
    async def get_user_by_email(cls, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        user = await cls.db.users.find_one({"email": email})
        if user:
            user["_id"] = str(user["_id"])
        return user
    
    # Conversation operations
    @classmethod
    async def create_conversation(cls, conversation_data: Dict[str, Any]) -> str:
        """Create a new conversation"""
        conversation_data["created_at"] = datetime.utcnow()
        conversation_data["updated_at"] = datetime.utcnow()
        conversation_data["message_count"] = 0
        conversation_data["total_tokens"] = 0
        
        result = await cls.db.conversations.insert_one(conversation_data)
        return str(result.inserted_id)
    
    @classmethod
    async def get_conversation(cls, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation by ID"""
        conversation = await cls.db.conversations.find_one({"_id": ObjectId(conversation_id)})
        if conversation:
            conversation["_id"] = str(conversation["_id"])
        return conversation
    
    @classmethod
    async def list_conversations(
        cls, 
        user_id: Optional[str] = None, 
        limit: int = 20, 
        offset: int = 0
    ) -> tuple[List[Dict[str, Any]], int]:
        """List conversations (optionally filtered by user) with pagination"""
        # Build query filter
        query_filter = {"user_id": user_id} if user_id else {}
        
        cursor = cls.db.conversations.find(query_filter)
        total = await cls.db.conversations.count_documents(query_filter)
        
        conversations = await cursor.sort("updated_at", -1).skip(offset).limit(limit).to_list(length=limit)
        
        for conv in conversations:
            conv["_id"] = str(conv["_id"])
        
        return conversations, total
    
    @classmethod
    async def update_conversation(cls, conversation_id: str, update_data: Dict[str, Any]) -> bool:
        """Update conversation"""
        update_data["updated_at"] = datetime.utcnow()
        result = await cls.db.conversations.update_one(
            {"_id": ObjectId(conversation_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    @classmethod
    async def delete_conversation(cls, conversation_id: str) -> bool:
        """Delete conversation and all its messages"""
        # Delete messages first
        await cls.db.messages.delete_many({"conversation_id": conversation_id})
        
        # Delete conversation
        result = await cls.db.conversations.delete_one({"_id": ObjectId(conversation_id)})
        return result.deleted_count > 0
    
    # Message operations
    @classmethod
    async def create_message(cls, message_data: Dict[str, Any]) -> str:
        """Create a new message"""
        message_data["timestamp"] = datetime.utcnow()
        result = await cls.db.messages.insert_one(message_data)
        
        # Update conversation stats
        await cls.db.conversations.update_one(
            {"_id": ObjectId(message_data["conversation_id"])},
            {
                "$inc": {
                    "message_count": 1,
                    "total_tokens": message_data.get("tokens", 0)
                },
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        return str(result.inserted_id)
    
    @classmethod
    async def get_messages(cls, conversation_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get messages for a conversation"""
        cursor = cls.db.messages.find({"conversation_id": conversation_id}).sort("timestamp", 1)
        
        if limit:
            cursor = cursor.limit(limit)
        
        messages = await cursor.to_list(length=None)
        
        for msg in messages:
            msg["_id"] = str(msg["_id"])
        
        return messages
    
    # Document operations
    @classmethod
    async def create_document(cls, document_data: Dict[str, Any]) -> str:
        """Create a new document"""
        document_data["created_at"] = datetime.utcnow()
        result = await cls.db.documents.insert_one(document_data)
        return str(result.inserted_id)
    
    @classmethod
    async def get_document(cls, document_id: str) -> Optional[Dict[str, Any]]:
        """Get document by ID"""
        document = await cls.db.documents.find_one({"_id": ObjectId(document_id)})
        if document:
            document["_id"] = str(document["_id"])
        return document
    
    @classmethod
    async def list_documents(
        cls, 
        user_id: str, 
        limit: int = 20, 
        offset: int = 0
    ) -> tuple[List[Dict[str, Any]], int]:
        """List documents for a user with pagination"""
        cursor = cls.db.documents.find({"user_id": user_id})
        total = await cls.db.documents.count_documents({"user_id": user_id})
        
        documents = await cursor.sort("created_at", -1).skip(offset).limit(limit).to_list(length=limit)
        
        for doc in documents:
            doc["_id"] = str(doc["_id"])
        
        return documents, total
    
    @classmethod
    async def delete_document(cls, document_id: str) -> bool:
        """Delete document"""
        result = await cls.db.documents.delete_one({"_id": ObjectId(document_id)})
        return result.deleted_count > 0


# Global database service instance
db_service = DatabaseService()
