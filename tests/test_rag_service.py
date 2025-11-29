"""
Tests for RAG service
"""
import pytest
from app.services.rag_service import rag_service
from app.models.document import DocumentChunk


def test_chunk_document():
    """Test document chunking"""
    content = "This is a test document. " * 100  # Create longer text
    filename = "test.txt"
    
    chunks = rag_service.chunk_document(content, filename)
    
    assert len(chunks) > 0
    assert all(isinstance(chunk, DocumentChunk) for chunk in chunks)
    assert all(chunk.tokens > 0 for chunk in chunks)


def test_retrieve_relevant_chunks():
    """Test chunk retrieval"""
    chunks = [
        DocumentChunk(
            chunk_id=0,
            content="Python is a programming language",
            start_char=0,
            end_char=35,
            tokens=10
        ),
        DocumentChunk(
            chunk_id=1,
            content="JavaScript is used for web development",
            start_char=36,
            end_char=75,
            tokens=10
        ),
        DocumentChunk(
            chunk_id=2,
            content="Python is great for data science and machine learning",
            start_char=76,
            end_char=130,
            tokens=12
        ),
    ]
    
    query = "Tell me about Python"
    relevant = rag_service.retrieve_relevant_chunks(query, chunks, max_chunks=2)
    
    assert len(relevant) <= 2
    # Should retrieve Python-related chunks
    assert any("Python" in chunk.content for chunk in relevant)


def test_build_rag_context():
    """Test RAG context building"""
    chunks = [
        DocumentChunk(
            chunk_id=0,
            content="Python is a programming language",
            start_char=0,
            end_char=35,
            tokens=10
        ),
    ]
    
    query = "What is Python?"
    context = rag_service.build_rag_context(query, chunks)
    
    assert "Python" in context
    assert query in context
    assert "Document Excerpt" in context


def test_create_rag_messages():
    """Test RAG message creation"""
    chunks = [
        DocumentChunk(
            chunk_id=0,
            content="Test content",
            start_char=0,
            end_char=12,
            tokens=5
        ),
    ]
    
    query = "Test query"
    messages = rag_service.create_rag_messages(query, chunks)
    
    assert len(messages) >= 2  # System + user message
    assert messages[0]["role"] == "system"
    assert messages[-1]["role"] == "user"
    assert query in messages[-1]["content"]
