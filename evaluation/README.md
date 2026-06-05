# RAG Evaluation Dashboard

Standalone Gradio app that ingests documents, auto-generates test questions via LLM, and scores retrieval + answer quality. Runs in its own container, fully independent of the main RAG Assistant backend.

---

## Prerequisites

- Python 3.11+
- [OpenRouter API key](https://openrouter.ai/keys) (free tier available)

---

## Quick Start — Docker

```bash
cd evaluation
docker compose up --build
```

Open http://localhost:7860.

The evaluator reads `OPENROUTER_API_KEY` from `../.env` (project root). Make sure that file exists and contains the key.

---

## Manual Setup

```bash
cd evaluation

python -m venv venv
# venv\Scripts\activate   (Windows)
# source venv/bin/activate (macOS/Linux)

pip install --index-url https://download.pytorch.org/whl/cpu torch==2.3.1+cpu
pip install -r requirements.txt

python -m evaluation.evaluator
```

Opens at http://localhost:7860.

---

## Usage

The dashboard has a three-step workflow:

### Step 1 — Load Documents & Generate Tests

Upload PDF or .txt files, then click *Load & Generate Tests*. The system:
1. Chunks each document (800 tokens, 100 overlap)
2. Embeds chunks with all-MiniLM-L6-v2 and stores them in Chroma
3. Sends sampled chunks to the LLM to generate test questions with expected keywords

Generated questions appear in a preview table with their category and keywords.

### Step 2 — Retrieval Evaluation

Click *Run Retrieval Evaluation*. For each test question, the system:
1. Retrieves the top-6 chunks from Chroma
2. Checks how many expected keywords appear in the retrieved chunks
3. Computes MRR (Mean Reciprocal Rank), nDCG (Normalized Discounted Cumulative Gain), and keyword-coverage percentage

Results are shown per-category.

### Step 3 — Answer Evaluation

Click *Run Answer Evaluation*. For each test question, the system:
1. Generates an answer using the same RAG pipeline
2. Asks the LLM to judge the answer on accuracy, completeness, and relevance (1–5 scale)

Results are shown per-category.

---

## Project Structure

```
evaluation/
├── docker-compose.yml       # Standalone Docker setup
├── Dockerfile               # CPU-only torch, python:3.11-slim
├── requirements.txt         # Pinned Python dependencies
├── evaluator.py             # Gradio UI, callbacks, event wiring
├── rag_core.py              # RAG primitives (ingest, retrieve, answer) via litellm
├── eval.py                  # MRR, nDCG, keyword coverage, LLM judge
├── test_generator.py        # LLM-based test question generation
├── session.py               # Per-browser session store singleton
└── test.py                  # TestQuestion Pydantic model
```

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `OPENROUTER_API_KEY` | **Yes** | — | OpenRouter API key for LLM + judge |
| `LLM_MODEL` | No | `openai/gpt-4o-mini` | Model for question gen and answer judging |
| `LLM_BASE_URL` | No | `https://openrouter.ai/api/v1` | API base URL |
| `EMBEDDINGS_MODEL` | No | `all-MiniLM-L6-v2` | Sentence-transformer model |

All variables are read from `../.env` (project root) via `python-dotenv`.

---

## Architecture Notes

| Component | Choice | Rationale |
|---|---|---|
| UI framework | Gradio 6.15 | Rapid prototyping, built-in state, file upload |
| LLM client | litellm | Direct API calls to avoid `openai` SDK conflict with main backend |
| Vector store | Chroma (in-memory) | Zero-config, per-session isolation |
| Chunking | RecursiveCharacterTextSplitter (800/100) | Tighter precision for retrieval metrics |
| Retriever | Top-6 cosine similarity | Higher recall for sensitivity in metrics |
| Session store | Python singleton (`gr.State`) | Per-browser isolation without a database |

See `architecture.pdf` for a detailed discussion of design decisions and trade-offs.
