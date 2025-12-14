import faiss
from sentence_transformers import SentenceTransformer

class VectorMemory:
    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.index = faiss.IndexFlatL2(384)
        self.texts = []

    def store(self, text):
        emb = self.model.encode([text])
        self.index.add(emb)
        self.texts.append(text)

    def retrieve(self, query, k=3):
        if self.index.ntotal == 0:
            return ""
        emb = self.model.encode([query])
        _, idx = self.index.search(emb, k)
        return "\n".join(self.texts[i] for i in idx[0])
