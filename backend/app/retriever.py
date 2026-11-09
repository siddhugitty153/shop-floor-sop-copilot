import json
import faiss
import numpy as np
import joblib
from app.config import settings, FAISS_DIR
from app.schemas import SourceCitation

class SOPRetriever:
    def __init__(self):
        self.vectorizer = None
        self.index = None
        self.metadata = []
        self.load_store()

    def load_store(self):
        index_file = FAISS_DIR / "index.faiss"
        meta_file = FAISS_DIR / "metadata.json"
        vec_file = FAISS_DIR / "vectorizer.joblib"

        if index_file.exists() and meta_file.exists() and vec_file.exists():
            self.index = faiss.read_index(str(index_file))
            self.vectorizer = joblib.load(str(vec_file))
            with open(meta_file, "r", encoding="utf-8") as f:
                self.metadata = json.load(f)
            print(f"[Retriever] Loaded {len(self.metadata)} SOP chunks and TF-IDF vectorizer (100% offline).")
        else:
            print("[Retriever] Vector store not found yet. Run `python -m app.ingest` first.")

    def retrieve(self, question: str, category_filter: str = "All") -> list[SourceCitation]:
        if not self.index or not self.vectorizer or not self.metadata:
            return []

        # Transform question to L2-normalized TF-IDF vector
        q_sparse = self.vectorizer.transform([question])
        q_vec = np.ascontiguousarray(q_sparse.toarray(), dtype=np.float32)

        # Search all available chunks in the corpus
        search_k = len(self.metadata)
        scores, indices = self.index.search(q_vec, search_k)

        results: list[SourceCitation] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.metadata):
                continue
            if float(score) < settings.SIMILARITY_THRESHOLD:
                continue

            item = self.metadata[idx]
            if category_filter and category_filter not in ["All", "All Docs", ""]:
                if item["category"].lower() != category_filter.lower():
                    continue

            results.append(
                SourceCitation(
                    source_file=item["source_file"],
                    page_number=item["page_number"],
                    category=item["category"],
                    snippet=item["text"],
                    score=round(float(score), 3)
                )
            )
            if len(results) >= max(settings.TOP_K, 5):
                break

        return results

retriever = SOPRetriever()
