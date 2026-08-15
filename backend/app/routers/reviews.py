from fastapi import APIRouter, HTTPException
from app.services.review_service import analyze_product_reviews

router = APIRouter(prefix="/reviews", tags=["Review Intelligence"])


@router.get("/analyze/{product_id}")
def analyze_reviews(product_id: int):
    """Extract aspect-based sentiment summary for all reviews of a product."""
    result = analyze_product_reviews(product_id)
    if result["review_count"] == 0:
        raise HTTPException(status_code=404, detail=f"No reviews found for product_id {product_id}")
    return result
