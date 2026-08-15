from fastapi import APIRouter, Query
from app.services.search_service import build_index, search_products

router = APIRouter(prefix="/search", tags=["Semantic Search"])


@router.post("/build-index")
def build_index_endpoint():
    """One-time (or on-demand) endpoint to embed products.csv and load into Qdrant."""
    result = build_index()
    return {"status": "success", **result}


@router.get("")
def search(q: str = Query(..., description="Natural language search query"), top_k: int = 5):
    """Semantic product search — pass any natural language query."""
    results = search_products(q, top_k=top_k)
    return {"query": q, "results": results}
