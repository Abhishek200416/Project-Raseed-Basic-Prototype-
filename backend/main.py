import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

# load from project root
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

from backend.receipt_processor import extract_items
from backend.ai_agent         import get_insight
from backend.wallet_client    import create_wallet_pass

app = FastAPI(title="Project Raseed API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

@app.exception_handler(Exception)
async def json_exception_handler(request, exc):
    return JSONResponse(status_code=500, content={"detail": str(exc)})

@app.post("/upload-receipt")
async def upload_receipt(file: UploadFile = File(...)):
    img_bytes = await file.read()
    try:
        items = extract_items(img_bytes)
    except HTTPException as he:
        raise he
    return {"items": items}

@app.post("/insight")
async def insight(payload: dict = Body(...)):
    items    = payload.get("items", [])
    question = payload.get("question", "")

    # bullet-list all historical items
    items_text = "\n".join(f"• {it['name']}: ₹{it['price']}" for it in items) \
                 or "• (no items uploaded)"

    prompt = f"""
You are a concise personal finance assistant.
Below is the list of ALL items from the user's uploaded receipts:
{items_text}

Please:
1) Calculate the **grand total** across all receipts.
2) Provide up to two brief insights or suggestions.
3) Answer the question: {question}
""".strip()

    answer = get_insight(prompt)
    return {"insight": answer}


@app.get("/query")
async def query_insight(q: str):
    insight = get_insight(q)
    pass_id = create_wallet_pass(title="Your Insight", details=insight)
    return {
        "insight": insight,
        "passUrl": f"https://wallet.google.com/pass/{pass_id}"
    }

# serve SPA
frontend_dir = Path(__file__).parent.parent / "frontend"
app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
