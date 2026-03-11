from dotenv import load_dotenv
import os

load_dotenv()  # this will look for .env in current directory

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in environment.")

import json
import random
import time
from google import genai
from google.genai import types

class ReplyGenerator:
    def __init__(self):
        with open("config.json", "r") as f:
            self.config = json.load(f)

        self.client = genai.Client(api_key=api_key)
        self.safety_settings = [
            types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
            types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
            types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
            types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
        ]

    def get_contact_config(self, sender_name):
        if sender_name in self.config["contacts"]:
            return self.config["contacts"][sender_name]
        return self.config["contacts"]["default"]

    def calculate_delay(self, reply_text):
        base_delay = len(reply_text) * 80
        noise = random.randint(-1000, 3000)
        final_delay = max(2000, base_delay + noise)
        return final_delay

    def should_ignore(self, contact_config):
        prob = contact_config.get("reply_probability", 1.0)
        return random.random() > prob

    def generate(self, message, examples_list, sender_name, conversation_history=None, override_tone=None):
        if conversation_history is None:
            conversation_history = []
            
        contact_config = self.get_contact_config(sender_name)
        
        examples_str = ""
        for ex in examples_list:
            examples_str += f"Friend: {ex['input']}\nMe: {ex['reply']}\n\n"

        recent_context = "\n".join(conversation_history[-6:])
        
        prompt = f"""
# IDENTITY
You are {self.config['persona']['name']}, a {self.config['persona']['age']}-year-old {self.config['persona']['background']}.
You are chatting with {sender_name}, who is your {contact_config['relationship']}.

# TONE FOR THIS CONTACT
{override_tone if override_tone else contact_config['tone']}

# STRICT FORMATTING RULES
- ALL LOWERCASE
- NO PERIODS OR PUNCTUATION AT END OF LINE
- ONE LINE ONLY
- EMOJIS SPARINGLY (🍌, 😈, 🙃, 😴, 🥹)
- NEVER SAY YOU ARE AN AI
- NEVER BE FORMAL

# RECENT CONVERSATION
{recent_context}

# EXAMPLES FROM YOUR ACTUAL PAST CHATS
{examples_str}

# CURRENT MESSAGE
{sender_name}: {message}

Output ONLY the exact text message, nothing else.
"""

        fallback_replies = ["ruk", "ha thike", "kya", "bol", "hmm"]

        for limit in range(3):
            try:
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        safety_settings=self.safety_settings
                    )
                )
                if response.text:
                    return response.text.strip()
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "Quota" in error_str:
                    print(f"Rate limit hit. Retrying... ({limit+1}/3)")
                    time.sleep(2)
                else:
                    print(f"Generator Error: {e}")
                    return random.choice(fallback_replies)
                    
        return random.choice(fallback_replies)
