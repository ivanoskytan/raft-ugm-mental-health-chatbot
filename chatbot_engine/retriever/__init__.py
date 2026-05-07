import numpy as np
import logging
import psycopg
from supabase import create_client, Client
from chatbot_engine.llm_client import GPTClient
from config.config import Settings
from tenacity import retry, stop_after_attempt, wait_exponential

settings = Settings.load()

class Retriever:
    def __init__(self):
        self.gpt_client = GPTClient(
            api_key=settings.OPENAI_API_KEY,
            model="text-embedding-3-small"
        )

        self.conn_info = (
            "host=chatbotknowledgevectordb.postgres.database.azure.com "
            "user=joyivan777 "
            "password=Kut754jio08# "
            "dbname=postgres "
            "sslmode=require"
        )

        self.logger = logging.getLogger("Retriever")

    def _embed(self, text: str):
        try:
            embedding = self.gpt_client.get_embedding(text)
            return embedding[0]
        except Exception as e:
            self.logger.error(f"Embedding failed: {e}")
            raise
    
    @retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=4, max=10),
            reraise=True
    )
    def run(self, query, aspect, top_k=5):
        self.logger.info(f"[Retriever] Querying aspect: {aspect}")

        query_embedding = self._embed(query)
        results = []

        try:
            with psycopg.connect(self.conn_info) as conn:
                with conn.cursor() as cur:
                    sql = """
                    SELECT 
                        content, 1 - (embedding <=> %s) AS similarity
                    FROM documents
                    WHERE aspect = %s
                    ORDER BY similarity DESC
                    LIMIT %s
                    """

                    cur.execute(sql, (query_embedding, aspect, top_k))
                    rows = cur.fetchall()

                    if not rows:
                        self.logger.warning(f"No results found for aspect: {aspect}")   
                        return []
                    
                    for i, (content, similarity) in enumerate(rows):
                        results.append({
                            "rank": i+1,
                            "chunk": content,
                            "score": float(similarity)
                        })

        except Exception as e:
            self.logger.error(f"Azure ProstgreSQL query failed: {e}")
            raise RuntimeError(f"Retriever failed: {e}")

        self.logger.info(f"[Retriever] Retrieved {len(results)} chunks")

        return results