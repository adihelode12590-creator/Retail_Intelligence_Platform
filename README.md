# Retail Intelligence Platform

An AI-powered retail platform combining **semantic search**, **LLM-based review intelligence**, and a **RAG shopping copilot** — with a real-time product ingestion pipeline and full deployment.

---

## What it does

| Module | Description |
|---|---|
| **Semantic Search** | Natural-language product search using vector embeddings (FastEmbed + Qdrant) — understands meaning, not just keywords |
| **Review Intelligence** | LLM-based aspect extraction (Groq/Llama) — surfaces what customers actually like/dislike per feature, with sentiment breakdown |
| **AI Shopping Copilot** | RAG chatbot answering product questions, grounded in real search + review data — cites sources, never hallucinates |
| **Real-Time Ingestion** | Live product data pulled from eBay's Browse API (OAuth2), normalized and stored in PostgreSQL alongside demo data |

## How it works

FastAPI backend connects to: **PostgreSQL** (stores product/review data), **Qdrant** (vector search index), **Groq/Llama** (LLM for sentiment + chat), and **eBay's Browse API** (real-time product ingestion). The Streamlit frontend calls the backend's REST API.
## Tech Stack

`Python` · `FastAPI` · `Streamlit` · `FastEmbed` · `Qdrant` · `PostgreSQL` · `SQLAlchemy` · `Groq (Llama 3)` · `Docker` · `Render`

## Run Locally

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Set these environment variables for full functionality (falls back gracefully without them):
GROQ_API_KEY= # free at console.groq.com
EBAY_CLIENT_ID= # free at developer.ebay.com
EBAY_CLIENT_SECRET=
QDRANT_URL= # optional — defaults to local storage
QDRANT_API_KEY=
DATABASE_URL= # optional — defaults to local SQLite
Then initialize data: `POST /ingest/migrate-csv` → `POST /search/build-index`

## Deployment

Fully containerized, deployed on Render (backend + frontend as separate services).

## Roadmap

- [x] Semantic Search
- [x] Review Intelligence Engine
- [x] AI Shopping Copilot (RAG)
- [x] Real-Time Ingestion (eBay API)
- [x] Deployment (Docker + Render)
- [ ] Image Search (CLIP)
- [ ] Product Recommendations
- [ ] Cross-Platform Price Comparison
