import os
import chromadb
from chromadb.utils import embedding_functions
from google import genai as genai_new
import json

class RAGRetriever:
    def __init__(self):
        self.chroma_data_dir = "../chroma_data"
        self.collection_name = "whatsapp_mimic"
        
        with open("config.json", "r") as f:
            self.config = json.load(f)

        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment.")

        # Custom embedding class matching vector_db.py
        class GeminiEmbeddingFunction(embedding_functions.EmbeddingFunction):
            def __init__(self, api_key):
                self.client = genai_new.Client(api_key=api_key)
            def __call__(self, input: chromadb.Documents) -> chromadb.Embeddings:
                result = self.client.models.embed_content(
                    model="gemini-embedding-001",
                    contents=list(input)
                )
                return [e.values for e in result.embeddings]
        
        self.emb_fn = GeminiEmbeddingFunction(api_key=api_key)
        self.client = chromadb.PersistentClient(path=self.chroma_data_dir)
        self.collection = self.client.get_collection(name=self.collection_name, embedding_function=self.emb_fn)

    def query(self, message: str, contact_name: str, n_results=5):
        try:
            # 1. Query specifically for this contact
            contact_results = self.collection.query(
                query_texts=[message],
                n_results=3,
                where={"contact": contact_name}
            )

            # 2. Query globally for generic fallback
            global_results = self.collection.query(
                query_texts=[message],
                n_results=2
            )

            # 3. Merge and deduplicate
            merged_docs = []
            seen_inputs = set()

            def process_results(results):
                if results['documents'] and results['documents'][0]:
                    docs = results['documents'][0]
                    metadatas = results['metadatas'][0]
                    distances = results['distances'][0]

                    for i in range(len(docs)):
                        doc_text = docs[i]
                        if doc_text not in seen_inputs:
                            seen_inputs.add(doc_text)
                            merged_docs.append({
                                "input": doc_text,
                                "reply": metadatas[i]["reply"],
                                "distance": distances[i]
                            })

            process_results(contact_results)
            process_results(global_results)

            if not merged_docs:
                return []

            # Determine confidence (ChromaDB uses L2 distance by default, lower is better. Assuming threshold is inverse)
            # A rough estimate for L2 distance matching: lower distance = higher confidence. 
            # If distance is too high (e.g. > configured threshold inverted or handled differently), we flag it.
            # Using a simplified check just passing all valid docs to prompt since Gemini handles context best.

            return merged_docs[:n_results]

        except Exception as e:
            print(f"RAG Error: {e}")
            return []
