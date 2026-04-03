import logging
import os
import json
import faiss
import numpy as np
import pickle
from tqdm import tqdm
from chatbot_engine.llm_client import GPTClient
from config.config import Settings

settings = Settings.load()


class FAISSIndexer:
    def __init__(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.files_dir = os.path.join(base_dir, "data", "text_files")
        self.chunked_files_dir = os.path.join(base_dir, "data", "chunked_files")
        self.vectorstore_dir = os.path.join(base_dir, "..", "vectorstore")

        self.gpt_client = GPTClient(
            api_key=settings.OPENAI_API_KEY,
            model="text-embedding-3-small"
        )

        os.makedirs(self.vectorstore_dir, exist_ok=True)
        self.logger = logging.getLogger("FAISSIndexer")

    def build_index(self, force=False):
        json_files = [
            f for f in os.listdir(self.chunked_files_dir)
            if f.endswith(".json")
        ]

        if not json_files:
            raise RuntimeError("No chunked JSON files found")

        pbar = tqdm(json_files, desc="Building FAISS indices")

        for filename in pbar:
            aspect = filename.replace(".json", "")
            json_path = os.path.join(self.chunked_files_dir, filename)
            out_path = os.path.join(self.vectorstore_dir, f"{aspect}.faiss")

            if os.path.exists(out_path) and not force:
                pbar.set_postfix_str(f"Skipped: {aspect}")
                continue

            pbar.set_postfix_str(f"Processing: {aspect}")

            with open(json_path, "r", encoding="utf-8") as f:
                chunks = json.load(f)

            texts = self._extract_texts(chunks)

            if not texts:
                self.logger.warning(f"[{aspect}] No valid texts found, skipping...")
                continue

            embeddings = self._embed_chunks(texts)

            if embeddings.size == 0:
                self.logger.warning(f"[{aspect}] Empty embeddings, skipping...")
                continue

            dim = embeddings.shape[1]
            index = faiss.IndexFlatL2(dim)
            index.add(embeddings)

            faiss.write_index(index, out_path)

            self.logger.info(f"[{aspect}] Saved index with {index.ntotal} vectors")
            pbar.set_postfix_str(f"Saved: {aspect}")
            
    def _extract_texts(self, chunks):
        if not chunks:
            return []

        if isinstance(chunks[0], str):
            return chunks

        return [
            chunk["text"]
            for chunk in chunks
            if isinstance(chunk, dict) and "text" in chunk
        ]

    def _embed_chunks(self, texts):
        vectors = []

        for text in tqdm(texts, desc="Embedding", leave=False):
            try:
                emb = self.gpt_client.get_embedding(text)
                vectors.append(emb)
            except Exception as e:
                self.logger.warning(f"Embedding failed: {e}")

        return np.array(vectors, dtype="float32")
    
    def rebuild_section_metadata(self):
        section_data = {}

        json_files = [
            f for f in os.listdir(self.chunked_files_dir)
            if f.endswith(".json")
        ]

        if not json_files:
            raise RuntimeError("No chunked JSON files found")

        pbar = tqdm(json_files, desc="Rebuilding section metadata")

        for filename in pbar:
            aspect = filename.replace(".json", "")
            json_path = os.path.join(self.chunked_files_dir, filename)
            index_path = os.path.join(self.vectorstore_dir, f"{aspect}.faiss")

            if not os.path.exists(index_path):
                self.logger.warning(f"[{aspect}] Missing FAISS index, skipping...")
                continue

            with open(json_path, "r", encoding="utf-8") as f:
                chunks = json.load(f)

            texts = self._extract_texts(chunks)

            if not texts:
                self.logger.warning(f"[{aspect}] No texts found, skipping...")
                continue

            index = faiss.read_index(index_path)

            if index.ntotal != len(texts):
                self.logger.warning(
                    f"[{aspect}] Mismatch → index={index.ntotal}, texts={len(texts)}"
                )
                continue

            section_data[aspect] = {
                "texts": texts
            }

            pbar.set_postfix_str(f"Added: {aspect}")

        section_meta_path = os.path.join(self.vectorstore_dir, "section_data.pkl")

        with open(section_meta_path, "wb") as f:
            pickle.dump(section_data, f)

        self.logger.info(f"Rebuilt section metadata → {section_meta_path}")

        print("\nFINAL VALIDATION:")
        for aspect, data in section_data.items():
            print(f"{aspect}: texts={len(data['texts'])}")

        print("\nMetadata rebuild complete ✅")