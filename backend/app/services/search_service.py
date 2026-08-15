"""
Semantic Search Service — Module 1
Embeds product title+description using fastembed (lightweight, ONNX-based —
no PyTorch dependency, uses far less memory than sentence-transformers,
which is required to fit in free-tier hosting's 512MB RAM limit).
Stores vectors in Qdrant, and exposes a similarity search function.

Reads products from the database (populated via /ingest/migrate-csv
and /ingest/ebay) instead of directly from the CSV.
"""

import os
from fastembed import TextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from app.db import SessionLocal, init_db
from app.models import Product

# ---- Config ----
COLLECTION_NAME = "products"
EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"  # 384-dim, lightweight, free, good quality
EMBEDDING_DIM = 384
QDRANT_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "qdrant_local_db")

QDRANT_URL = os.getenv("QDRANT_URL", "")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")

# ---- Lazy-loaded singletons ----
_model = None
_client = None


def get_model() -> TextEmbedding:
    global _model
    if _model is None:
        _model = TextEmbedding(model_name=EMBEDDING_MODEL_NAME)
    return _model


def get_client() -> QdrantClient:
    global _client
    if _client is None:
        if QDRANT_URL:
            _client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
        else:
            _client = QdrantClient(path=QDRANT_PATH)
    return _client


def build_index():
    """Load all products from the database, embed each, and upsert into Qdrant."""
    init_db()
    db = SessionLocal()
    try:
        products = db.query(Product).all()
        if not products:
            return {"indexed_products": 0, "warning": "No products in DB yet — call /ingest/migrate-csv or /ingest/ebay first"}

        model = get_model()
        client = get_client()

        if client.collection_exists(COLLECTION_NAME):
            client.delete_collection(COLLECTION_NAME)
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
        )

        texts = [f"{p.title}. {p.description}" for p in products]
        embeddings = list(model.embed(texts))  # returns list of numpy arrays

        points = [
            PointStruct(
                id=p.id,
                vector=embeddings[i].tolist(),
                payload={
                    "title": p.title,
                    "description": p.description,
                    "category": p.category,
                    "price": p.price,
                    "brand": p.brand,
                    "source": p.source,
                    "url": p.url,
                },
            )
            for i, p in enumerate(products)
        ]

        client.upsert(collection_name=COLLECTION_NAME, points=points)
        return {"indexed_products": len(points)}
    finally:
        db.close()


def search_products(query: str, top_k: int = 5):
    """Embed the user's query and return the top_k most similar products."""
    model = get_model()
    client = get_client()

    query_vector = list(model.embed([query]))[0].tolist()

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=top_k,
    ).points

    return [
        {
            "id": r.id,
            "score": round(r.score, 4),
            **r.payload,
        }
        for r in results
    ]
