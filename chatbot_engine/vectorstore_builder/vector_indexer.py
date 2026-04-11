import logging
import os
import json
from tqdm import tqdm
from supabase import create_client, Client
from chatbot_engine.llm_client import GPTClient
from config.config import Settings

settings = Settings.load()


class VectorIndexer:
    def __init__(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.chunked_files_dir = os.path.join(base_dir, "data", "chunked_files")

        self.gpt_client = GPTClient(
            api_key=settings.OPENAI_API_KEY,
            model="text-embedding-3-small"
        )

        self.logger = logging.getLogger("VectorIndexer")

        self.supabase: Client = create_client(
            settings.VECTORSTORE_URL,
            settings.VECTORSTORE_KEY
        )

        self.group_size = 300   # you can tune this (200–500 recommended)

    def build_index(self, force=False):
        json_files = [
            f for f in os.listdir(self.chunked_files_dir)
            if f.endswith(".json")
        ]

        if not json_files:
            raise RuntimeError("No chunked JSON files found")

        pbar = tqdm(json_files, desc="Processing Aspects")

        for filename in pbar:
            aspect = filename.replace(".json", "")
            json_path = os.path.join(self.chunked_files_dir, filename)

            pbar.set_postfix_str(f"Reading: {aspect}")

            if not force:
                existing = self.supabase.table("documents") \
                    .select("id") \
                    .eq("aspect", aspect) \
                    .limit(1) \
                    .execute()

                if existing.data:
                    self.logger.info(f"[{aspect}] already indexed, skipping...")
                    continue

            with open(json_path, "r", encoding="utf-8") as f:
                chunks = json.load(f)

            raw_texts = self._extract_texts(chunks)
            texts = [self._clean_text(t) for t in raw_texts if t and t.strip()]

            if not texts:
                continue

            embeddings = self._embed_in_batches(texts, batch_size=20)

            if not embeddings:
                self.logger.warning(f"[{aspect}] No embeddings generated")
                continue

            records = []
            for idx, (text, emb) in enumerate(zip(texts, embeddings)):
                group_id = idx // self.group_size

                records.append({
                    "aspect": aspect,
                    "group_id": group_id,
                    "content": text,
                    "embedding": emb
                })

            upload_batch_size = 100

            for i in range(0, len(records), upload_batch_size):
                batch = records[i:i + upload_batch_size]
                try:
                    self.supabase.table("documents").insert(batch).execute()
                except Exception as e:
                    self.logger.error(f"[{aspect}] DB Insert failed: {e}")

            self.logger.info(
                f"[{aspect}] Uploaded {len(records)} chunks "
                f"into {max(r['group_id'] for r in records) + 1} groups"
            )

    def _embed_in_batches(self, texts, batch_size=20):
        all_vectors = []
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            try:
                vectors = self.gpt_client.get_embedding(batch_texts)
                if not isinstance(vectors, list):
                    raise ValueError("Embedding output is not a list")
                
                for v in vectors:
                    if not isinstance(v, list):
                        raise ValueError(f"Invalid embedding format: {type(v)}")
                    
                if isinstance(vectors, list) and isinstance(vectors[0], float):
                    vectors = [vectors]
                all_vectors.extend(vectors)
            except Exception as e:
                self.logger.error(f"Batch embedding failed: {e}")
        return all_vectors

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

    def _clean_text(self, text):
        if not text:
            return ""
        text = text.replace("\x00", "")
        return "".join(
            ch for ch in text
            if ch == "\n" or ch == "\t" or ord(ch) >= 32
        ).strip()