import numpy as np
import logging
from supabase import create_client, Client
from chatbot_engine.llm_client import GPTClient
from config.config import Settings

settings = Settings.load()

class Retriever:
    def __init__(self):
        self.gpt_client = GPTClient(
            api_key=settings.OPENAI_API_KEY,
            model="text-embedding-3-small"
        )

        self.supabase: Client = create_client(
            settings.VECTORSTORE_URL,
            settings.VECTORSTORE_KEY,
        )

        self.supabase.postgrest.timeout = 60

        self.logger = logging.getLogger("Retriever")

    def _embed(self, text: str):
        try:
            embedding = self.gpt_client.get_embedding(text)
            return embedding[0]
        except Exception as e:
            self.logger.error(f"Embedding failed: {e}")
            raise

    def run(self, query, aspect, top_k=5):
        self.logger.info(f"[Retriever] Querying aspect: {aspect}")

        query_embedding = self._embed(query)

        try:
            response = self.supabase.rpc(
                "match_documents",
                {
                    "query_embedding": query_embedding,
                    "match_aspect": aspect,
                    "match_count": top_k
                }
            ).execute()

        except Exception as e:
            self.logger.error(f"Supabase RPC failed: {e}")
            raise RuntimeError(f"Retriever failed: {e}")

        if not response.data:
            raise RuntimeError(f"No results for aspect '{aspect}'")

        results = []
        for i, row in enumerate(response.data):
            results.append({
                "rank": i + 1,
                "score": float(row["similarity"]),
                "chunk": row["content"]
            })

        self.logger.info(f"[Retriever] Retrieved {len(results)} chunks")

        return results