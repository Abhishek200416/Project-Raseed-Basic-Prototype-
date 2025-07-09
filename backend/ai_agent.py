import os
import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
GEN_URL = (
    "https://generativelanguage.googleapis.com/v1/"
    "models/gemini-2.5-pro:generateContent"
)

SYSTEM_INSTRUCTIONS = """
You are a concise personal finance assistant.
When given a list of items with prices, you MUST:
1) Calculate and report the total amount spent in one line.
2) Answer the user’s question in one or two direct sentences.
3) Offer up to two brief actionable suggestions or insights
   (e.g., “Consider setting a weekly budget,” 
    “You may want to restock item X soon.”)
"""

def _extract_text(candidate: dict) -> str | None:
    # new schema (v1)
    for p in candidate.get("content", {}).get("parts", []):
        if isinstance(p, dict) and "text" in p:
            return p["text"]
    # legacy schema
    if isinstance(candidate.get("output"), str):
        return candidate["output"]
    return None

def get_insight(user_prompt: str) -> str:
    full_prompt = SYSTEM_INSTRUCTIONS.strip() + "\n\n" + user_prompt.strip()
    payload = {"contents": [{"parts": [{"text": full_prompt}]}]}

    resp = requests.post(
        GEN_URL,
        headers={
            "Content-Type": "application/json",
            "X-goog-api-key": API_KEY
        },
        json=payload,
        timeout=30
    )
    resp.raise_for_status()

    for cand in resp.json().get("candidates", []):
        text = _extract_text(cand)
        if text:
            return text.strip()

    return "[No response — unable to extract text]"
