import pandas as pd
import os
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db, init_db
from app.models import Product
from app.services.ebay_service import fetch_ebay_products, save_products_to_db, ebay_configured

router = APIRouter(prefix="/ingest", tags=["Data Ingestion"])

CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "products.csv")


@router.post("/migrate-csv")
def migrate_csv(db: Session = Depends(get_db)):
    """One-time: load the original demo products.csv into the database."""
    init_db()
    df = pd.read_csv(CSV_PATH)
    count = 0
    for _, row in df.iterrows():
        existing = db.query(Product).filter(
            Product.source == "csv", Product.title == row["title"]
        ).first()
        if not existing:
            db.add(Product(
                source="csv",
                title=row["title"],
                description=row["description"],
                category=row["category"],
                price=float(row["price"]),
                brand=row["brand"],
            ))
            count += 1
    db.commit()
    return {"status": "success", "migrated": count}


@router.post("/ebay")
def ingest_from_ebay(
    query: str = Query(..., description="Search term, e.g. 'wireless earbuds'"),
    limit: int = Query(10, le=50),
    db: Session = Depends(get_db),
):
    """Pull live product listings from eBay's Browse API and save to the database."""
    if not ebay_configured():
        raise HTTPException(
            status_code=400,
            detail="EBAY_CLIENT_ID and EBAY_CLIENT_SECRET environment variables not set. "
                   "Get free keys at https://developer.ebay.com",
        )
    init_db()
    products = fetch_ebay_products(query, limit=limit)
    saved = save_products_to_db(products, db)
    return {"status": "success", "query": query, "products_saved": saved}


@router.get("/status")
def ingestion_status(db: Session = Depends(get_db)):
    """Quick check: how many products from each source are in the DB."""
    init_db()
    total = db.query(Product).count()
    csv_count = db.query(Product).filter(Product.source == "csv").count()
    ebay_count = db.query(Product).filter(Product.source == "ebay").count()
    return {"total_products": total, "from_csv": csv_count, "from_ebay": ebay_count}
