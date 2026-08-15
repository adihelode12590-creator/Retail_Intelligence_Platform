"""
Real-time product ingestion from eBay's Browse API.

Setup:
1. Sign up at https://developer.ebay.com (free)
2. Create an application -> get Client ID + Client Secret (from the
   'Production' keyset once your app is approved, or 'Sandbox' keyset for
   testing immediately without approval delay)
3. Set environment variables:
       EBAY_CLIENT_ID
       EBAY_CLIENT_SECRET

eBay uses OAuth2 client-credentials flow for the Browse API (app-level
access, no user login needed) — we fetch a short-lived access token, then
use it to search live listings.
"""

import os
import base64
import time
import requests
from sqlalchemy.orm import Session
from app.models import Product

EBAY_CLIENT_ID = os.getenv("EBAY_CLIENT_ID", "")
EBAY_CLIENT_SECRET = os.getenv("EBAY_CLIENT_SECRET", "")

# Use sandbox by default (works instantly after signup, no approval wait).
# Switch to production endpoints once your app is approved for live data:
#   token url -> https://api.ebay.com/identity/v1/oauth2/token
#   search url -> https://api.ebay.com/buy/browse/v1/item_summary/search
EBAY_TOKEN_URL = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"
EBAY_SEARCH_URL = "https://api.sandbox.ebay.com/buy/browse/v1/item_summary/search"

_token_cache = {"access_token": None, "expires_at": 0}


def ebay_configured() -> bool:
    return bool(EBAY_CLIENT_ID and EBAY_CLIENT_SECRET)


def get_ebay_token() -> str:
    """Get a cached OAuth token, refreshing if expired."""
    if _token_cache["access_token"] and time.time() < _token_cache["expires_at"]:
        return _token_cache["access_token"]

    credentials = f"{EBAY_CLIENT_ID}:{EBAY_CLIENT_SECRET}"
    encoded = base64.b64encode(credentials.encode()).decode()

    headers = {
        "Authorization": f"Basic {encoded}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "grant_type": "client_credentials",
        "scope": "https://api.ebay.com/oauth/api_scope",
    }

    response = requests.post(EBAY_TOKEN_URL, headers=headers, data=data, timeout=15)
    response.raise_for_status()
    token_data = response.json()

    _token_cache["access_token"] = token_data["access_token"]
    _token_cache["expires_at"] = time.time() + token_data.get("expires_in", 7200) - 60
    return _token_cache["access_token"]


def fetch_ebay_products(query: str, limit: int = 10):
    """Search eBay's live catalog and return normalized product dicts."""
    token = get_ebay_token()
    headers = {"Authorization": f"Bearer {token}"}
    params = {"q": query, "limit": limit}

    response = requests.get(EBAY_SEARCH_URL, headers=headers, params=params, timeout=15)
    response.raise_for_status()
    items = response.json().get("itemSummaries", [])

    normalized = []
    for item in items:
        normalized.append({
            "external_id": item.get("itemId"),
            "source": "ebay",
            "title": item.get("title", "Untitled"),
            "description": item.get("shortDescription", item.get("title", "")),
            "category": item.get("categories", [{}])[0].get("categoryName", "General") if item.get("categories") else "General",
            "price": float(item.get("price", {}).get("value", 0)),
            "brand": item.get("seller", {}).get("username", "Unknown"),
            "url": item.get("itemWebUrl"),
        })
    return normalized


def save_products_to_db(products: list, db: Session):
    """Upsert fetched products into the database (update if external_id exists, else insert)."""
    saved_count = 0
    for p in products:
        existing = db.query(Product).filter(Product.external_id == p["external_id"]).first()
        if existing:
            for key, value in p.items():
                setattr(existing, key, value)
        else:
            db.add(Product(**p))
        saved_count += 1
    db.commit()
    return saved_count
