import os
import re
import json

MY_NAME = "Chetanya Rathi"
CHATS_DIR = "../chats"
OUTPUT_DIR = "./datasets"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def parse_all_chats():
    # Matches standard WhatsApp export formats (both iOS and Android)
    pattern = re.compile(
        r'^\[?(\d{1,2}[\/\.\-]\d{1,2}[\/\.\-]\d{2,4}),?\s+(\d{1,2}:\d{2}(?::\d{2})?(?:\s?[APap][Mm])?)\]?\s*[-–]?\s*([^:]+):\s+(.*)$'
    )

    skip_keywords = [
        "<Media omitted>", "image omitted", "video omitted", "sticker omitted",
        "document omitted", "Contact card omitted", "Voice call", "Video call",
        "Missed voice call", "Missed video call", "Missed group call",
        "end-to-end encrypted", "Messages and calls are end-to-end",
        "audio omitted", "GIF omitted"
    ]

    merged_pairs = []

    if not os.path.exists(CHATS_DIR):
        print(f"Error: {CHATS_DIR} not found. Please place .txt exports there.")
        return

    chat_files = [f for f in os.listdir(CHATS_DIR) if f.endswith('.txt')]
    
    if not chat_files:
        print(f"No .txt files found in {CHATS_DIR}. Exiting.")
        return

    print(f"Found {len(chat_files)} chat files to process.")

    for filename in chat_files:
        contact_name = os.path.splitext(filename)[0]
        filepath = os.path.join(CHATS_DIR, filename)
        
        messages = []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                    
                match = pattern.match(line)
                if match:
                    sender = match.group(3).strip()
                    message = match.group(4).strip()
                else:
                    if messages:
                        messages[-1]['text'] += f"\n{line}"
                    continue
                    
                if any(kw in message for kw in skip_keywords):
                    continue
                    
                messages.append({'sender': sender, 'text': message})

        if not messages:
            continue

        is_group_chat = len(set(msg['sender'] for msg in messages)) > 2

        # Group continuous messages by the same sender
        grouped_messages = []
        for msg in messages:
            sender = msg['sender']
            text = msg['text']
            if not grouped_messages:
                grouped_messages.append({'sender': sender, 'text': text})
            else:
                if grouped_messages[-1]['sender'] == sender:
                    grouped_messages[-1]['text'] += f"\n{text}"
                else:
                    grouped_messages.append({'sender': sender, 'text': text})

        contact_pairs = []
        for i in range(len(grouped_messages) - 1):
            msg1 = grouped_messages[i]
            msg2 = grouped_messages[i+1]
            
            if msg1['sender'] != MY_NAME and msg2['sender'] == MY_NAME:
                contact_pairs.append({
                    "input": msg1['text'],
                    "reply": msg2['text'],
                    "contact": contact_name,
                    "chat_type": "group" if is_group_chat else "individual"
                })
        
        merged_pairs.extend(contact_pairs)
        
        if contact_pairs:
            output_file = os.path.join(OUTPUT_DIR, f"{contact_name}.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(contact_pairs, f, indent=4, ensure_ascii=False)
            print(f"Extracted {len(contact_pairs)} QA pairs for contact '{contact_name}'.")

    if merged_pairs:
        merged_file = os.path.join(OUTPUT_DIR, "merged.json")
        with open(merged_file, 'w', encoding='utf-8') as f:
            json.dump(merged_pairs, f, indent=4, ensure_ascii=False)
        print(f"\nSuccessfully created merged dataset containing {len(merged_pairs)} total pairs.")
    else:
        print("\nNo QA pairs could be extracted. Check chat export formats and MY_NAME setting.")

if __name__ == "__main__":
    parse_all_chats()
