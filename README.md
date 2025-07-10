![Screenshot 2025-07-10 050651](https://github.com/user-attachments/assets/38887133-71d8-4f8f-9658-9054815eecaf)
# 🧾 Project Raseed – AI Receipt Manager + Google Wallet Pass Generator

> **PromptForge / Agentic-AI Hackathon 2025-07-10**  
> Tech stack: FastAPI · Gemini 2.5 (Vision + Pro) · Vanilla JS · Material Web Components · Google Wallet API

---

## ✨ What the demo does

1. **Drag-and-drop any retail receipt** (photo/scan).  
2. Back-end uses **Gemini 2.5-Flash Vision** to extract clean **line-items & prices**.  
3. Front-end displays an **editable table** and stores the receipt JSON in your browser’s `localStorage` (`praseed_history`).  
4. You can:
   - Expand, delete or correct any item or entire receipt.
   - Ask the chat box natural-language questions (e.g.  
     “How much did I spend on groceries this week?”).  
     All history is bundled into one prompt sent to **Gemini 2.5-Pro**.
5. Click **“Add to Wallet”** → a **Google Wallet pass** is created programmatically containing your insight.

> **No server-side database** — this PoC is entirely self-contained.

---

## 1 · Prerequisites

| Tool / API                        | Notes                                                 |
|-----------------------------------|-------------------------------------------------------|
| **Python 3.11+**                  | `venv` recommended                                     |
| **Docker** *(optional)*           | For one-command containerized run                     |
| **Google Cloud project**          | Enable: Vision API, Generative Language API, Wallet API |
| **Service-account JSON**          | Wallet-Issuer permissions; path set via `.env`         |
| **Generative Language API key**   | Plain API key (Gemini)                                 |

---
tree -I node_modules -L 2 > structure.txt

## 2 · Folder structure
```
project-raseed/
├─ backend/
│ ├─ main.py ← FastAPI entry-point
│ ├─ receipt_processor.py ← Gemini-Vision OCR + parser
│ ├─ ai_agent.py ← Gemini-Pro chat helper
│ └─ wallet_client.py ← Google Wallet pass creator
├─ frontend/
│ ├─ index.html
│ ├─ styles.css
│ └─ app.js
├─ .env ← DO NOT COMMIT REAL KEYS
├─ backend/requirements.txt
├─ Dockerfile
└─ README.md ← you’re here
```

---

## 3 · Environment variables

| Variable                           | Purpose                                         | Example                                  |
|------------------------------------|-------------------------------------------------|------------------------------------------|
| `GEMINI_API_KEY`                   | Generative Language API key (Gemini)            | `AIza…`                                  |
| `GOOGLE_APPLICATION_CREDENTIALS`   | Path to service-account JSON for Wallet API     | `/home/me/wallet-sa.json`                |
| *(optional)* `PORT`                | FastAPI port override                           | `8080`                                   |

Create a local `.env` file at repo root:

```bash
cp .env.example .env
# then edit:
GEMINI_API_KEY="YOUR_GEMINI_KEY"
GOOGLE_APPLICATION_CREDENTIALS="/full/path/to/sa.json"


# 0) Clone repo
git clone https://github.com/<your-org>/project-raseed.git
cd project-raseed

# 1) Create & activate venv
python3 -m venv venv && source venv/bin/activate

# 2) Install back-end deps
pip install -r backend/requirements.txt

# 3) Export env vars (or rely on .env)
export $(grep -v '^#' .env | xargs)

# 4) Launch server
uvicorn backend.main:app --reload --port ${PORT:-8080}

8 · What you should see
Upload a sample receipt → line-items appear in a table

Edit or delete any entry → totals update

Ask “What’s my total spend?” → insight text appears

Add to Wallet → Google Wallet opens with your pass![Screenshot 2025-07-10 050651](https://github.com/user-attachments/assets/5387f402-68f0-458d-b715-02be6d071aba)

# Project-Raseed-Basic-Prototype-

