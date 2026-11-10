import json
import re
import faiss
import numpy as np
import joblib
from app.config import settings, FAISS_DIR
from app.schemas import SourceCitation

STOPWORDS = {
    "what", "is", "the", "for", "and", "or", "to", "of", "in", "on", "a", "an",
    "how", "who", "when", "where", "why", "which", "are", "was", "were", "be",
    "do", "does", "did", "can", "could", "should", "would", "it", "its", "this",
    "that", "from", "with", "about", "tell", "me", "explain", "mean", "machine",
    "recommended", "allowed", "checked", "showing", "often", "much", "many",
    "policy", "there", "have", "has", "had", "into", "get", "make"
}

def extract_query_keywords(question: str) -> list[str]:
    tokens = re.findall(r'[a-zA-Z0-9\-]+', question.lower())
    return [t for t in tokens if len(t) >= 2 and t not in STOPWORDS]

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
            print(f"[Retriever] Loaded {len(self.metadata)} structured SOP chunks (100% offline).")
        else:
            print("[Retriever] Vector store not found yet. Run `python -m app.ingest` first.")

    def retrieve(self, question: str, category_filter: str = "All") -> list[SourceCitation]:
        if not self.index or not self.vectorizer or not self.metadata:
            return []

        q_sparse = self.vectorizer.transform([question])
        q_vec = np.ascontiguousarray(q_sparse.toarray(), dtype=np.float32)

        search_k = len(self.metadata)
        scores, indices = self.index.search(q_vec, search_k)

        keywords = extract_query_keywords(question)
        unique_keywords = set(keywords)

        candidates = []
        max_raw_score = 0.0
        matched_keywords_anywhere = set()

        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.metadata):
                continue
            item = self.metadata[idx]

            if category_filter and category_filter not in ["All", "All Docs", ""]:
                if item["category"].lower() != category_filter.lower():
                    continue

            raw_score = float(score)
            if raw_score > max_raw_score:
                max_raw_score = raw_score

            # Count exact query keyword hits in the chunk body + filename
            search_surface = (item["text"] + " " + item["source_file"]).lower()
            hits_in_chunk = {kw for kw in unique_keywords if kw in search_surface}
            matched_keywords_anywhere.update(hits_in_chunk)

            kw_ratio = len(hits_in_chunk) / max(len(unique_keywords), 1)
            rev_bonus = 0.02 if "rev04" in item["source_file"].lower() else 0.0

            combined_score = raw_score + (0.35 * kw_ratio) + rev_bonus
            candidates.append((combined_score, raw_score, len(hits_in_chunk), item))

        # STRICT ZERO-HALLUCINATION GUARDRAILS:
        # 1. Corpus vector similarity must pass threshold
        if max_raw_score < settings.SIMILARITY_THRESHOLD:
            return []

        # 2. Prevent single-word TF-IDF traps (e.g. "business class" matching table header "Class: Critical")
        # Require meaningful keyword coverage across the corpus for multi-word queries
        corpus_coverage = len(matched_keywords_anywhere) / max(len(unique_keywords), 1)
        if len(unique_keywords) >= 3 and corpus_coverage < 0.35:
            return []
        if len(unique_keywords) >= 1 and len(matched_keywords_anywhere) == 0:
            return []

        # Sort by combined hybrid score (ensures content/table chunks outrank generic headers)
        candidates.sort(key=lambda x: x[0], reverse=True)

        results: list[SourceCitation] = []
        for combined_score, raw_score, hit_count, item in candidates:
            # Once query is confirmed in-scope, keep chunks that match keywords OR pass a floor score
            if raw_score < 0.03 and hit_count == 0 and len(results) > 0:
                continue

            results.append(
                SourceCitation(
                    source_file=item["source_file"],
                    page_number=item["page_number"],
                    category=item["category"],
                    snippet=item["text"],
                    score=round(min(combined_score, 0.99), 3)
                )
            )
            if len(results) >= max(settings.TOP_K, 4):
                break

        return results

retriever = SOPRetriever()
