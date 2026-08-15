"""
Review Intelligence Engine — Module 2

Extracts (aspect, sentiment) pairs from raw customer reviews using an LLM
(few-shot prompting), then aggregates them per product into a structured
summary like: "Battery: 70% negative | Sound: 90% positive".

Falls back to a simple keyword-based extractor if no LLM API key is
configured, so the pipeline is testable without any setup.
"""

import os
import pandas as pd
from collections import defaultdict
from app.services.llm_client import call_llm, extract_json, llm_available

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "reviews.csv")

ASPECT_EXTRACTION_PROMPT = """You are analyzing a customer product review.
Extract every distinct product aspect mentioned (e.g. battery, sound quality,
comfort, price, build quality, sizing) along with the sentiment expressed
about that aspect: "positive", "negative", or "neutral".

Review: "{review_text}"

Respond with ONLY a JSON array, no other text, in this exact format:
[{{"aspect": "battery", "sentiment": "negative"}}, {{"aspect": "sound quality", "sentiment": "positive"}}]

If no clear aspect is mentioned, respond with an empty array: []
"""

# ---- Fallback rule-based extractor (used if no LLM API key is set) ----
POSITIVE_WORDS = {"great", "amazing", "excellent", "good", "comfortable", "perfect",
                   "sturdy", "accurate", "helpful", "premium", "effortless", "crisp",
                   "breathable", "safe", "lightweight"}
NEGATIVE_WORDS = {"disappointing", "flimsy", "fast", "small", "hard", "frustrating",
                   "dropping", "wearing", "peeling", "drains", "barely"}

FALLBACK_ASPECT_KEYWORDS = {
    "battery": ["battery"], "sound": ["sound", "bass", "audio"],
    "comfort": ["comfortable", "comfort", "fit"], "build quality": ["sturdy", "flimsy", "build", "zippers"],
    "sizing": ["sizing", "size", "small", "large"], "connectivity": ["connectivity", "syncs", "dropping"],
    "screen": ["screen"], "price": ["price"], "durability": ["wearing", "peeling", "months"],
}


def fallback_extract(review_text: str):
    text_lower = review_text.lower()
    results = []
    for aspect, keywords in FALLBACK_ASPECT_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            pos_hits = sum(1 for w in POSITIVE_WORDS if w in text_lower)
            neg_hits = sum(1 for w in NEGATIVE_WORDS if w in text_lower)
            sentiment = "positive" if pos_hits > neg_hits else ("negative" if neg_hits > pos_hits else "neutral")
            results.append({"aspect": aspect, "sentiment": sentiment})
    return results


def extract_aspects(review_text: str):
    """Extract (aspect, sentiment) pairs from a single review."""
    if llm_available():
        prompt = ASPECT_EXTRACTION_PROMPT.format(review_text=review_text)
        raw = call_llm(prompt)
        try:
            return extract_json(raw)
        except (ValueError, KeyError, IndexError):
            # If LLM response isn't clean JSON, fall back gracefully
            return fallback_extract(review_text)
    else:
        return fallback_extract(review_text)


def analyze_product_reviews(product_id: int):
    """Run aspect extraction across all reviews for a product and aggregate results."""
    df = pd.read_csv(DATA_PATH)
    product_reviews = df[df["product_id"] == product_id]["review_text"].tolist()

    if not product_reviews:
        return {"product_id": product_id, "review_count": 0, "aspects": {}}

    aspect_sentiments = defaultdict(lambda: {"positive": 0, "negative": 0, "neutral": 0})

    for review in product_reviews:
        pairs = extract_aspects(review)
        for pair in pairs:
            aspect = pair.get("aspect", "").lower().strip()
            sentiment = pair.get("sentiment", "neutral").lower().strip()
            if aspect and sentiment in ("positive", "negative", "neutral"):
                aspect_sentiments[aspect][sentiment] += 1

    # Build a clean summary with percentages
    summary = {}
    for aspect, counts in aspect_sentiments.items():
        total = sum(counts.values())
        summary[aspect] = {
            "positive_pct": round(100 * counts["positive"] / total, 1) if total else 0,
            "negative_pct": round(100 * counts["negative"] / total, 1) if total else 0,
            "neutral_pct": round(100 * counts["neutral"] / total, 1) if total else 0,
            "mentions": total,
        }

    return {
        "product_id": product_id,
        "review_count": len(product_reviews),
        "aspects": summary,
        "mode": "llm" if llm_available() else "fallback (rule-based, set GROQ_API_KEY for better results)",
    }
