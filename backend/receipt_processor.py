# backend/receipt_processor.py

import os
import re
import base64
import mimetypes
import requests
from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv()
API_KEY      = os.getenv("GEMINI_API_KEY")
BASE_URL     = "https://generativelanguage.googleapis.com/v1/"
VISION_MODEL = "models/gemini-2.5-flash"

#────────── What to drop entirely ──────────
FORBIDDEN = {
    "subtotal", "net", "vat", "gross", "item count",
    "items:", "qty:", "hsn", "value", "breakup", "amount inr",
    "cgst", "sgst", "igst", "cess",
    "thank you", "served by", "cashier", "bill",
    "saved rs",          # new
    "credit card",       # already handled
    "card payment",      # already handled
}

#────────── Regex patterns ──────────
QTY_PRICE_RX = re.compile(r"(.+?)\s+(\d+)\s+(\d+\.\d{2})(?:\D.*)?$")
PRICE_RX     = re.compile(r"(.+?)\s+(\d+\.\d{2})(?:\D.*)?$")
LEAD_RX      = re.compile(r"^[\s\*\u2022>\-\d\)\(]+")  # strip bullets/indices

#────────── OCR via Gemini-2.5-Flash ──────────
def _ocr(image_bytes: bytes) -> str:
    mime = mimetypes.guess_type("receipt.jpg")[0] or "image/jpeg"
    payload = {
        "contents": [{
            "parts": [
                {"inline_data": {
                    "mime_type": mime,
                    "data": base64.b64encode(image_bytes).decode()
                }},
                {"text": "Extract every visible line of text from this retail receipt."}
            ]
        }]
    }
    resp = requests.post(
        f"{BASE_URL}{VISION_MODEL}:generateContent",
        headers={
            "Content-Type": "application/json",
            "X-goog-api-key": API_KEY
        },
        json=payload,
        timeout=60
    )
    if resp.status_code != 200:
        snippet = resp.text.replace("\n", " ")[:200]
        raise HTTPException(502, f"Gemini OCR failed ({resp.status_code}): {snippet}")

    cands = resp.json().get("candidates", [])
    if not cands:
        raise HTTPException(502, "Gemini OCR returned no candidates")

    first = cands[0]
    # v1 schema
    if isinstance(first.get("output"), str):
        return first["output"]

    # fallback
    parts = first.get("content", {}).get("parts", [])
    return "\n".join(p["text"] for p in parts if isinstance(p, dict) and "text" in p)

#────────── Main extractor ──────────
def extract_items(image_bytes: bytes) -> list[dict]:
    """
    Returns a list of {"name": ..., "price": "..."} for each line-item.
    If it finds *no* real items, it will fall back to the 'Amt:' or 'Card Payment:' total.
    """
    raw      = _ocr(image_bytes)
    seen     = set()
    items    = []
    fallback = None

    for line in raw.splitlines():
        txt = LEAD_RX.sub("", line).strip()
        if not txt:
            continue
        low = txt.lower()

        # 1) catch the grand‐total and stash for fallback
        if low.startswith("amt:") or low.startswith("t:") or "card payment" in low:
            m = re.search(r"(\d+\.\d{2})\b", txt)
            if m:
                fallback = m.group(1)
            continue

        # 2) filter out any forbidden keywords
        if any(tok in low for tok in FORBIDDEN):
            continue

        # 3) drop pure‐number lines (e.g. "9924.89", "2792.29")
        if re.fullmatch(r"[\d\.\s,×]+", txt):
            continue

        # 4) parse "name qty unitPrice"
        m = QTY_PRICE_RX.match(txt)
        if m:
            name, qty_s, unit_s = m.groups()
            price = int(qty_s) * float(unit_s)
        else:
            # 5) parse single "name unitPrice"
            m2 = PRICE_RX.match(txt)
            if not m2:
                continue
            name, unit_s = m2.groups()
            price = float(unit_s)

        name = name.strip()
        # must be at least 3 chars and contain a letter
        if len(name) < 3 or not re.search(r"[A-Za-z]", name):
            continue

        key = (name.lower(), f"{price:.2f}")
        if key in seen:
            continue
        seen.add(key)
        items.append({"name": name, "price": f"{price:.2f}"})

    # 6) if absolutely no items found, return the grand-total as one entry
    if not items and fallback:
        return [{"name": "Total (from receipt)", "price": fallback}]

    return items
