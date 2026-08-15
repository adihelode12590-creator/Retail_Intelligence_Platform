"""
Lightweight LLM client wrapper.

Uses Groq's free-tier API (OpenAI-compatible endpoint) by default since it's
free and fast. You can swap PROVIDER/BASE_URL/MODEL to Gemini, OpenAI, or
Claude later without changing any calling code.

Get a free Groq API key at: https://console.groq.com/keys
Then set it as an environment variable:
    Windows (PowerShell): $env:GROQ_API_KEY="your_key_here"
    Mac/Linux:            export GROQ_API_KEY="your_key_here"

If no API key is set, this falls back to a simple rule-based extractor so you
can still test the pipeline end-to-end without any setup.
"""

import os
import json
import requests

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_BASE_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.1-8b-instant"  # fast + free tier friendly


def llm_available() -> bool:
    return bool(GROQ_API_KEY)


def call_llm(prompt: str, max_tokens: int = 500) -> str:
    """Send a prompt to the LLM and return the raw text response."""
    if not GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY not set. Get a free key at https://console.groq.com/keys "
            "and set it as an environment variable, or use fallback mode."
        )

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": max_tokens,
    }

    response = requests.post(GROQ_BASE_URL, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


def extract_json(text: str):
    """LLMs sometimes wrap JSON in markdown fences or extra text — strip that."""
    text = text.strip()
    if "```" in text:
        text = text.split("```")[1]
        text = text.replace("json", "", 1).strip()
    return json.loads(text)
