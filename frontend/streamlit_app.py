"""
Retail Intelligence Platform — Streamlit Frontend

Run with: streamlit run streamlit_app.py
Make sure the backend (uvicorn) is running on http://localhost:8000 first.
"""

import streamlit as st
import requests
import os

API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000")

st.set_page_config(page_title="Retail Intelligence Platform", page_icon="🛍️", layout="wide")
st.title("🛍️ Retail Intelligence Platform")
st.caption("Semantic Search · Review Intelligence · AI Shopping Copilot · Real-Time Ingestion")

tab_search, tab_reviews, tab_chat, tab_ingest = st.tabs(
    ["🔍 Search", "⭐ Review Intelligence", "🤖 AI Copilot", "📡 Live Data Ingestion"]
)

# ---------------- SEARCH TAB ----------------
with tab_search:
    st.subheader("Semantic Product Search")
    query = st.text_input("Search for anything (natural language, not just keywords)",
                           placeholder="e.g. something to keep my drink cold")
    top_k = st.slider("Number of results", 1, 10, 5)

    if st.button("Search", type="primary"):
        if query:
            with st.spinner("Searching..."):
                res = requests.get(f"{API_URL}/search", params={"q": query, "top_k": top_k})
            if res.ok:
                results = res.json()["results"]
                for p in results:
                    with st.container(border=True):
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            st.markdown(f"**{p['title']}**  \n{p['description']}")
                            st.caption(f"Brand: {p.get('brand', 'N/A')} · Category: {p.get('category', 'N/A')} · "
                                       f"Source: {p.get('source', 'csv')}")
                        with col2:
                            st.metric("Match Score", f"{p['score']:.2f}")
                            st.write(f"₹{p.get('price', 0):.0f}")
            else:
                st.error(res.json().get("detail", "Search failed"))
        else:
            st.warning("Enter a search query first.")

# ---------------- REVIEWS TAB ----------------
with tab_reviews:
    st.subheader("Review Intelligence — Aspect-Based Sentiment")
    product_id = st.number_input("Product ID", min_value=1, value=1, step=1)

    if st.button("Analyze Reviews", type="primary"):
        with st.spinner("Extracting aspects from reviews..."):
            res = requests.get(f"{API_URL}/reviews/analyze/{product_id}")
        if res.ok:
            data = res.json()
            st.caption(f"{data['review_count']} reviews analyzed · mode: {data['mode']}")
            aspects = data.get("aspects", {})
            if aspects:
                for aspect, stats in aspects.items():
                    st.write(f"**{aspect.title()}**")
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Positive", f"{stats['positive_pct']}%")
                    col2.metric("Negative", f"{stats['negative_pct']}%")
                    col3.metric("Mentions", stats["mentions"])
                    st.progress(stats["positive_pct"] / 100)
            else:
                st.info("No aspects extracted for this product.")
        else:
            st.error(res.json().get("detail", "No reviews found for this product ID."))

# ---------------- CHAT TAB ----------------
with tab_chat:
    st.subheader("AI Shopping Copilot")
    st.caption("Ask a question — answers are grounded in real product + review data.")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for role, msg in st.session_state.chat_history:
        with st.chat_message(role):
            st.write(msg)

    question = st.chat_input("Ask about any product...")
    if question:
        st.session_state.chat_history.append(("user", question))
        with st.chat_message("user"):
            st.write(question)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                res = requests.post(f"{API_URL}/chat", json={"question": question, "top_k": 3})
            if res.ok:
                data = res.json()
                st.write(data["answer"])
                st.caption("Matched products: " + ", ".join(data.get("matched_products", [])))
                st.session_state.chat_history.append(("assistant", data["answer"]))
            else:
                error_msg = "Sorry, something went wrong."
                st.error(error_msg)
                st.session_state.chat_history.append(("assistant", error_msg))

# ---------------- INGESTION TAB ----------------
with tab_ingest:
    st.subheader("Real-Time Product Ingestion (eBay API)")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**One-time setup**")
        if st.button("Migrate demo CSV data into database"):
            with st.spinner("Migrating..."):
                res = requests.post(f"{API_URL}/ingest/migrate-csv")
            st.json(res.json())

    with col2:
        st.markdown("**Pull live data**")
        ingest_query = st.text_input("Search term for eBay", placeholder="e.g. wireless earbuds")
        ingest_limit = st.slider("How many to fetch", 1, 50, 10)
        if st.button("Fetch live products from eBay", type="primary"):
            with st.spinner("Fetching live data from eBay..."):
                res = requests.post(f"{API_URL}/ingest/ebay",
                                     params={"query": ingest_query, "limit": ingest_limit})
            if res.ok:
                st.success(f"Ingested {res.json()['products_saved']} products from eBay")
            else:
                st.error(res.json().get("detail", "Ingestion failed"))

    st.divider()
    if st.button("🔄 Rebuild search index (run after any data change)"):
        with st.spinner("Rebuilding embeddings and vector index..."):
            res = requests.post(f"{API_URL}/search/build-index")
        st.json(res.json())

    status_res = requests.get(f"{API_URL}/ingest/status")
    if status_res.ok:
        s = status_res.json()
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Products", s["total_products"])
        c2.metric("From CSV (demo)", s["from_csv"])
        c3.metric("From eBay (live)", s["from_ebay"])
