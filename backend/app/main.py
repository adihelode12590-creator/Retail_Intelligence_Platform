from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import search, reviews, chat, ingest

app = FastAPI(
    title="Retail Intelligence Platform API",
    description="Module 1: Semantic Search (Phase 1 MVP)",
    version="0.1.0",
)

# Allow frontend (React/Streamlit) to call this API during local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router)
app.include_router(reviews.router)
app.include_router(chat.router)
app.include_router(ingest.router)


@app.get("/")
def root():
    return {"status": "ok", "message": "Retail Intelligence Platform API is running"}


@app.get("/health")
def health():
    return {"status": "healthy"}
