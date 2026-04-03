import faiss
import os
import numpy as np
import logging
import json
from chatbot_engine.llm_client import GPTClient
from config.config import Settings


settings = Settings.load()


class Retriever:
    def __init__(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))

        self.vectorstore_dir = os.path.join(base_dir, "../vectorstore")
        self.chunked_dir = os.path.join(base_dir, "../vectorstore_builder/data/chunked_files")

        self.gpt_client = GPTClient(
            api_key=settings.OPENAI_API_KEY,
            model="text-embedding-3-small"
        )

        self.logger = logging.getLogger("Retriever")

        self.indices = {}
        self.texts = {}

        self._load_all()

    def _load_all(self):
        for file in os.listdir(self.vectorstore_dir):
            if not file.endswith(".faiss"):
                continue

            aspect = file.replace(".faiss", "")
            index_path = os.path.join(self.vectorstore_dir, file)
            json_path = os.path.join(self.chunked_dir, f"{aspect}.json")

            # 🔹 Load FAISS
            try:
                index = faiss.read_index(index_path)
                self.indices[aspect] = index
            except Exception as e:
                self.logger.error(f"[{aspect}] Failed loading FAISS: {e}")
                continue

            # 🔹 Load TEXTS from JSON
            if not os.path.exists(json_path):
                self.logger.warning(f"[{aspect}] Missing JSON chunks")
                continue

            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    chunks = json.load(f)

                if isinstance(chunks[0], str):
                    texts = chunks
                else:
                    texts = [
                        c["text"]
                        for c in chunks
                        if isinstance(c, dict) and "text" in c
                    ]

                if len(texts) != index.ntotal:
                    self.logger.warning(
                        f"[{aspect}] mismatch index={index.ntotal}, texts={len(texts)}"
                    )
                    continue

                self.texts[aspect] = texts

            except Exception as e:
                self.logger.error(f"[{aspect}] Failed loading JSON: {e}")

        print("Loaded aspects:", list(self.indices.keys()))
    
    def _embed(self, text: str):
        return np.array(
            self.gpt_client.get_embedding(text),
            dtype="float32"
        )

    def run(self, query, aspect, top_k=5):
        print("Indices: ", self.indices)
        if aspect not in self.indices:
            raise ValueError(f"[Retriever]: Aspect {aspect} index not found")

        print("Enter retriever - 1")
        index = self.indices[aspect]
        texts = self.texts[aspect]
        print("Enter retriever - 2")

        if index.ntotal == 0:
            raise RuntimeError(f"[Retriever]: FAISS index for {aspect} is empty")

        top_k = min(top_k, index.ntotal)

        print("Enter retriever - 3")
        query_vector = np.array(self._embed(query), dtype=np.float32).reshape(1, -1)

        print("Enter retriever - 3a: ", query_vector)

        print("Query dim:", query_vector.shape[1])
        print("Index dim:", index.d)

        distances, indices = index.search(query_vector, top_k)
        print("Enter retriever - 3b")
        max_valid_idx = min(index.ntotal, len(texts)) - 1
        print("Enter retriever - 4")
        results = []
        print("Index ntotal:", index.ntotal)
        print("Texts length:", len(texts))
        print("Returned indices:", indices)
        for rank, idx in enumerate(indices[0]):
            print("Enter retriever - for loop")
            results.append({
                "rank": rank + 1,
                "score": float(distances[0][rank]),
                "chunk": texts[idx]
            })

        print("Results: ", results)
        if not results:
            raise RuntimeError(
                f"[Retriever]: No retrievable chunks for aspect '{aspect}' "
                f"(ntotal={index.ntotal}, top_k={top_k})"
            )

        return results
