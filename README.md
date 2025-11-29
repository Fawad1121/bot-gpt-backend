# BOT GPT Backend - Conversational AI Platform

> **Case Study Submission for BOT Consulting**  
> **Candidate:** Fawad Ahmed  
> **Role:** Associate AI Software Engineer (Backend-Focused)  
> **GitHub:** [@Fawad1121](https://github.com/Fawad1121)

---

## 📖 Table of Contents

- [Overview](#-overview)
- [What I Built](#-what-i-built)
- [Quick Start](#-quick-start)
- [Features](#-features)
- [Architecture](#-architecture)
- [Technology Stack](#-technology-stack)
- [API Documentation](#-api-documentation)
- [RAG Implementation](#-rag-implementation)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Design Decisions](#-design-decisions)
- [Challenges & Solutions](#-challenges--solutions)

---

## 🎯 Overview

I built **BOT GPT Backend** - a production-grade conversational AI platform that supports both general chat and document-grounded conversations (RAG). The system is designed with scalability, cost-efficiency, and production-readiness in mind.

### What Makes This Special?

- ✅ **Dual Conversation Modes**: Open chat + RAG with vector similarity search
- ✅ **Production-Ready**: Docker, CI/CD, comprehensive tests, structured logging
- ✅ **Memory-Efficient**: Background processing, async operations, disk-based storage
- ✅ **Vector RAG**: Google Gemini embeddings with cosine similarity retrieval
- ✅ **Cost-Optimized**: Free-tier APIs (Groq + Gemini), smart context management
- ✅ **Scalable Architecture**: Stateless API, MongoDB Atlas, horizontal scaling ready

---

## 🚀 What I Built

### Core Features Implemented

1. **RESTful API** (FastAPI)
   - Create, read, update, delete conversations
   - Multi-turn conversation support
   - Document upload and management
   - Pagination, error handling, validation

2. **LLM Integration** (Groq API - Llama 3.3 70B)
   - Automatic context window management
   - Token counting and optimization
   - Retry logic with exponential backoff
   - Sliding window for conversation history

3. **RAG System** (Vector-Based)
   - Document upload with background processing
   - Character-based chunking (500 chars, sentence boundaries)
   - Google Gemini embeddings (768 dimensions)
   - Cosine similarity search for retrieval
   - Separate chunks collection for scalability

4. **Production Infrastructure**
   - Docker containerization
   - GitHub Actions CI/CD pipeline
   - Unit and integration tests
   - Structured logging
   - Health check endpoints

---

## ⚡ Quick Start

### Prerequisites

- Python 3.11+
- MongoDB Atlas account (free tier)
- Groq API key (free tier)
- Google Gemini API key (free tier)

### 1. Clone & Setup

```bash
git clone https://github.com/Fawad1121/bot-gpt-backend.git
cd bot-gpt-backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and add your credentials:

```env
MONGODB_URI=your_mongodb_atlas_connection_string
GROQ_API_KEY=your_groq_api_key
GEMINI_API_KEY=your_gemini_api_key
```

### 3. Run the Server

```bash
uvicorn main:app --reload
```

✅ **Server running at**: http://localhost:8000

---

## 🧪 Test the API

### Option 1: Swagger UI (Recommended)

1. Open http://localhost:8000/docs
2. Click on any endpoint
3. Click "Try it out"
4. Fill in the parameters
5. Click "Execute"

**All endpoints are interactive and documented!**

### Option 2: Postman

#### Test 1: Health Check
```http
GET http://localhost:8000/health
```

#### Test 2: Create Open Chat Conversation
```http
POST http://localhost:8000/api/v1/conversations
Content-Type: application/json

{
  "user_id": "user123",
  "message": "Explain FastAPI in simple terms",
  "mode": "open_chat"
}
```

#### Test 3: Continue Conversation
```http
POST http://localhost:8000/api/v1/conversations/{conversation_id}/messages
Content-Type: application/json

{
  "message": "Can you give me a code example?"
}
```

#### Test 4: Upload Document for RAG
```http
POST http://localhost:8000/api/v1/documents
Content-Type: multipart/form-data

file: <select your .txt file>
user_id: user123
```

#### Test 5: RAG Conversation
```http
POST http://localhost:8000/api/v1/conversations
Content-Type: application/json

{
  "user_id": "user123",
  "message": "What does the document say about FastAPI?",
  "mode": "rag_mode",
  "document_ids": ["<document_id from test 4>"]
}
```

**Note:** Wait 10-30 seconds after uploading document for vectorization to complete.

---

## ✨ Features

### 1. Dual Conversation Modes

**Open Chat Mode:**
- Direct conversation with Llama 3.3 70B
- Maintains conversation history
- Automatic context window management
- Token optimization

**RAG Mode (Retrieval-Augmented Generation):**
- Upload documents (.txt files)
- Background vectorization with Gemini embeddings
- Vector similarity search (cosine similarity)
- Document-grounded responses
- Progress tracking (`is_vectorized` status)

### 2. Smart Context Management

- **Sliding Window**: Keeps last 10 messages
- **Token Counting**: Uses tiktoken for accuracy
- **Auto-Truncation**: Removes oldest messages when exceeding limits
- **RAG Context**: Top 5 most relevant chunks only

### 3. Production-Ready Features

- ✅ **Error Handling**: Retry logic, graceful failures, detailed error messages
- ✅ **Logging**: Structured logging with request tracking
- ✅ **Validation**: Pydantic models for all inputs
- ✅ **CORS**: Configured for frontend integration
- ✅ **Health Checks**: Endpoint for monitoring
- ✅ **Docker**: Multi-stage build, non-root user
- ✅ **CI/CD**: GitHub Actions for linting, testing, building

---

## 🏗️ Architecture

### High-Level System Design

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

### Request Flow

**Open Chat:**
```
User → API → Conversation Service → LLM Service → Groq API → Response
                    ↓
              Save to MongoDB
```

**RAG Mode:**
```
User → API → Check vectorization → Vector Search → LLM → Response
                                         ↓
                              Top 5 relevant chunks
```

---

## 🛠️ Technology Stack

### Backend Framework: **FastAPI**
**Why I chose it:**
- High performance (ASGI-based, async/await)
- Auto-generated API docs (Swagger UI)
- Type safety with Pydantic
- Easy testing with built-in test client
- Modern Python 3.11+ features

### Database: **MongoDB Atlas**
**Why I chose it:**
- Flexible schema (perfect for conversational data)
- Document model (natural fit for messages)
- Horizontal scaling with sharding
- Free tier (cloud-hosted)
- Can store vector embeddings as arrays
- Async driver (Motor)

### LLM: **Groq API (Llama 3.3 70B)**
**Why I chose it:**
- Free tier for development
- Fast inference (optimized serving)
- High-quality open-source model
- OpenAI-compatible API

### Embeddings: **Google Gemini**
**Why I chose it:**
- Free API
- 768-dimensional vectors
- Batch embedding support
- Official SDK

---

## 📚 API Documentation

### Base URL
```
http://localhost:8000
```

### Endpoints

#### Conversations

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/conversations` | Create new conversation |
| `GET` | `/api/v1/conversations` | List all conversations |
| `GET` | `/api/v1/conversations/{id}` | Get conversation details |
| `POST` | `/api/v1/conversations/{id}/messages` | Add message to conversation |
| `DELETE` | `/api/v1/conversations/{id}` | Delete conversation |

#### Documents

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/documents` | Upload document |
| `GET` | `/api/v1/documents` | List documents |
| `GET` | `/api/v1/documents/{id}` | Get document details |
| `DELETE` | `/api/v1/documents/{id}` | Delete document |

#### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |

### Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

**Try all endpoints directly in the browser!**

---

## 🔍 RAG Implementation

### How It Works

#### 1. Document Upload Flow

```
Upload → Save to Disk → Return Response (Immediate)
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

#### 2. Chunking Strategy

- **Size**: 500 characters per chunk
- **Boundaries**: Breaks at sentence endings (periods/newlines)
- **No Overlap**: Simple, predictable chunks
- **Token Counting**: Uses tiktoken for accuracy

#### 3. Vector Storage

- **Collection**: `chunks` (separate from documents)
- **Embedding**: 768-dimensional vectors (Gemini text-embedding-004)
- **Format**: BSON array in MongoDB
- **Indexing**: Compound index on `(document_id, is_vectorized)`

#### 4. Retrieval Strategy

**Method**: Cosine Similarity Search

```python
# 1. Generate query embedding
query_vector = gemini.embed(user_query)

# 2. Fetch vectorized chunks
chunks = db.chunks.find({
    "document_id": {"$in": document_ids},
    "is_vectorized": True
})

# 3. Compute cosine similarity (NumPy)
similarities = cosine_similarity(query_vector, chunk_vectors)

# 4. Return top 5 chunks
top_chunks = sorted(chunks, key=similarity, reverse=True)[:5]
```

#### 5. Memory Efficiency

**Problem Solved**: Server was freezing during document processing

**Solution**:
- Save file to disk immediately
- Return response to user
- Process in background (async tasks)
- Chunk one at a time
- Clear memory after each step

**Result**: Server stays responsive, handles large files

---

## 🧪 Testing

### Run Tests

```bash
# All tests
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=app --cov-report=html

# Specific test file
pytest tests/test_api.py -v
```

### Test Coverage

- ✅ Database service methods
- ✅ LLM service (mocked API)
- ✅ RAG service (chunking, retrieval)
- ✅ Conversation service logic
- ✅ All API endpoints
- ✅ Error handling
- ✅ Validation

### Manual Testing via Swagger

1. Go to http://localhost:8000/docs
2. Test each endpoint interactively
3. See request/response in real-time
4. Validate error handling

---

## 🚀 Deployment

### Docker

```bash
# Build image
docker build -t bot-gpt-backend .

# Run container
docker run -p 8000:8000 --env-file .env bot-gpt-backend
```

### Docker Compose

```bash
docker-compose up -d
```

### CI/CD Pipeline

**GitHub Actions Workflow:**
1. Lint code (Black, Flake8)
2. Type check (MyPy)
3. Run tests (Pytest)
4. Build Docker image

**Triggers**: Push to `main`, Pull requests

---

## 💡 Design Decisions

### 1. Why Separate Chunks Collection?

**Instead of storing chunks in document:**
- ✅ Better scalability (millions of chunks)
- ✅ Faster queries (indexed separately)
- ✅ Memory efficient (load one chunk at a time)
- ✅ Easier to update embeddings

### 2. Why Background Processing?

**Instead of processing during upload:**
- ✅ Immediate response to user
- ✅ Server stays responsive
- ✅ Can handle large files
- ✅ Progress tracking

### 3. Why Cosine Similarity?

**Instead of vector database:**
- ✅ Simple implementation
- ✅ No external dependencies
- ✅ Works well for moderate scale
- ✅ Easy to understand and debug

**Future**: Can migrate to Pinecone/Chroma for larger scale

### 4. Why MongoDB?

**Instead of PostgreSQL:**
- ✅ Flexible schema (conversations evolve)
- ✅ Document model (natural for messages)
- ✅ Can store vectors as arrays
- ✅ Easy horizontal scaling

---

## 🔧 Challenges & Solutions

### Challenge 1: Server Freezing During Document Upload

**Problem**: Loading entire file + chunking + embedding in memory froze server

**Solution**:
1. Save file to disk immediately
2. Return response to user
3. Process in background (asyncio tasks)
4. Chunk and vectorize one at a time
5. Clear memory after each step

**Result**: Upload returns in <2 seconds, processing happens in background

### Challenge 2: Package Version Conflicts

**Problem**: `groq` and `google-genai` had conflicting dependencies

**Solution**:
- Updated `groq` to 0.11.0
- Updated `httpx` to 0.27.0
- Tested compatibility

### Challenge 3: Blocking I/O in Async Context

**Problem**: File reading and chunking blocked event loop

**Solution**:
- Used `asyncio.get_running_loop().run_in_executor()`
- Moved blocking operations to thread pool
- Server stays responsive

### Challenge 4: Token Context Management

**Problem**: Long conversations exceed LLM context window

**Solution**:
- Sliding window (last 10 messages)
- Token counting with tiktoken
- Auto-truncation when needed
- RAG: Only top 5 chunks

---

## 📂 Project Structure

```
bot-gpt-backend/
├── app/
│   ├── models/              # Pydantic models
│   │   ├── conversation.py
│   │   ├── message.py
│   │   └── document.py
│   ├── routes/              # API endpoints
│   │   ├── health.py
│   │   ├── conversations.py
│   │   └── documents.py
│   ├── services/            # Business logic
│   │   ├── database.py
│   │   ├── llm_service.py
│   │   ├── rag_service.py
│   │   ├── embedding_service.py
│   │   ├── conversation_service.py
│   │   └── vectorization_queue.py
│   ├── utils/               # Utilities
│   │   ├── token_counter.py
│   │   └── logger.py
│   └── config.py            # Configuration
├── tests/                   # Unit tests
├── uploads/                 # Uploaded documents
├── main.py                  # FastAPI app
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── README.md
└── DESIGN_DOCUMENT.md       # Detailed design doc
```

---

## 📊 Database Schema

### Collections

**1. conversations**
- Stores conversation metadata
- Indexes: `user_id`, `updated_at`

**2. messages**
- Individual messages (user + assistant)
- Indexes: `conversation_id`, `timestamp`

**3. documents**
- Document metadata + vectorization status
- Indexes: `user_id`, `is_vectorized`

**4. chunks**
- Document chunks with embeddings (768D vectors)
- Indexes: `document_id`, `is_vectorized`, compound index

---

## 🔒 Security

- ✅ Environment variables for secrets
- ✅ Non-root Docker user
- ✅ Input validation (Pydantic)
- ✅ CORS configuration
- ✅ Error messages without sensitive data
- ✅ No hardcoded credentials

---

## 📈 Scalability

### Current Architecture
- Stateless API (horizontal scaling ready)
- MongoDB Atlas (managed, auto-scaling)
- Connection pooling
- Background task processing

### Scaling Strategies

**At 1M Users:**

1. **API Layer**: Deploy multiple instances behind load balancer
2. **Database**: MongoDB sharding by `user_id`
3. **LLM Calls**: Request queue (Celery + Redis)
4. **File Storage**: Migrate to S3/Cloud Storage
5. **Caching**: Redis for recent conversations

---

## 🎓 What I Learned

1. **Async Python**: FastAPI's async/await, background tasks
2. **Vector RAG**: Embeddings, cosine similarity, retrieval
3. **Production Practices**: Docker, CI/CD, testing, logging
4. **LLM Integration**: Context management, token optimization
5. **MongoDB**: Document modeling, indexing, async operations
6. **Memory Management**: Background processing, disk-based storage

---

## 📞 Contact

**Fawad Ahmed**
- GitHub: [@Fawad1121](https://github.com/Fawad1121)
- Email: [Your Email]

---

## 🙏 Acknowledgments

- **BOT Consulting** for the case study opportunity
- **FastAPI** for the excellent framework
- **Groq** for free LLM API access
- **Google Gemini** for free embedding API
- **MongoDB Atlas** for managed database services

---

## 📄 Additional Documentation

- **Design Document**: See `DESIGN_DOCUMENT.md` for detailed architecture
- **Quick Start**: See `QUICK_START.md` for 3-step setup
- **API Docs**: http://localhost:8000/docs (when server is running)

---

**Built with ❤️ for BOT Consulting Case Study**

*This project demonstrates production-ready backend engineering, LLM integration, RAG implementation, and modern DevOps practices.*
