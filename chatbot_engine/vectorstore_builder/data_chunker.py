import logging
import os
import tqdm
import json

class DataChunker:
    def __init__(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.files_dir = os.path.join(base_dir, "data", "text_files")
        self.chunked_files_dir = os.path.join(base_dir, "data", "chunked_files")
        self.chunk_size = 180
        self.overlap_size = 30

    def chunk_all_files(self):
        files = [f for f in os.listdir(self.files_dir) if f.endswith(".txt")]

        logging.info(f"Found {len(files)} text files")

        for filename in tqdm.tqdm(files, desc="Chunking all text files"):
            aspect = filename.replace(".txt", "")
            input_path = os.path.join(self.files_dir, filename)
            self.chunk_single_file(input_path, aspect)

    def chunk_single_file(self, file_path, aspect):
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read().strip()

        if not text:
            logging.warning(f"[{aspect}] Empty text file, skipping...")
            return

        chunks = []
        start = 0
        text_length = len(text)

        estimated_chunks = max(1, text_length // (self.chunk_size - self.overlap_size))

        pbar = tqdm.tqdm(total=estimated_chunks, desc=f"[{aspect}] Chunking", leave=False)

        while start < text_length:
            end = start + self.chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            pbar.update(1)

            start = end - self.overlap_size

        pbar.close()

        os.makedirs(self.chunked_files_dir, exist_ok=True)

        output_path = os.path.join(self.chunked_files_dir, f"{aspect}.json")

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)

        logging.info(f"[{aspect}] Saved {len(chunks)} chunks to {output_path}")