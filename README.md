# BOT GPT Backend

A production-grade conversational AI backend platform supporting both open chat and RAG-based (Retrieval-Augmented Generation) conversations with external LLM integration.

## 🚀 Features

- **Dual Conversation Modes**
  - **Open Chat**: Direct conversation with LLM
  - **RAG Mode**: Document-grounded conversations with context retrieval

- **RESTful API**
  - Full CRUD operations for conversations
  - Document upload and management
  - Pagination support
  - Comprehensive error handling

- **LLM Integration**
  - Groq API integration with Llama 3 models
  - Automatic context window management
  - Token counting and optimization
  - Retry logic with exponential backoff

- **RAG Capabilities**
  - Document chunking with overlap
  - Keyword-based retrieval
  - Context injection for grounded responses

- **Production Ready**
  - Docker containerization
  - CI/CD pipeline with GitHub Actions
  - Comprehensive unit tests
  - Structured logging
  - Health check endpoints

## 📋 Prerequisites

- Python 3.11+
- MongoDB Atlas account (free tier)
- Groq API key (free tier)
- Git

## 🛠️ Tech Stack

- **Backend**: FastAPI
- **Database**: MongoDB Atlas
- **LLM**: Groq API (Llama 3)
- **Testing**: Pytest
- **Containerization**: Docker
- **CI/CD**: GitHub Actions

## 📦 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Fawad1121/bot-gpt-backend.git
cd bot-gpt-backend
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Configuration

Copy `.env.example` to `.env` and update with your credentials:

```bash
cp .env.example .env
```

Edit `.env`:

```env
MONGODB_URI=your_mongodb_atlas_connection_string
GROQ_API_KEY=your_groq_api_key
```

## 🚀 Running the Application

### Local Development

```bash
# Activate virtual environment first
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

- **API Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### Using Docker

```bash
# Build and run
docker build -t bot-gpt-backend .
docker run -p 8000:8000 --env-file .env bot-gpt-backend
```

### Using Docker Compose

```bash
docker-compose up -d
```

## 📚 API Documentation

### Conversations

#### Create Conversation
```http
POST /api/v1/conversations
Content-Type: application/json

{
  "user_id": "user123",
  "message": "Hello, how are you?",
  "mode": "open_chat"
}
```

#### List Conversations
```http
GET /api/v1/conversations?user_id=user123&limit=20&offset=0
```

#### Get Conversation
```http
GET /api/v1/conversations/{conversation_id}
```

#### Add Message
```http
POST /api/v1/conversations/{conversation_id}/messages
Content-Type: application/json

{
  "message": "Tell me more"
}
```

#### Delete Conversation
```http
DELETE /api/v1/conversations/{conversation_id}
```

### Documents (RAG)

#### Upload Document
```http
POST /api/v1/documents
Content-Type: multipart/form-data

file: <file>
user_id: user123
```

#### List Documents
```http
GET /api/v1/documents?user_id=user123&limit=20&offset=0
```

#### Get Document
```http
GET /api/v1/documents/{document_id}?include_content=false
```

#### Delete Document
```http
DELETE /api/v1/documents/{document_id}
```

## 🧪 Testing

### Run All Tests

```bash
pytest tests/ -v
```

### Run with Coverage

```bash
pytest tests/ -v --cov=app --cov-report=html
```

### Run Specific Test File

```bash
pytest tests/test_api.py -v
```

## 🏗️ Project Structure

```
bot-gpt-backend/
├── app/
│   ├── __init__.py
│   ├── config.py                 # Configuration management
│   ├── models/                   # Pydantic models
│   │   ├── user.py
│   │   ├── conversation.py
│   │   ├── message.py
│   │   └── document.py
│   ├── routes/                   # API endpoints
│   │   ├── health.py
│   │   ├── conversations.py
│   │   └── documents.py
│   ├── services/                 # Business logic
│   │   ├── database.py
│   │   ├── llm_service.py
│   │   ├── rag_service.py
│   │   └── conversation_service.py
│   └── utils/                    # Utilities
│       ├── token_counter.py
│       └── logger.py
├── tests/                        # Unit tests
├── main.py                       # FastAPI app entry point
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MONGODB_URI` | MongoDB connection string | Required |
| `GROQ_API_KEY` | Groq API key | Required |
| `DATABASE_NAME` | MongoDB database name | `bot_gpt_db` |
| `DEFAULT_MODEL` | LLM model to use | `llama-3.1-70b-versatile` |
| `MAX_TOKENS` | Max tokens per response | `2048` |
| `TEMPERATURE` | LLM temperature | `0.7` |
| `CONTEXT_WINDOW_SIZE` | Max context tokens | `6000` |
| `DEBUG` | Debug mode | `True` |
| `LOG_LEVEL` | Logging level | `INFO` |

## 📊 Architecture

### High-Level Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────┐
│   FastAPI REST API          │
│   - CORS Middleware         │
│   - Request Validation      │
└──────┬──────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│   Service Layer             │
│   - Conversation Service    │
│   - LLM Service (Groq)      │
│   - RAG Service             │
│   - Database Service        │
└──────┬──────────────────────┘
       │
       ├──────────────┬─────────────┐
       ▼              ▼             ▼
┌────────────┐  ┌──────────┐  ┌──────────┐
│  MongoDB   │  │ Groq API │  │   RAG    │
│   Atlas    │  │  (LLM)   │  │ Retrieval│
└────────────┘  └──────────┘  └──────────┘
```

### Data Models

- **User**: User accounts and metadata
- **Conversation**: Chat sessions with mode and metadata
- **Message**: Individual messages with role and tokens
- **Document**: Uploaded documents with chunks for RAG

### Context Management

- **Token Counting**: Uses tiktoken for accurate token estimation
- **Sliding Window**: Keeps last N messages to fit context
- **Smart Truncation**: Preserves system prompts and recent context
- **RAG Context**: Limits retrieved chunks to prevent overflow

## 🔒 Security

- Non-root Docker user
- Environment variable management
- Input validation with Pydantic
- CORS configuration
- Error handling without sensitive data exposure

## 📈 Scalability

### Current Architecture
- Stateless API (easy horizontal scaling)
- MongoDB Atlas (managed, auto-scaling)
- Connection pooling

### Scaling Strategies
- **API Layer**: Deploy multiple instances behind load balancer
- **Database**: MongoDB sharding by user_id
- **LLM**: Request queuing, multiple API keys
- **Storage**: Archive old conversations to cold storage

## 🐛 Error Handling

- LLM API timeouts: Retry with exponential backoff
- Database failures: Connection pooling with auto-reconnect
- Token limit breaches: Automatic truncation
- Validation errors: Detailed error messages

## 📝 Development

### Code Quality

```bash
# Format code
black app/

# Lint
flake8 app/

# Type check
mypy app/ --ignore-missing-imports
```

### Adding New Features

1. Create feature branch
2. Implement changes
3. Add tests
4. Update documentation
5. Create pull request

## 🚀 Deployment

### GitHub Actions CI/CD

The project includes a GitHub Actions workflow that:
- Runs linting (flake8, black)
- Performs type checking (mypy)
- Executes tests with coverage
- Builds Docker image

### Manual Deployment

1. Build Docker image
2. Push to container registry
3. Deploy to cloud platform (AWS ECS, GCP Cloud Run, etc.)
4. Set environment variables
5. Configure load balancer

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is created for the BOT Consulting case study.

## 👤 Author

**Fawad Ahmed**
- GitHub: [@Fawad1121](https://github.com/Fawad1121)

## 🙏 Acknowledgments

- BOT Consulting for the case study opportunity
- FastAPI for the excellent framework
- Groq for providing free LLM API access
- MongoDB Atlas for managed database services

## 📞 Support

For questions or issues, please open an issue on GitHub or contact the development team.

---

**Built with ❤️ for BOT Consulting Case Study**
