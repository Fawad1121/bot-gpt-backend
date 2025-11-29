# BOT GPT Backend - Design Document
**Case Study: Conversational AI Platform**  
**Candidate:** Fawad Ahmed  
**Role:** Associate AI Software Engineer (Backend-Focused)  
**Date:** November 2024

---

## 1. Executive Summary

BOT GPT is a production-grade conversational AI backend supporting:
- **Open Chat Mode**: General-purpose conversations with LLM
- **RAG Mode**: Document-grounded conversations using vector similarity search
- **Multi-turn conversations** with persistent history
- **Scalable architecture** with async processing and background tasks

**Tech Stack:** FastAPI + MongoDB Atlas + Groq API + Google Gemini Embeddings

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Client Layer                         │
│              (Postman / cURL / Frontend App)                │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP/REST
┌─────────────────────▼───────────────────────────────────────┐
│                     API Layer (FastAPI)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ Conversations│  │  Documents   │  │    Health    │       │
│  │   Routes     │  │   Routes     │  │    Check     │       │
│  └──────┬───────┘  └──────┬───────┘  └──────────────┘       │
└─────────┼──────────────────┼────────────────────────────────┘
          │                  │
┌─────────▼──────────────────▼────────────────────────────────┐
│                   Service Layer                             │
│  ┌─────────────────┐  ┌─────────────────┐                   │
│  │ Conversation    │  │  RAG Service    │                   │
│  │   Service       │  │  (Chunking +    │                   │
│  │                 │  │   Retrieval)    │                   │
│  └────────┬────────┘  └────────┬────────┘                   │
│           │                    │                            │
│  ┌────────▼────────┐  ┌────────▼────────┐                   │
│  │  LLM Service    │  │  Embedding      │                   │
│  │  (Groq API)     │  │  Service        │                   │
│  │                 │  │  (Gemini API)   │                   │
│  └─────────────────┘  └─────────────────┘                   │
│                                                             │
│  ┌──────────────────────────────────────┐                   │
│  │   Background Vectorization Queue     │                   │
│  │   (Async Task Processing)            │                   │
│  └──────────────────────────────────────┘                   │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│              Persistence Layer (MongoDB Atlas)              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ Conversations│  │   Messages   │  │  Documents   │       │
│  │  Collection  │  │  Collection  │  │  Collection  │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│                                                             │
│  ┌──────────────┐                                           │
│  │    Chunks    │  (Vector embeddings stored here)          │
│  │  Collection  │                                           │
│  └──────────────┘                                           │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Request Flow

**Open Chat Mode:**
```
User → API → Conversation Service → LLM Service → Groq API → Response
                    ↓
              Database (save message)
```

**RAG Mode:**
```
User → API → Conversation Service → Check vectorization status
                    ↓
              RAG Service (vector similarity search)
                    ↓
              Retrieve top-K relevant chunks
                    ↓
              LLM Service (chunks + query)
                    ↓
              Groq API → Response
                    ↓
              Database (save message)
```

---

## 3. Technology Stack Justification

### 3.1 Backend Framework: **FastAPI**
**Why:**
- ✅ **High Performance**: ASGI-based, async/await support
- ✅ **Auto-generated API Docs**: Swagger UI out-of-the-box
- ✅ **Type Safety**: Pydantic models for validation
- ✅ **Modern Python**: Python 3.11+ features
- ✅ **Easy Testing**: Built-in test client

### 3.2 Database: **MongoDB Atlas**
**Why:**
- ✅ **Flexible Schema**: Perfect for conversational data
- ✅ **Document Model**: Natural fit for messages/conversations
- ✅ **Scalability**: Horizontal scaling with sharding
- ✅ **Free Tier**: Cloud-hosted, no infrastructure needed
- ✅ **Vector Support**: Can store embeddings as arrays
- ✅ **Async Driver**: Motor for async operations

**Alternative Considered:** PostgreSQL with JSONB
- ❌ More rigid schema
- ❌ Complex joins for conversation history
- ✅ Better for transactional data

### 3.3 LLM Provider: **Groq API**
**Why:**
- ✅ **Free Tier**: No cost for development
- ✅ **Fast Inference**: Optimized LLM serving
- ✅ **Llama Models**: Open-source, high-quality
- ✅ **Simple API**: OpenAI-compatible interface

### 3.4 Embeddings: **Google Gemini**
**Why:**
- ✅ **Free API**: No cost for embeddings
- ✅ **High Quality**: 768-dimensional vectors
- ✅ **Fast**: Batch embedding support
- ✅ **Simple Integration**: Official SDK

---

## 4. Data Model & Database Schema

### 4.1 Collections

#### **Conversations Collection**
```json
{
  "_id": ObjectId("..."),
  "user_id": "user123",
  "mode": "rag_mode",  // or "open_chat"
  "document_ids": ["doc1", "doc2"],  // for RAG mode
  "created_at": ISODate("2024-11-29T10:00:00Z"),
  "updated_at": ISODate("2024-11-29T10:05:00Z"),
  "metadata": {
    "title": "Chat about FastAPI",
    "total_messages": 10,
    "total_tokens": 2500
  }
}
```

**Indexes:**
- `user_id` (for listing user's conversations)
- `updated_at` (for sorting by recent)

#### **Messages Collection**
```json
{
  "_id": ObjectId("..."),
  "conversation_id": "conv123",
  "role": "user",  // or "assistant"
  "content": "What is FastAPI?",
  "timestamp": ISODate("2024-11-29T10:00:00Z"),
  "metadata": {
    "tokens": 15,
    "model": "llama-3.3-70b-versatile"
  }
}
```

**Indexes:**
- `conversation_id` (for fetching conversation history)
- `timestamp` (for ordering messages)

#### **Documents Collection**
```json
{
  "_id": ObjectId("..."),
  "user_id": "user123",
  "filename": "fastapi_guide.txt",
  "file_path": "uploads/user123/doc123/fastapi_guide.txt",
  "file_size": 15000,
  "total_chunks": 10,
  "vectorized_chunks": 10,
  "is_vectorized": true,
  "created_at": ISODate("2024-11-29T09:00:00Z"),
  "metadata": {
    "processing_status": "completed"
  }
}
```

**Indexes:**
- `user_id` (for listing user's documents)
- `is_vectorized` (for filtering ready documents)

#### **Chunks Collection** (Vector Storage)
```json
{
  "_id": ObjectId("..."),
  "document_id": "doc123",
  "chunk_id": 0,
  "content": "FastAPI is a modern web framework...",
  "start_char": 0,
  "end_char": 500,
  "tokens": 120,
  "embedding": [0.123, 0.456, ...],  // 768 floats
  "is_vectorized": true
}
```

**Indexes:**
- `document_id` (for fetching document chunks)
- `is_vectorized` (for filtering ready chunks)
- Compound: `(document_id, is_vectorized)` (optimized queries)

### 4.2 Design Decisions

**Message Ordering:**
- Stored in separate `messages` collection
- Ordered by `timestamp` field
- Indexed for fast retrieval

**Conversation History:**
- Fetch messages by `conversation_id`
- Sort by `timestamp` ascending
- Limit to last N messages for context window

**Vector Storage:**
- Embeddings stored as BSON arrays in MongoDB
- 768-dimensional vectors (Gemini embedding-004)
- Cosine similarity computed in-memory (NumPy)

**Alternative:** Could use dedicated vector DB (Pinecone, Chroma) for larger scale

---

## 5. REST API Design

### 5.1 Endpoint Specifications

#### **Create Conversation**
```http
POST /api/v1/conversations
Content-Type: application/json

{
  "user_id": "user123",
  "message": "What is FastAPI?",
  "mode": "open_chat",  // or "rag_mode"
  "document_ids": []     // required for rag_mode
}

Response: 201 Created
{
  "conversation_id": "692abc...",
  "message_id": "692def...",
  "response": "FastAPI is a modern web framework..."
}
```

#### **Continue Conversation**
```http
POST /api/v1/conversations/{conversation_id}/messages
Content-Type: application/json

{
  "message": "Tell me more"
}

Response: 200 OK
{
  "message_id": "692ghi...",
  "response": "FastAPI provides automatic..."
}
```

#### **List Conversations**
```http
GET /api/v1/conversations?user_id=user123&limit=10&offset=0

Response: 200 OK
{
  "conversations": [
    {
      "conversation_id": "692abc...",
      "mode": "open_chat",
      "created_at": "2024-11-29T10:00:00Z",
      "updated_at": "2024-11-29T10:05:00Z",
      "metadata": { "total_messages": 5 }
    }
  ],
  "total": 25,
  "limit": 10,
  "offset": 0
}
```

#### **Get Conversation Details**
```http
GET /api/v1/conversations/{conversation_id}

Response: 200 OK
{
  "conversation_id": "692abc...",
  "user_id": "user123",
  "mode": "open_chat",
  "messages": [
    {
      "message_id": "692def...",
      "role": "user",
      "content": "What is FastAPI?",
      "timestamp": "2024-11-29T10:00:00Z"
    },
    {
      "message_id": "692ghi...",
      "role": "assistant",
      "content": "FastAPI is...",
      "timestamp": "2024-11-29T10:00:05Z"
    }
  ]
}
```

#### **Delete Conversation**
```http
DELETE /api/v1/conversations/{conversation_id}

Response: 204 No Content
```

#### **Upload Document (RAG)**
```http
POST /api/v1/documents
Content-Type: multipart/form-data

file: fastapi_guide.txt
user_id: user123

Response: 201 Created
{
  "document_id": "692jkl...",
  "filename": "fastapi_guide.txt",
  "chunks": 0  // Will be set after processing
}
```

#### **List Documents**
```http
GET /api/v1/documents?user_id=user123

Response: 200 OK
{
  "documents": [
    {
      "document_id": "692jkl...",
      "filename": "fastapi_guide.txt",
      "is_vectorized": true,
      "total_chunks": 10,
      "created_at": "2024-11-29T09:00:00Z"
    }
  ]
}
```

### 5.2 Error Handling

**HTTP Status Codes:**
- `200 OK` - Successful GET/POST
- `201 Created` - Resource created
- `204 No Content` - Successful DELETE
- `400 Bad Request` - Invalid input
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

**Error Response Format:**
```json
{
  "detail": "Document not found"
}
```

---

## 6. LLM Context & Cost Management

### 6.1 Context Window Strategy

**Model:** Llama 3.3 70B (6000 token context window)

**Context Construction:**
```python
# Open Chat Mode
context = [
    {"role": "system", "content": "You are a helpful assistant"},
    *last_10_messages,  # Sliding window
    {"role": "user", "content": current_message}
]

# RAG Mode
context = [
    {"role": "system", "content": "Answer based on documents"},
    {"role": "user", "content": f"Context: {chunks}\n\nQuestion: {query}"}
]
```

### 6.2 Token Management

**Strategies:**
1. **Sliding Window**: Keep last 10 messages only
2. **Token Counting**: Use `tiktoken` to count tokens
3. **Truncation**: If exceeds limit, remove oldest messages
4. **System Prompt**: Keep concise (< 50 tokens)

**Cost Optimization:**
- Free tier usage (Groq API)
- Minimal context (only relevant chunks for RAG)
- No redundant API calls
- Cache embeddings (don't re-embed same chunks)

### 6.3 Context Overflow Handling

```python
if total_tokens > 6000:
    # Remove oldest messages until under limit
    while total_tokens > 5500:  # Buffer
        messages.pop(0)
        total_tokens = count_tokens(messages)
```

---

## 7. RAG Implementation

### 7.1 Document Processing Pipeline

```
Upload → Save to Disk → Return Response
              ↓
    Background Processing:
    1. Read file from disk
    2. Chunk (500 chars, sentence boundaries)
    3. Store chunks in DB (without embeddings)
    4. For each chunk:
       - Generate embedding (Gemini API)
       - Update chunk with embedding
       - Mark as vectorized
    5. Mark document as vectorized
```

### 7.2 Chunking Strategy

**Method:** Character-based with sentence boundaries

```python
CHUNK_SIZE = 500 characters
NO_OVERLAP  # Simple, no overlap

# Algorithm:
1. Start at position 0
2. Take next 500 characters
3. Find last period/newline in chunk
4. Break at sentence boundary
5. Move to next chunk
```

**Why:**
- Simple and predictable
- Preserves sentence meaning
- Fast processing
- Good for embeddings

### 7.3 Retrieval Strategy

**Method:** Cosine Similarity Search

```python
# 1. Generate query embedding
query_vector = gemini.embed(user_query)

# 2. Fetch all vectorized chunks for documents
chunks = db.chunks.find({
    "document_id": {"$in": document_ids},
    "is_vectorized": True
})

# 3. Compute cosine similarity
for chunk in chunks:
    similarity = cosine_similarity(query_vector, chunk.embedding)

# 4. Return top 5 most similar chunks
top_chunks = sorted(chunks, key=similarity, reverse=True)[:5]
```

**Why Cosine Similarity:**
- Standard for semantic search
- Works well with normalized embeddings
- Fast computation with NumPy
- Proven effective for RAG

### 7.4 RAG Flow Diagram

```
User Query
    ↓
Check if documents vectorized
    ↓ (if not ready)
Return: "Please wait, processing your file"
    ↓ (if ready)
Generate query embedding (Gemini)
    ↓
Fetch vectorized chunks from DB
    ↓
Compute cosine similarity
    ↓
Select top 5 chunks
    ↓
Construct LLM prompt:
  "Context: [chunk1, chunk2, ...]
   Question: {user_query}"
    ↓
Send to Groq API
    ↓
Return response
```

---

## 8. Error Handling & Scalability

### 8.1 Failure Points & Mitigation

| Failure Point | Mitigation Strategy |
|--------------|---------------------|
| **LLM API Timeout** | Retry with exponential backoff (3 attempts) |
| **LLM API Rate Limit** | Implement request queuing, return 429 status |
| **Database Write Failure** | Transaction rollback, log error, return 500 |
| **Token Limit Breach** | Truncate context, retry with smaller history |
| **Document Processing Failure** | Mark as failed, log error, allow re-upload |
| **Embedding API Failure** | Retry, mark chunk as failed, continue others |

### 8.2 Retry Strategy

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def call_llm(messages):
    return await groq_client.chat.completions.create(...)
```

### 8.3 Logging & Monitoring

**Structured Logging:**
```python
logger.info(f"LLM request", extra={
    "conversation_id": conv_id,
    "tokens": token_count,
    "model": model_name
})
```

**Metrics to Track:**
- API response times
- Token usage per conversation
- Error rates by endpoint
- Document processing time
- Embedding generation time

### 8.4 Scalability Analysis

**Bottlenecks at 1M Users:**

1. **Database Queries** (Most Critical)
   - **Problem:** Fetching conversation history
   - **Solution:** 
     - Add indexes on `user_id`, `conversation_id`
     - Use MongoDB sharding by `user_id`
     - Implement caching (Redis) for recent conversations

2. **LLM API Calls**
   - **Problem:** Rate limits, latency
   - **Solution:**
     - Implement request queue (Celery + Redis)
     - Use multiple API keys
     - Add response caching for common queries

3. **Embedding Generation**
   - **Problem:** Slow for large documents
   - **Solution:**
     - Already using background processing
     - Batch embedding requests
     - Use dedicated worker pool

4. **File Storage**
   - **Problem:** Disk space
   - **Solution:**
     - Use S3/Cloud Storage
     - Implement file cleanup policies
     - Compress old documents

**Horizontal Scaling:**
```
Load Balancer
    ↓
FastAPI Instance 1 ─┐
FastAPI Instance 2 ─┼─→ MongoDB Cluster (Sharded)
FastAPI Instance N ─┘
    ↓
Background Workers (Celery)
    ↓
Redis (Queue + Cache)
```

---

## 9. DevOps & Deployment

### 9.1 Docker Setup

**Dockerfile:**
- Multi-stage build
- Non-root user
- Health check endpoint
- Production-ready

**docker-compose.yml:**
- FastAPI service
- MongoDB service
- Volume mounts
- Network configuration

### 9.2 CI/CD Pipeline (GitHub Actions)

**Workflow:**
1. **Lint & Format** (Black, Flake8)
2. **Type Check** (MyPy)
3. **Unit Tests** (Pytest)
4. **Build Docker Image**
5. **Push to Registry** (optional)

**Triggers:**
- Push to `main` branch
- Pull requests

### 9.3 Environment Variables

**Required:**
- `MONGODB_URI` - MongoDB connection string
- `GROQ_API_KEY` - Groq API key
- `GEMINI_API_KEY` - Google Gemini API key

**Optional:**
- `LOG_LEVEL` - Logging level (default: INFO)
- `MAX_TOKENS` - Max tokens per request (default: 2048)
- `CHUNK_SIZE` - Chunk size for RAG (default: 500)

---

## 10. Testing Strategy

### 10.1 Unit Tests

**Coverage:**
- Database service methods
- LLM service (mocked API)
- RAG service (chunking, retrieval)
- Conversation service logic

**Example:**
```python
async def test_create_conversation():
    response = await conversation_service.create_conversation(
        user_id="test_user",
        message="Hello",
        mode="open_chat"
    )
    assert response.conversation_id is not None
```

### 10.2 API Tests

**Coverage:**
- All REST endpoints
- Request validation
- Error responses
- Authentication (if added)

**Example:**
```python
def test_create_conversation_endpoint():
    response = client.post("/api/v1/conversations", json={
        "user_id": "test",
        "message": "Hello",
        "mode": "open_chat"
    })
    assert response.status_code == 201
```

### 10.3 Integration Tests

**Manual Testing:**
- Upload document → Wait for vectorization → RAG query
- Multi-turn conversation flow
- Error scenarios (invalid input, missing documents)

---

## 11. Future Enhancements

### 11.1 Short-term (Next Sprint)
- [ ] User authentication (JWT)
- [ ] Rate limiting per user
- [ ] Conversation summarization
- [ ] Export conversation history
- [ ] Support for PDF files

### 11.2 Long-term (Roadmap)
- [ ] Multi-modal support (images, audio)
- [ ] Real-time streaming responses (SSE)
- [ ] Conversation analytics dashboard
- [ ] A/B testing for different LLMs
- [ ] Fine-tuned embeddings
- [ ] Dedicated vector database (Pinecone/Chroma)
- [ ] WebSocket support for real-time chat

---

## 12. Conclusion

This backend architecture provides:
- ✅ **Production-ready** REST API with comprehensive error handling
- ✅ **Scalable design** with async processing and background tasks
- ✅ **Cost-effective** using free-tier APIs (Groq, Gemini)
- ✅ **Modern stack** (FastAPI, MongoDB, Vector RAG)
- ✅ **Well-tested** with unit and integration tests
- ✅ **DevOps-ready** with Docker and CI/CD

The system is designed to handle both simple chat and complex RAG scenarios while maintaining performance, reliability, and scalability.

**GitHub Repository:** [Your GitHub Link]  
**Live Demo:** [Optional - if deployed]

---

**End of Document**
