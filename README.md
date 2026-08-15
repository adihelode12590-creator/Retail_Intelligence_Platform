# Retail Intelligence Platform

Phase 1 MVP — Module 1: Semantic Search (built first, more modules coming)

## Project Structure
```
retail-intelligence-platform/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI entrypoint
│   │   ├── routers/
│   │   │   └── search.py            # /search endpoints
│   │   └── services/
│   │       └── search_service.py    # embedding + Qdrant logic
│   ├── data/
│   │   └── products.csv             # sample product dataset (15 items)
│   └── requirements.txt
└── frontend/                        # (coming in a later module)
```

## Setup (run on your own machine — needs internet access to download the embedding model)

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Run the API

```bash
uvicorn app.main:app --reload --port 8000
```

Visit interactive docs: http://localhost:8000/docs

## Build the search index (one-time, or whenever products.csv changes)

Call this endpoint once before searching:
```
POST http://localhost:8000/search/build-index
```
or with curl:
```bash
curl -X POST http://localhost:8000/search/build-index
```
This downloads the `all-MiniLM-L6-v2` embedding model (~80MB, first run only, needs internet), embeds all products in `products.csv`, and stores vectors in a local Qdrant database (`backend/qdrant_local_db/` — auto-created, no separate server needed).

## Search

```
GET http://localhost:8000/search?q=something to keep my drink cold&top_k=5
```

Try queries like:
- "shoes for jogging"
- "something to carry my laptop to office"
- "cookware that doesn't stick"
- "gift for someone who works out"

Notice these aren't exact keyword matches — that's the point of semantic search, it matches meaning, not just words.

## Module 2: Review Intelligence Engine

Extracts aspect-based sentiment from reviews (e.g. "battery: negative, comfort: positive") and aggregates per product.

### Setup (recommended — free, ~2 minutes)
1. Get a free Groq API key: https://console.groq.com/keys
2. Set it as an environment variable before starting the server:
   - Windows (PowerShell): `$env:GROQ_API_KEY="your_key_here"`
   - Mac/Linux: `export GROQ_API_KEY="your_key_here"`
3. Restart `uvicorn`

Without a key, it still runs using a basic keyword-matching fallback (works, but much less accurate — real LLM mode understands context, fallback just counts words).

### Try it
```
GET http://localhost:8000/reviews/analyze/1
GET http://localhost:8000/reviews/analyze/5
GET http://localhost:8000/reviews/analyze/15
```
(product_id 1, 2, 5, 6, 15 have sample reviews in `data/reviews.csv`)

The response's `"mode"` field tells you whether it used the real LLM or fallback.

- ✅ Full FastAPI + Qdrant + sentence-transformers pipeline structured and logic-tested
- ✅ Qdrant vector storage/search mechanics tested and working (see dev notes)
- ⚠️ Embedding model download requires internet access — run `pip install` + first API call on your own machine, not in a network-restricted sandbox

