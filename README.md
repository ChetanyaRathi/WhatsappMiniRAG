# 🤖 WhatsApp Mimic RAG Agent

A fully autonomous WhatsApp AI agent that **replies on your behalf** by learning your texting style from your actual chat history. Built with RAG (Retrieval Augmented Generation) using ChromaDB for semantic search and Google Gemini for generation.

> It doesn't just reply — it replies like **you**.

---

## ✨ Features

- **Style Mimicking** — Learns your tone, slang, emoji usage, and vocabulary from real WhatsApp exports
- **Per-Contact Personality** — Different tones and reply probabilities per contact
- **Group Chat Support** — Whitelisted group replies with configurable probability
- **RAG Pipeline** — Retrieves your most relevant past conversations as context before generating
- **Smart Safety** — OTP/password detection, killswitch keyword, daily reply limits
- **Natural Delays** — Typing delay simulation based on message length + random noise
- **Rolling Memory** — Maintains recent conversation context (last 10 exchanges)
- **Contact Whitelist** — Only replies to contacts defined in your config

---

## 🏗️ Architecture

```
WhatsApp ←→ whatsapp-web.js (Node.js Bridge)
                    ↓ HTTP POST
              FastAPI Backend (Python)
                    ↓
        ┌───────────┴───────────┐
        │                       │
   RAG Retriever          Reply Generator
   (ChromaDB)             (Gemini 2.5 Flash)
        │                       │
   Semantic Search         Prompt + Context
   on past chats          → Natural Reply
```

---

## 📁 Project Structure

```
WhatsApp-Mimic-RAG/
├── autonomous_agent/
│   ├── agent/
│   │   ├── main.py          # FastAPI server — routes, safety checks, group logic
│   │   ├── rag.py           # RAG retriever — ChromaDB semantic search
│   │   ├── generator.py     # Gemini reply generator — prompt engineering + delays
│   │   ├── parser.py        # Chat export parser — .txt → structured JSON pairs
│   │   ├── vector_db.py     # ChromaDB populator — embeds parsed chats
│   │   ├── config.json      # Contact configs, tones, safety rules, group settings
│   │   └── .env             # API key (gitignored)
│   ├── bridge/
│   │   ├── index.js         # WhatsApp Web bridge — message listener + relay
│   │   └── package.json     # Node.js dependencies
│   └── chats/               # Your .txt chat exports (gitignored)
├── requirements.txt
├── .gitignore
└── README.md
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| WhatsApp Interface | `whatsapp-web.js` + `qrcode-terminal` |
| API Bridge | Node.js + Axios |
| Backend Server | Python + FastAPI + Uvicorn |
| Embeddings | Google Gemini (`gemini-embedding-001`) |
| Generation | Google Gemini (`gemini-2.5-flash`) |
| Vector Database | ChromaDB (persistent, local) |
| Config | JSON-based per-contact personality system |

---

## 🚀 Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- A Google Gemini API key ([get one here](https://aistudio.google.com/apikey))

### 1. Clone & Install

```bash
git clone https://github.com/ChetanyaRathi/WhatsappMiniRAG.git
cd WhatsappMiniRAG
pip install -r requirements.txt
cd autonomous_agent/bridge && npm install && cd ../..
```

### 2. Add Your Chat Exports

Export your WhatsApp chats as `.txt` files (without media) and drop them into:
```
autonomous_agent/chats/
```
Name each file after the contact (e.g., `vinayak.txt`, `parth.txt`).  
For group chats, name the file after the group key used in config (e.g., `stock.txt`).

### 3. Configure API Key

Create `autonomous_agent/agent/.env`:
```
GEMINI_API_KEY=your_api_key_here
```

### 4. Parse & Embed

```bash
cd autonomous_agent/agent
python parser.py       # Parses .txt → JSON pairs
python vector_db.py    # Embeds pairs into ChromaDB
```

### 5. Run the Agent

**Terminal 1** — Start the Python backend:
```bash
cd autonomous_agent/agent
python main.py
```

**Terminal 2** — Start the WhatsApp bridge:
```bash
cd autonomous_agent/bridge
node index.js
```

Scan the QR code with your WhatsApp and you're live! 🟢

---

## ⚙️ Configuration

Edit `autonomous_agent/agent/config.json` to customize:

```jsonc
{
  "contacts": {
    "Friend Name": {
      "relationship": "close_friend",
      "tone": "casual hinglish banter, friendly",
      "reply_probability": 0.95,    // 95% chance of replying
      "avg_delay_seconds": 5
    }
  },
  "groups": {
    "stock": {                       // matches stock.txt filename
      "display_name": "Stock Analysts",
      "tone": "talks about stocks and market, short replies",
      "reply_probability": 0.4
    }
  },
  "safety": {
    "killswitch_keyword": "CHETANYA_OVERRIDE",
    "otp_keywords": ["otp", "password", "bank", "cvv"],
    "max_daily_replies": 200,
    "allowed_groups": ["Stock Analysts"]
  }
}
```

---

## 🔒 Privacy & Safety

- **`.env`**, **`chats/`**, **`datasets/`**, and **`chroma_data/`** are all **gitignored** — your personal data never leaves your machine
- **OTP Detection** — Auto-pauses replies if sensitive keywords are detected
- **Killswitch** — Send a specific keyword to immediately stop the agent
- **Daily Limit** — Caps total replies per day to prevent runaway behavior
- **Whitelist Only** — Unknown contacts and non-whitelisted groups are silently blocked

---

## 📊 How It Works

1. **Parse** — `parser.py` reads your WhatsApp `.txt` exports and extracts input→reply pairs
2. **Embed** — `vector_db.py` embeds all pairs into ChromaDB using Gemini embeddings
3. **Listen** — `index.js` hooks into WhatsApp Web and forwards incoming messages to FastAPI
4. **Retrieve** — `rag.py` finds the most similar past conversations via semantic search
5. **Generate** — `generator.py` feeds your persona, tone, past examples, and recent context to Gemini
6. **Reply** — Response is sent back through the bridge with a natural typing delay

---

## 📝 License

This project is for personal/educational use. Use responsibly.
