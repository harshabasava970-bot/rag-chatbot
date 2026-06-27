# DocChat — AI Document Search

A production-ready **Retrieval-Augmented Generation (RAG)** chatbot that lets you upload PDF documents and ask questions about them in natural language.

**100% free to run** — uses Groq (free LLM API), sentence-transformers (local embeddings), and FAISS (local vector store).

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, TailwindCSS, TanStack Query |
| Backend | FastAPI, Python 3.12 |
| LLM | Groq API — `llama-3.3-70b-versatile` (free tier) |
| Embeddings | `all-MiniLM-L6-v2` via sentence-transformers (local, free) |
| Vector Store | FAISS (local file, free) |
| PDF Processing | PyMuPDF (fitz) |

---

## Quick Start (Local Dev)

### 1. Backend

```bash
cd backend

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and set GROQ_API_KEY (free at https://console.groq.com)

# Run the API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Frontend

```bash
cd frontend

npm install
npm run dev
# Open http://localhost:5173
```

---

## Docker (Full Stack)

```bash
# Copy and configure the backend env
cp backend/.env.example backend/.env
# Set GROQ_API_KEY in backend/.env

docker-compose up --build
# Backend: http://localhost:8000
# API docs: http://localhost:8000/docs
```

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Default | Description |
|---|---|---|
| `GROQ_API_KEY` | *(required)* | Free key from [console.groq.com](https://console.groq.com) |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Groq model to use |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | HuggingFace embedding model |
| `APP_PORT` | `8000` | Server port |
| `ALLOWED_ORIGINS` | `http://localhost:5173` | CORS origins (comma-separated) |
| `UPLOAD_DIR` | `./uploads` | Where PDFs and FAISS index are stored |
| `MAX_FILE_SIZE_MB` | `50` | Max PDF size |
| `CHUNK_SIZE` | `1000` | Characters per text chunk |
| `CHUNK_OVERLAP` | `200` | Overlap between chunks |
| `TOP_K_RESULTS` | `5` | Number of chunks retrieved per query |

### Frontend (`frontend/.env`)

| Variable | Default | Description |
|---|---|---|
| `VITE_API_URL` | *(empty)* | Backend URL (empty = use Vite proxy locally) |

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/upload` | Upload and process a PDF |
| `GET` | `/api/v1/documents` | List all uploaded documents |
| `DELETE` | `/api/v1/documents/{id}` | Delete a document |
| `POST` | `/api/v1/chat` | Ask a question (RAG query) |
| `GET` | `/api/v1/health` | System health check |

Interactive API docs available at `/docs` when the backend is running.

---

## Deployment

### Frontend → Vercel

```bash
cd frontend
# Set VITE_API_URL to your deployed backend URL in Vercel environment variables
vercel deploy
```

### Backend → Render / Railway / Fly.io

1. Point to the `backend/` directory
2. Set all environment variables from `.env.example`
3. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

> Note: Add your deployed frontend URL to `ALLOWED_ORIGINS` in the backend config.

---

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── api/routes.py          # FastAPI route handlers
│   │   ├── models/schemas.py      # Pydantic request/response models
│   │   ├── rag/pipeline.py        # RAG pipeline (retrieve → generate → cite)
│   │   ├── services/
│   │   │   ├── document_store.py  # JSON-backed document metadata store
│   │   │   ├── pdf_processor.py   # PDF text extraction + chunking
│   │   │   └── vector_store.py    # FAISS embeddings + similarity search
│   │   ├── utils/
│   │   │   ├── config.py          # Pydantic settings (env vars)
│   │   │   └── logger.py          # Structured logger
│   │   └── main.py                # FastAPI app factory
│   ├── requirements.txt
│   └── Dockerfile
│
└── frontend/
    ├── src/
    │   ├── components/            # UI components
    │   ├── hooks/                 # React hooks (useChat, useDocuments, useDarkMode)
    │   ├── services/api.js        # Axios API client
    │   └── App.jsx                # Root layout
    └── package.json
```
