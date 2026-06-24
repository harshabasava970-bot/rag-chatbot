# DocChat – AI Document Search (RAG Chatbot)

A production-ready **Retrieval-Augmented Generation (RAG)** application that lets you upload PDF documents and ask natural-language questions about their contents.

![Tech Stack](https://img.shields.io/badge/FastAPI-0.111-green) ![React](https://img.shields.io/badge/React-18-blue) ![LangChain](https://img.shields.io/badge/LangChain-0.2-purple) ![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-orange)

---

## Features

| Feature | Details |
|---|---|
| PDF Upload | Drag-and-drop, multiple files, up to 50 MB each |
| Text Extraction | PyMuPDF with page-level metadata |
| Intelligent Chunking | Recursive character splitting (1000 chars, 200 overlap) |
| Embeddings | OpenAI `text-embedding-3-small` |
| Vector Store | Pinecone (cloud) or FAISS (local fallback) |
| LLM | OpenAI `gpt-4o-mini` (configurable) |
| Conversation Memory | Last 10 turns sent with every request |
| Source Citations | Each answer includes ranked source chunks |
| Dark Mode | System preference + manual toggle |
| Responsive UI | Tailwind CSS, works on mobile |

---

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── api/routes.py          # All FastAPI endpoints
│   │   ├── models/schemas.py      # Pydantic request/response models
│   │   ├── rag/pipeline.py        # RAG retrieval + generation logic
│   │   ├── services/
│   │   │   ├── document_store.py  # Document metadata persistence
│   │   │   ├── pdf_processor.py   # PDF extraction + chunking
│   │   │   └── vector_store.py    # Pinecone / FAISS abstraction
│   │   ├── utils/
│   │   │   ├── config.py          # Settings (pydantic-settings)
│   │   │   └── logger.py          # Structured logger
│   │   └── main.py                # FastAPI app factory
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/            # React UI components
│   │   ├── hooks/                 # React Query + state hooks
│   │   ├── services/api.js        # Axios API client
│   │   └── App.jsx
│   ├── package.json
│   ├── vite.config.js
│   └── vercel.json
├── docker-compose.yml
└── README.md
```

---

## Quick Start (Local Development)

### Prerequisites

- Python 3.11+
- Node.js 18+
- An OpenAI API key

### 1. Clone & configure

```bash
git clone https://github.com/harshabasava970-bot/rag-chatbot.git
cd rag-chatbot
```

### 2. Backend setup

```bash
cd backend

# Create virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env – at minimum set OPENAI_API_KEY
```

### 3. Start the backend

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs are available at: http://localhost:8000/docs

### 4. Frontend setup

```bash
cd ../frontend
npm install
cp .env.example .env
# Leave VITE_API_URL empty for local dev (Vite proxy handles it)
npm run dev
```

Open http://localhost:5173 in your browser.

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | ✅ | Your OpenAI secret key |
| `OPENAI_MODEL` | | LLM model (default: `gpt-4o-mini`) |
| `OPENAI_EMBEDDING_MODEL` | | Embedding model (default: `text-embedding-3-small`) |
| `PINECONE_API_KEY` | ⚠️ optional | Enables Pinecone; falls back to FAISS if unset |
| `PINECONE_ENVIRONMENT` | ⚠️ optional | Pinecone cloud region (e.g. `us-east-1`) |
| `PINECONE_INDEX_NAME` | | Index name (default: `rag-documents`) |
| `ALLOWED_ORIGINS` | | Comma-separated CORS origins |
| `CHUNK_SIZE` | | Token chunk size (default: `1000`) |
| `CHUNK_OVERLAP` | | Chunk overlap (default: `200`) |
| `TOP_K_RESULTS` | | Default retrieval count (default: `5`) |

### Frontend (`frontend/.env`)

| Variable | Description |
|---|---|
| `VITE_API_URL` | Backend base URL for production. Leave empty for local dev. |

---

## API Reference

All endpoints are prefixed with `/api/v1`.

### `GET /health`
Returns system status, vector store type, OpenAI connectivity, and document count.

### `GET /documents`
Returns list of all uploaded documents with metadata.

### `POST /upload`
Upload a PDF file (multipart/form-data, field name `file`).  
Returns `document_id`, page count, chunk count.

### `DELETE /documents/{id}`
Deletes document metadata, file, and all vector embeddings.

### `POST /chat`
```json
{
  "query": "What is the main topic of the report?",
  "conversation_history": [],
  "document_ids": null,
  "top_k": 5
}
```
Returns answer text and ranked source chunks.

---

## Docker Deployment

### Build and run

```bash
# Copy and fill in environment variables
cp backend/.env.example backend/.env
# Edit backend/.env

docker-compose up --build -d
```

The API will be available at http://localhost:8000.

### Check health

```bash
curl http://localhost:8000/api/v1/health
```

### Stop

```bash
docker-compose down
```

Data (uploads + FAISS index) is persisted in the `uploads_data` Docker volume.

---

## Vercel Deployment (Frontend)

1. Push the repository to GitHub.
2. Go to [vercel.com](https://vercel.com) → New Project → import your repo.
3. Set **Root Directory** to `frontend`.
4. Add environment variable:
   - `VITE_API_URL` = your backend URL (e.g. `https://your-backend.fly.dev`)
5. Click **Deploy**.

The `vercel.json` in `frontend/` already configures SPA routing rewrites.

---

## Backend Cloud Deployment (Docker)

The backend can be deployed to any service that runs Docker containers:

- **Fly.io**: `fly launch` from the `backend/` directory
- **Railway**: connect repo, set root to `backend/`, add env vars
- **Render**: New Web Service → Docker → add env vars
- **AWS ECS / Google Cloud Run**: push the Docker image and configure env vars

Ensure `ALLOWED_ORIGINS` includes your Vercel frontend URL.

---

## Architecture

```
User → React (Vite)
         │  POST /chat
         ▼
      FastAPI ──→ OpenAI Embeddings ──→ Pinecone / FAISS
         │                                    │
         │          similarity_search         │
         │ ◄──────────────────────────────────┘
         │
         │  top-K chunks + conversation history
         ▼
      ChatOpenAI (gpt-4o-mini) → grounded answer + citations
         │
         ▼
      React chat bubble with collapsible sources
```

---

## License

MIT
