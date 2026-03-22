

# import os
# import json
# import faiss
# import numpy as np
# from sentence_transformers import SentenceTransformer
# from collections import defaultdict
# import pickle


# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# knowledge_base_path = os.path.join(BASE_DIR, "./phase-output/phase2-knowledge-base.json")
# os.environ['HF_HUB_DOWNLOAD_TIMEOUT'] = '600'

# class Retriever:
#     BASE_DIR = os.path.dirname(os.path.abspath(__file__))
#     INDEX_DIR = os.path.join(BASE_DIR, "faiss_raft_indices")

#     def __init__(self, model_name: str = 'intfloat/multilingual-e5-large'):
#         self.model = SentenceTransformer(model_name)
#         self.chunked_data_path = knowledge_base_path
#         self.section_data = defaultdict(list)
#         self.indices = {}
#         self.embeddings = {}

#         os.makedirs(self.INDEX_DIR, exist_ok=True)

#         if self._check_indices_exist():
#             print("Loading FAISS indices from disk...")
#             self._load_indices()
#         else:
#             print("FAISS indices not found. Building indices...")
#             self.load_data()
#             self.build_indices()
#             self._save_indices()

#     def _check_indices_exist(self):
#         section_data_exists = os.path.exists(os.path.join(self.INDEX_DIR, "section_data.pkl"))
#         if not section_data_exists:
#             return False
#         with open(os.path.join(self.INDEX_DIR, "section_data.pkl"), "rb") as f:
#             section_data = pickle.load(f)
#         for section in section_data.keys():
#             if not os.path.exists(os.path.join(self.INDEX_DIR, f"{section}.index")):
#                 return False
#         return True

#     def _save_indices(self):
#         print("Saving FAISS indices to disk...")
#         for section, index in self.indices.items():
#             faiss.write_index(index, os.path.join(self.INDEX_DIR, f"{section}.index"))
#         with open(os.path.join(self.INDEX_DIR, "section_data.pkl"), "wb") as f:
#             pickle.dump(dict(self.section_data), f)

#     def _load_indices(self):
#         with open(os.path.join(self.INDEX_DIR, "section_data.pkl"), "rb") as f:
#             self.section_data = defaultdict(list, pickle.load(f))
#         for section in self.section_data.keys():
#             index_path = os.path.join(self.INDEX_DIR, f"{section}.index")
#             self.indices[section] = faiss.read_index(index_path)

#     def load_data(self):
#         with open(self.chunked_data_path, encoding="utf-8") as f:
#             chunked_doc = json.load(f)
#         for chunk in chunked_doc:
#             self.section_data[chunk["section"]].append(chunk["content"])

#     def build_indices(self):
#         print("Encoding chunks by section...")
#         for section, contents in self.section_data.items():
#             if section in self.indices:
#                 print(f"Index for section '{section}' already exists. Skipping encoding.")
#                 continue
#             print(f"Building index for section: {section} ({len(contents)} chunks)")
            
#             embeddings = self.model.encode(contents, convert_to_numpy=True, show_progress_bar=False)
            
#             faiss.normalize_L2(embeddings)
            
#             dim = embeddings.shape[1]
#             index = faiss.IndexFlatIP(dim)  
#             index.add(embeddings)
            
#             self.indices[section] = index
#             self.embeddings[section] = embeddings

#     def retrieve(self, query: dict, top_k: int = 3):
#         section = query.get("section")
#         content = query.get("content", "")
#         if section not in self.indices:
#             print(f"Section '{section}' not found.")
#             return []
        
#         translated_content = translate_query(content, "en")
#         print("Translated content:", translated_content)

#         query_vec = self.model.encode([translated_content], convert_to_numpy=True)
#         faiss.normalize_L2(query_vec)

#         results = []

#         dist_gen, idx_gen = self.indices["General"].search(query_vec, top_k)
#         for d, i in zip(dist_gen[0], idx_gen[0]):
#             results.append((d, self.section_data["General"][i]))

#         dist_sec, idx_sec = self.indices[section].search(query_vec, top_k)
#         for d, i in zip(dist_sec[0], idx_sec[0]):
#             results.append((d, self.section_data[section][i]))

#         results.sort(key=lambda x: x[0], reverse=True)

#         return "\n".join([
#             f"{rank + 1}. {text.strip()}"
#             for rank, (score, text) in enumerate(results[:top_k])
#         ])
