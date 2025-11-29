"""
Background task queue for document vectorization
"""
import asyncio
from typing import Dict, Any
from app.services.database import db_service
from app.services.rag_service import rag_service
from app.services.embedding_service import embedding_service
from app.utils.logger import setup_logger
from bson import ObjectId

logger = setup_logger(__name__)


class VectorizationQueue:
    """Background task queue for vectorizing documents one chunk at a time"""
    
    def __init__(self):
        self.tasks = {}
    
    async def vectorize_document(self, document_id: str):
        """
        Background task to chunk and vectorize a document
        
        Args:
            document_id: Document ID to process
        """
        try:
            logger.info(f"Starting background processing for document: {document_id}")
            
            # Get document from database
            document = await db_service.get_document(document_id)
            if not document:
                logger.error(f"Document not found: {document_id}")
                return
            
            file_path = document.get("file_path")
            if not file_path:
                logger.error(f"No file path for document: {document_id}")
                return
            
            # STEP 1: Chunk the document from disk (async, non-blocking)
            logger.info(f"Step 1: Chunking document from {file_path}")
            chunks = await rag_service.load_and_chunk_from_file_async(file_path)
            
            if not chunks:
                logger.error(f"No chunks generated for document: {document_id}")
                return
            
            logger.info(f"Created {len(chunks)} chunks")
            
            # STEP 2: Store chunks in database WITHOUT embeddings
            chunk_ids = []
            for chunk in chunks:
                chunk_data = {
                    "document_id": document_id,
                    "chunk_id": chunk.chunk_id,
                    "content": chunk.content,
                    "start_char": chunk.start_char,
                    "end_char": chunk.end_char,
                    "tokens": chunk.tokens,
                    "embedding": None,
                    "is_vectorized": False
                }
                result = await db_service.db.chunks.insert_one(chunk_data)
                chunk_ids.append(str(result.inserted_id))
            
            # Update document with chunk count
            await db_service.db.documents.update_one(
                {"_id": ObjectId(document_id)},
                {"$set": {"total_chunks": len(chunk_ids)}}
            )
            
            logger.info(f"Stored {len(chunk_ids)} chunks in database")
            
            # Clear memory
            del chunks
            
            # STEP 3: Vectorize each chunk ONE AT A TIME
            logger.info(f"Step 2: Vectorizing {len(chunk_ids)} chunks one at a time")
            
            vectorized_count = 0
            for i, chunk_id in enumerate(chunk_ids):
                try:
                    # Fetch chunk from DB
                    chunk = await db_service.db.chunks.find_one({"_id": ObjectId(chunk_id)})
                    if not chunk:
                        continue
                    
                    logger.info(f"Vectorizing chunk {i+1}/{len(chunk_ids)} (ID: {chunk_id})")
                    
                    # Generate embedding for this chunk
                    embedding = embedding_service.generate_embedding(chunk["content"])
                    
                    # Update this chunk with embedding
                    await db_service.db.chunks.update_one(
                        {"_id": ObjectId(chunk_id)},
                        {
                            "$set": {
                                "embedding": embedding,
                                "is_vectorized": True
                            }
                        }
                    )
                    
                    vectorized_count += 1
                    
                    # Update document progress
                    await db_service.db.documents.update_one(
                        {"_id": ObjectId(document_id)},
                        {
                            "$set": {
                                "vectorized_chunks": vectorized_count,
                                "metadata.processing_status": f"vectorizing ({vectorized_count}/{len(chunk_ids)})"
                            }
                        }
                    )
                    
                    logger.info(f"✅ Chunk {i+1}/{len(chunk_ids)} vectorized ({vectorized_count} total)")
                    
                    # Small delay to prevent API rate limiting
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"Failed to vectorize chunk {i+1}: {e}")
                    continue
            
            # All chunks done - mark document as vectorized
            await db_service.db.documents.update_one(
                {"_id": ObjectId(document_id)},
                {
                    "$set": {
                        "is_vectorized": True,
                        "vectorized_chunks": vectorized_count,
                        "total_chunks": len(chunk_ids),
                        "metadata.processing_status": "completed"
                    }
                }
            )
            
            logger.info(f"✅ Document processing complete: {document_id} ({vectorized_count}/{len(chunk_ids)} chunks)")
            
        except Exception as e:
            logger.error(f"Failed to process document {document_id}: {e}")
            
            # Mark as failed
            try:
                await db_service.db.documents.update_one(
                    {"_id": ObjectId(document_id)},
                    {
                        "$set": {
                            "is_vectorized": False,
                            "metadata.processing_status": "failed",
                            "metadata.processing_error": str(e)
                        }
                    }
                )
            except:
                pass
    
    def start_vectorization(self, document_id: str):
        """
        Start vectorization task in background
        
        Args:
            document_id: Document ID to vectorize
        """
        task = asyncio.create_task(self.vectorize_document(document_id))
        self.tasks[document_id] = task
        logger.info(f"Started background vectorization task for: {document_id}")
        return task


# Global vectorization queue instance
vectorization_queue = VectorizationQueue()
