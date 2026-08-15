"""
AI Shopping Copilot — Module 3

Answers natural-language product questions by:
1. Retrieving relevant products (Module 1: semantic search)
2. Pulling aspect-sentiment review summaries for those products (Module 2)
3. Feeding both as context to the LLM, which generates a grounded answer
   with citations back to the data (not a hallucinated guess).
"""

from app.services.search_service import search_products
from app.services.review_service import analyze_product_reviews
from app.services.llm_client import call_llm, llm_available

COPILOT_PROMPT = """You are a helpful AI shopping assistant. Answer the customer's
question using ONLY the product and review information provided below. Be concise
(3-5 sentences). Reference specific products by name and cite what reviews say
when relevant (e.g. "based on customer reviews, battery life is a common complaint").
If the provided information doesn't answer the question, say so honestly instead
of guessing.

Customer question: "{question}"

Available product + review data:
{context}

Answer:"""


def build_context(products_with_reviews):
    """Format retrieved products + their review summaries into a text block for the LLM."""
    blocks = []
    for item in products_with_reviews:
        p = item["product"]
        reviews = item["review_summary"]

        block = f"- {p['title']} (₹{p['price']}, brand: {p['brand']})\n  {p['description']}"

        if reviews and reviews.get("aspects"):
            aspect_lines = []
            for aspect, stats in reviews["aspects"].items():
                aspect_lines.append(
                    f"{aspect}: {stats['positive_pct']}% positive, {stats['negative_pct']}% negative "
                    f"({stats['mentions']} mentions)"
                )
            block += "\n  Customer review insights: " + "; ".join(aspect_lines)
        else:
            block += "\n  Customer review insights: no reviews available"

        blocks.append(block)

    return "\n\n".join(blocks)


def ask_copilot(question: str, top_k: int = 3):
    """Main entry point: retrieve relevant products + reviews, then generate an answer."""
    # Step 1: retrieve relevant products via semantic search (Module 1)
    matched_products = search_products(question, top_k=top_k)

    # Step 2: pull review intelligence for each matched product (Module 2)
    products_with_reviews = []
    for p in matched_products:
        review_summary = analyze_product_reviews(p["id"])
        products_with_reviews.append({"product": p, "review_summary": review_summary})

    # Step 3: build context and ask the LLM
    context = build_context(products_with_reviews)

    if not llm_available():
        return {
            "question": question,
            "answer": (
                "AI Copilot needs GROQ_API_KEY set to generate answers. "
                "Here's the raw matched data instead:\n\n" + context
            ),
            "matched_products": [p["product"]["title"] for p in products_with_reviews],
            "mode": "fallback (no LLM key set)",
        }

    prompt = COPILOT_PROMPT.format(question=question, context=context)
    answer = call_llm(prompt, max_tokens=400)

    return {
        "question": question,
        "answer": answer.strip(),
        "matched_products": [p["product"]["title"] for p in products_with_reviews],
        "mode": "llm",
    }
