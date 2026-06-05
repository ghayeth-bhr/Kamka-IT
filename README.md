# RAG Assistant

## Overview
Document-grounded AI assistant built with a LangChain tool-calling agent, Chroma
vector store, and the all-MiniLM-L6-v2 embeddings model. The backend is FastAPI
and the frontend is Next.js with Tailwind CSS. The LLM is served via OpenRouter
using the GPT-4o-mini free tier by default.

## Prerequisites
- Python 3.11+
- Node.js 18+
- An OpenRouter API key

## Setup

### Backend
cd backend
cp .env.example .env
# fill in OPENROUTER_API_KEY
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

### Frontend
cd frontend
cp .env.local.example .env.local
# NEXT_PUBLIC_API_URL=http://localhost:8000
npm install
npm run dev

## Environment Variables
| Variable | Required | Description |
| --- | --- | --- |
| OPENROUTER_API_KEY | yes | OpenRouter API key for the LLM |
| HF_TOKEN | no | Hugging Face token (only for gated models) |
| LLM_MODEL | no | OpenRouter model name (default: openai/gpt-4o-mini) |
| LLM_BASE_URL | no | OpenRouter base URL |
| EMBEDDINGS_MODEL | no | Embeddings model name (default: all-MiniLM-L6-v2) |
| CORS_ORIGINS | no | Comma-separated allowed CORS origins |
| NEXT_PUBLIC_API_URL | yes (frontend) | Backend base URL for the UI |

## Architecture
This app implements a standard RAG flow: documents are chunked, embedded, and
stored in Chroma. A LangChain tool-calling agent retrieves relevant chunks and
generates grounded answers with citations. The default chunking parameters are
800/100 to preserve table structure while maintaining retrieval precision.

Key decisions:
- Chroma: lightweight, in-memory store for demo scope
- all-MiniLM-L6-v2: free, local, strong on English text
- RecursiveCharacterTextSplitter(800, 100): balances table integrity vs retrieval precision
- create_tool_calling_agent: native function-calling with clean tool routing
- OpenRouter: model-agnostic access with free GPT-4o-mini tier

## API Reference
FastAPI docs available at http://localhost:8000/docs

## Known Limitations and Next Steps
- Vector store is in-memory and resets on server restart; add persistence
- Single-user only; add authentication and per-user collections
