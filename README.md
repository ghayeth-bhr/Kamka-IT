# RAG Assistant

Document-grounded AI assistant with a LangChain tool-calling agent, Chroma vector store, and the all-MiniLM-L6-v2 embeddings model. The LLM is served via OpenRouter (GPT-4o-mini free tier by default).

---

## Prerequisites

- Python 3.11+
- Node.js 18+
- [OpenRouter API key](https://openrouter.ai/keys) (free tier available)

---

## Quick Start — Docker

```bash
git clone <repo-url> kamka
cd kamka

# Create .env files
cp backend/.env.example .env
cp .env backend/.env

# Edit .env — set OPENROUTER_API_KEY
```

```bash
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs

---

## Manual Setup

### Backend

```bash
cd backend
cp .env.example .env
# Edit .env — set OPENROUTER_API_KEY

python -m venv venv
# venv\Scripts\activate   (Windows)
# source venv/bin/activate (macOS/Linux)

pip install --index-url https://download.pytorch.org/whl/cpu torch==2.3.1+cpu
pip install -r requirements.txt

uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

Opens at http://localhost:3000.

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `OPENROUTER_API_KEY` | **Yes** | — | OpenRouter API key for LLM access |
| `LLM_MODEL` | No | `openai/gpt-4o-mini` | OpenRouter model identifier |
| `LLM_BASE_URL` | No | `https://openrouter.ai/api/v1` | API base URL |
| `EMBEDDINGS_MODEL` | No | `all-MiniLM-L6-v2` | Sentence-transformer model for embeddings |
| `HF_TOKEN` | No | — | Hugging Face token (for gated models only) |
| `CORS_ORIGINS` | No | `http://localhost:3000` | Comma-separated allowed CORS origins |
| `NEXT_PUBLIC_API_URL` | **Yes** (frontend) | — | Backend URL for the Next.js client |

---

## Project Structure

```
kamka/
├── .env                          # Shared env vars
├── docker-compose.yml            # Backend + frontend
├── backend/
│   ├── .env.example
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py               # FastAPI entry point
│       ├── config.py             # Pydantic settings
│       ├── api/routes/           # Chat & document upload endpoints
│       ├── core/agent/           # LangChain tool-calling agent
│       ├── core/rag/             # Ingestion, retrieval, prompts
│       ├── core/store/           # Chroma vector store wrapper
│       └── models/               # Pydantic schemas
└── frontend/
    ├── Dockerfile
    ├── package.json
    └── src/
        ├── app/                  # Next.js App Router
        ├── components/           # Chat, upload, message UI
        ├── hooks/                # useChat custom hook
        └── lib/                  # API client, types
```

---

## Usage

1. Open http://localhost:3000
2. Upload a PDF or .txt document via the upload panel
3. Ask questions in the chat — the agent retrieves relevant chunks and generates grounded answers with citations

---

## Architecture

| Component | Choice | Rationale |
|---|---|---|
| Vector store | Chroma (in-memory) | Zero-config, Python-native; ideal for demos |
| Embeddings | all-MiniLM-L6-v2 | Free, local, strong on English text |
| Chunking | RecursiveCharacterTextSplitter (1667/100) | Broader context for conversational Q&A |
| Retriever | Top-3 cosine similarity | Balances recall with context-window budget |
| Agent | LangChain `create_tool_calling_agent` | Native function-calling, clean tool routing |
| LLM proxy | OpenRouter | Model-agnostic access, free GPT-4o-mini tier |
| Docker torch | CPU-only (`--index-url .../cpu`) | Keeps image ~2.7 GB (CUDA adds no benefit) |

See `architecture.pdf` for a detailed discussion of design decisions, trade-offs, and known limitations.
