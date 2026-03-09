# Autonomous WhatsApp AI Agent

This project initializes a fully autonomous WhatsApp client powered by Gemini and ChromaDB that replies to your contacts natively utilizing your historic texting style.

## 🚀 Setup & Launch

1. **Export Chat Histories**: Export your WhatsApp chats (Settings > Chat > Export Chat > Without Media) and place all `.txt` files in the `chats/` directory.
2. **Environment Variables**: Make sure your `.env` contains your `GEMINI_API_KEY`.
3. **Install Core Backend Requirements**:
```bash
cd agent
pip install fastapi uvicorn chromadb google-generativeai pydantic python-dotenv
```
4. **Compile Databases**:
- Run `python parser.py` to parse all the chat logs into `.json` inputs inside `/datasets/`.
- Run `python vector_db.py` to encode the entire library into ChromaDB.
5. **Start RAG Server**:
- Run `python main.py` to launch the FastAPI backend endpoint.
6. **Start Node.js WhatsApp Bridge**:
- In a separate terminal window:
```bash
cd ../bridge
npm install
node index.js
```
- A QR code will generate in the terminal. Scan it natively with your WhatsApp Mobile Application to log the agent in!
7. **Configure Connections**: Edit `config.json` inside the `agent/` folder to set your Persona stats and custom rule sets for contacts (Probability/Tone matrices).
8. **Kill Switch**: If something goes wrong, text your number the override value located in the config (`CHETANYA_OVERRIDE`).
9. **Status Triggers**: Check if your agent paused globally or on a specific contact by testing the state of the API via `GET http://localhost:8000/status`.
10. **Resume Bridge**: Call `POST http://localhost:8000/unpause` to release locks.
