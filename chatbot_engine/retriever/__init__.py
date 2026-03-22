import faiss
import os
import numpy as np
import logging
import pickle
from chatbot_engine.llm_client import GPTClient

class Retriever:
    def __init__(self):
        base_dir = os.path.join(os.path.dirname(__file__))
        self.vectorstore_dir = os.path.join(base_dir, "../vectorstore")
        self.gpt_client = GPTClient()
        self.logger = logging.getLogger("Retriever")
        self.indices = {}
        self.texts = {}
        self._load_all()

    def _load_all(self):
        section_meta_path = os.path.join(self.vectorstore_dir, "section_data.pkl")
        if not os.path.exists(section_meta_path):
            raise FileNotFoundError("Missing `section_data.pkl`. Vector store incomplete")

        with open(section_meta_path, "rb") as f:
            section_data = pickle.load(f)

        for aspect, data in section_data.items():
            index_path = os.path.join(self.vectorstore_dir, f"{aspect}.index")
            if not os.path.exists(index_path):
                self.logger.warning(f"Missing FAISS index for aspect: {aspect}")
                continue

            self.indices[aspect] = faiss.read_index(index_path)

            if isinstance(data, dict) and "texts" in data:
                self.texts[aspect] = data["texts"]
            elif isinstance(data, list):
                self.texts[aspect] = data
            else:
                raise ValueError(f"Unsupported section_data format for aspect '{aspect}'")
    
    def _embed(self, text: str):
        return np.array(
            self.gpt_client.get_embedding(text),
            dtype="float32"
        )

    def run(self, query, aspect, top_k=5):
        if aspect not in self.indices:
            raise ValueError(f"[Retriever]: Aspect {aspect} index not found")

        index = self.indices[aspect]
        texts = self.texts[aspect]

        if index.ntotal == 0:
            raise RuntimeError(f"[Retriever]: FAISS index for {aspect} is empty")

        top_k = min(top_k, index.ntotal)

        query_vector = self._embed(query).reshape(1, -1)

        distances, indices = index.search(query_vector, top_k)
        max_valid_idx = min(index.ntotal, len(texts)) - 1

        results = []
        for rank, idx in enumerate(indices[0]):
            if idx > max_valid_idx:
                continue

            results.append({
                "rank": rank + 1,
                "score": float(distances[0][rank]),
                "chunk": texts[idx]
            })

        if not results:
            raise RuntimeError(
                f"[Retriever]: No retrievable chunks for aspect '{aspect}' "
                f"(ntotal={index.ntotal}, top_k={top_k})"
            )

        return results
