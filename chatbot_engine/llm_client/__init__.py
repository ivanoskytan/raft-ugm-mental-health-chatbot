import logging
from openai import OpenAI

class GPTClient:
    def __init__(self, api_key, model = "gpt-4o"):
        self.api_key = api_key
        self.model = model

        try:
            self.client = OpenAI(api_key=api_key)
        except Exception as err:
            logging.error(f"GPT Client: Failed to initialize client {err}")
            raise
    
    def run_prompt(self, system_prompt, user_prompt, temperature = 0.7):
        try:
            response = self.client.chat.completions.create(
                model = self.model,
                temperature = temperature,
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ]
            )

            return response.choices[0].message.content
        
        except Exception as err:
            logging.error(f"GPTClient: Error while generating response: {err}")
            return None
        
    def get_embedding(self, text):
        try:
            if isinstance(text, str):
                text = [text]

            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )

            embeddings = [item.embedding for item in response.data]
            
            return embeddings

        except Exception as err:
            logging.error(f"GPTClient: Error generating embedding: {err}")
            return None
    