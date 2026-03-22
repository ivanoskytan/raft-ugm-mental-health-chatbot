import logging
import os
import json
import faiss
import numpy as np
from tqdm import tqdm
from chatbot_engine.llm_client import GPTClient
from config.config import Settings

settings = Settings.load()
class FAISSIndexer:
    def __init__(self):
        self.chunked_files_dir = "./chunked_files"
        self.vectorstore_dir = "../vectorstore"
        self.gpt_client = GPTClient(api_key=settings.OPENAI_API_KEY, model="text-embedding-3-small")

        os.makedirs(self.vectorstore_dir, exist_ok=True)

    def build_index(self):
        json_files = [
            f for f in os.listdir(self.chunked_files_dir)
            if f.endswith(".json")
        ]

        for filename in tqdm(json_files, desc="Building FAISS indices"):
            aspect = filename.replace(".json", "")
            json_path = os.path.join(self.chunked_files_dir, filename)

            with open(json_path, "r", encoding="utf-8") as f:
                chunks = json.load(f)

            texts = self._extract_texts(chunks)

            logging.info(f"[{aspect}] Embedding {len(texts)} chunks...")

            embeddings = self._embed_chunks(texts)

            dim = embeddings.shape[1]
            index = faiss.IndexFlatL2(dim)
            index.add(embeddings)

            out_path = os.path.join(self.vectorstore_dir, f"{aspect}.faiss")
            faiss.write_index(index, out_path)

            logging.info(f"[{aspect}] Saved FAISS index → {out_path}")

    def _extract_texts(self, chunks):
        if isinstance(chunks[0], str):
            return chunks
        return [chunk["text"] for chunk in chunks if "text" in chunk]

    def _embed_chunks(self, texts):
        vectors = [
            self.gpt_client.get_embedding(text)
            for text in texts
        ]

        return np.array(vectors, dtype="float32")