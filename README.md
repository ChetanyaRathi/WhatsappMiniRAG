# WhatsApp Mimic RAG Agent

An autonomous WhatsApp agent that replies on your behalf using RAG (Retrieval Augmented Generation) built with ChromaDB, Gemini, FastAPI and whatsapp-web.js.

## Tech Stack
- Python
- FastAPI
- ChromaDB
- Google Gemini
- Node.js
- whatsapp-web.js

## Setup Instructions

1. Clone the repo
2. Add your WhatsApp chat exports as `.txt` files to `chats/`
3. Set `GEMINI_API_KEY` in `.env` file
4. `pip install -r requirements.txt`
5. `python autonomous_agent/agent/parser.py`
6. `python autonomous_agent/agent/vector_db.py`
7. `python autonomous_agent/agent/main.py`
8. `cd autonomous_agent/bridge && npm install && node index.js`
9. Scan QR code with WhatsApp

*Note: `chats/`, `.env`, and `chroma_data/` are gitignored for privacy.*
