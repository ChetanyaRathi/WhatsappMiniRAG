import json
import os
import time
import sys
import chromadb
from chromadb.utils import embedding_functions
from google import genai
from google.genai import types
import re
from dotenv import load_dotenv

load_dotenv()

CHROMA_DATA_DIR = "../chroma_data"
DATASETS_DIR = "./datasets"
COLLECTION_NAME = "whatsapp_mimic"
MERGED_FILE = os.path.join(DATASETS_DIR, "merged.json")

def setup_vector_db():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set.")
        print("Set it in the .env file or export it manually.")
        sys.exit(1)

    if not os.path.exists(MERGED_FILE):
        print(f"Error: {MERGED_FILE} not found. Please run parser.py first.")
        sys.exit(1)

    print("Loading merged dataset...")
    with open(MERGED_FILE, 'r', encoding='utf-8') as f:
        dataset = json.load(f)

    if not dataset:
        print("Dataset is empty. Exiting.")
        sys.exit(1)
    
    print("Initializing ChromaDB...")
    client = chromadb.PersistentClient(path=CHROMA_DATA_DIR)
    
    client_genai = genai.Client(api_key=api_key)
    
    class GeminiEmbeddingFunction(embedding_functions.EmbeddingFunction):
        def __init__(self):
            pass
        def __call__(self, input: chromadb.Documents) -> chromadb.Embeddings:
            result = client_genai.models.embed_content(
                model="gemini-embedding-001",
                contents=list(input)
            )
            return [e.values for e in result.embeddings]

    emb_fn = GeminiEmbeddingFunction()
    
    try:
        client.delete_collection(name=COLLECTION_NAME)
        print("Deleted existing collection to start fresh.")
    except Exception:
        pass

    collection = client.create_collection(name=COLLECTION_NAME, embedding_function=emb_fn)

    print(f"Populating vector database with {len(dataset)} items...")
    
    documents = []
    metadatas = []
    ids = []

    for idx, item in enumerate(dataset):
        documents.append(item["input"])
        metadatas.append({
            "reply": item["reply"],
            "contact": item.get("contact", "unknown")
        })
        ids.append(f"doc_{idx}")

    batch_size = 100
    total_batches = (len(documents) - 1) // batch_size + 1
    
    def add_with_retry(collection, documents, metadatas, ids):
        max_retries = 5
        for attempt in range(max_retries):
            try:
                collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                return
            except Exception as e:
                err = str(e)
                if "429" in err or "quota" in err.lower() or "RESOURCE_EXHAUSTED" in err:
                    wait = 60
                    match = re.search(r'retry in (\d+)', err)
                    if match:
                        wait = int(match.group(1)) + 5
                    print(f"Rate limit hit. Waiting {wait}s before retry {attempt+1}/{max_retries}...")
                    time.sleep(wait)
                else:
                    raise e
        raise Exception("Max retries exceeded")

    for i in range(0, len(documents), batch_size):
        add_with_retry(
            collection,
            documents[i:i+batch_size],
            metadatas[i:i+batch_size],
            ids[i:i+batch_size]
        )
        print(f"Inserted batch {i // batch_size + 1}/{total_batches}")
        time.sleep(2)

    print(f"Vector database populated successfully with {len(documents)} total records.")

if __name__ == "__main__":
    setup_vector_db()
