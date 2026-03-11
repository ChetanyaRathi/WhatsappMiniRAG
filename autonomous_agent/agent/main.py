from dotenv import load_dotenv
import os

load_dotenv()  # this will look for .env in current directory

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in environment.")

from fastapi import FastAPI, BackgroundTasks
import uvicorn
import json
import random
from pydantic import BaseModel
from rag import RAGRetriever
from generator import ReplyGenerator

app = FastAPI()

with open("config.json", "r") as f:
    config = json.load(f)

rag = RAGRetriever()
generator = ReplyGenerator()

conversation_histories = {}
daily_reply_count = 0
agent_paused = False
paused_contacts = set()

class IncomingMessage(BaseModel):
    sender_name: str
    sender_number: str
    message: str
    is_group: bool = False
    group_name: str = ""

@app.on_event("startup")
async def startup_event():
    print(f"WhatsApp RAG Agent Backend Started. Loaded {len(config['contacts'])} contacts.")

@app.post("/reply")
async def reply(msg: IncomingMessage):
    global agent_paused, daily_reply_count, paused_contacts

    ALLOWED_CONTACTS = list(config["contacts"].keys())
    ALLOWED_CONTACTS = [c for c in ALLOWED_CONTACTS if c != "default"]

    if not msg.is_group and msg.sender_name not in ALLOWED_CONTACTS:
        print(f"Blocked message from unknown contact: {msg.sender_name}")
        return {"reply": None, "delay_ms": 0}

    if agent_paused:
        return {"reply": None, "delay_ms": 0}
        
    if daily_reply_count >= config["safety"]["max_daily_replies"]:
        print(f"Daily reply limit reached ({daily_reply_count}).")
        return {"reply": None, "delay_ms": 0}

    # Killswitch
    if config["safety"]["killswitch_keyword"] in msg.message.upper():
        agent_paused = True
        print(f"!!! KILLSWITCH ACTIVATED BY {msg.sender_name} !!! Agent paused.")
        return {"reply": None, "delay_ms": 0}

    # OTP/Sensitive Trigger
    msg_lower = msg.message.lower()
    if any(keyword in msg_lower for keyword in config["safety"]["otp_keywords"]):
        paused_contacts.add(msg.sender_number)
        print(f"Sensitive message detected from {msg.sender_name}. Pausing auto-reply for this contact.")
        return {"reply": None, "delay_ms": 0}

    if msg.sender_number in paused_contacts:
        return {"reply": None, "delay_ms": 0}

    # Group Mentions Check
    if msg.is_group and config["behavior"].get("group_reply_only_if_mentioned", True):
        # Extremely basic mention logic - checks if persona name is in string
        if config["persona"]["name"].split()[0].lower() not in msg_lower:
            return {"reply": None, "delay_ms": 0}

    if msg.is_group:
        allowed_groups = config["safety"].get("allowed_groups", [])
        if msg.group_name not in allowed_groups:
            print(f"Blocked message from unknown group: {msg.group_name}")
            return {"reply": None, "delay_ms": 0}
        
        group_config = None
        group_key = None
        for key, val in config["groups"].items():
            if val["display_name"] == msg.group_name:
                group_config = val
                group_key = key
                break
        
        if not group_config:
            return {"reply": None, "delay_ms": 0}
        
        if random.random() > group_config["reply_probability"]:
            print(f"Ignored group message from {msg.group_name} (probability roll)")
            return {"reply": None, "delay_ms": 0}
        
        number = msg.sender_number
        if number not in conversation_histories:
            conversation_histories[number] = []
        conversation_histories[number].append(f"{msg.sender_name}: {msg.message}")
        
        rag_examples = rag.query(
            message=msg.message,
            contact_name=group_key
        )
        
        print(f"Generating group reply for {msg.group_name} based on {len(rag_examples)} DB context matches...")
        reply_text = generator.generate(
            msg.message,
            rag_examples,
            msg.sender_name,
            conversation_histories[number],
            override_tone=group_config["tone"]
        )
        
        conversation_histories[number].append(f"Me: {reply_text}")
        conversation_histories[number] = conversation_histories[number][-20:]
        daily_reply_count += 1
        delay = generator.calculate_delay(reply_text)
        print(f"Group reply -> {reply_text} (Delay: {delay}ms)")
        return {"reply": reply_text, "delay_ms": delay}

    contact_config = generator.get_contact_config(msg.sender_name)
    
    if generator.should_ignore(contact_config):
        print(f"Ignored message from {msg.sender_name} (Probability Roll).")
        return {"reply": None, "delay_ms": 0}

    # Rolling History Logic
    number = msg.sender_number
    if number not in conversation_histories:
        conversation_histories[number] = []
        
    conversation_histories[number].append(f"Friend: {msg.message}")

    # 1. RAG
    rag_examples = rag.query(message=msg.message, contact_name=msg.sender_name)

    # 2. Generation
    print(f"Generating reply for {msg.sender_name} based on {len(rag_examples)} DB context matches...")
    reply_text = generator.generate(msg.message, rag_examples, msg.sender_name, conversation_histories[number])

    # Update history and counters
    conversation_histories[number].append(f"Me: {reply_text}")
    # Cap memory list memory to last 20 inputs (10 pairs)
    conversation_histories[number] = conversation_histories[number][-20:]
    
    daily_reply_count += 1
    
    delay = generator.calculate_delay(reply_text)
    
    print(f"Reply -> {reply_text} (Delay: {delay}ms)")
    
    return {"reply": reply_text, "delay_ms": delay}

@app.get("/status")
async def status():
    return {
        "agent_paused": agent_paused,
        "daily_reply_count": daily_reply_count,
        "paused_contacts_count": len(paused_contacts),
        "paused_contacts": list(paused_contacts)
    }

@app.post("/unpause")
async def unpause():
    global agent_paused, paused_contacts
    agent_paused = False
    paused_contacts.clear()
    print("Agent Unpaused via API!")
    return {"status": "agent resumed"}

@app.post("/reset_count")
async def reset_count():
    global daily_reply_count
    daily_reply_count = 0
    return {"status": "count reset"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
