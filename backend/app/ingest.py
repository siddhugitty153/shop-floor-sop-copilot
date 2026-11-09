import json
import re
import fitz  # PyMuPDF
import faiss
import numpy as np
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from app.config import settings, PDF_DIR, FAISS_DIR

def infer_category(filename: str, text: str) -> str:
    combined = (filename + " " + text[:300]).lower()
    if any(k in combined for k in ["safety", "loto", "lockout", "ppe", "hazard", "emergency"]):
        return "Safety"
    if any(k in combined for k in ["quality", "inspection", "tolerance", "defect", "calibration"]):
        return "Quality"
    if any(k in combined for k in ["maintenance", "repair", "lubrication", "preventive", "hydraulic", "valve"]):
        return "Maintenance"
    return "General"

def clean_text(text: str) -> str:
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def chunk_page_text(text: str, chunk_size: int = 700, overlap: int = 150) -> list[str]:
    if len(text) <= chunk_size:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk.strip())
        if end >= len(text):
            break
        start += chunk_size - overlap
    return chunks

def build_vector_store():
    FAISS_DIR.mkdir(parents=True, exist_ok=True)
    PDF_DIR.mkdir(parents=True, exist_ok=True)

    pdf_files = sorted([f for f in PDF_DIR.iterdir() if f.suffix.lower() == ".pdf"])
    if not pdf_files:
        print(f"[WARNING] No PDFs found in {PDF_DIR}. Place the plant PDFs in data/pdfs/ first.")
        return

    print("Reading and chunking PDFs...")
    metadata = []
    corpus = []

    for pdf_path in pdf_files:
        doc = fitz.open(pdf_path)
        print(f"Parsing {pdf_path.name} ({len(doc)} pages)...")
        for page_idx in range(len(doc)):
            raw_text = doc[page_idx].get_text("text")
            cleaned = clean_text(raw_text)
            if len(cleaned) < 30:
                continue
            page_chunks = chunk_page_text(cleaned)
            for c_idx, chunk_str in enumerate(page_chunks):
                cat = infer_category(pdf_path.name, chunk_str)
                contextualized_chunk = f"Document: {pdf_path.name} (Page {page_idx + 1}, Category: {cat}) | Content: {chunk_str}"
                corpus.append(contextualized_chunk)
                metadata.append({
                    "chunk_id": f"{pdf_path.stem}_p{page_idx+1}_c{c_idx+1}",
                    "source_file": pdf_path.name,
                    "page_number": page_idx + 1,
                    "category": cat,
                    "text": chunk_str
                })

    print(f"Encoding {len(corpus)} chunks with 100% offline TfidfVectorizer (L2 normalized)...")
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        stop_words="english",
        sublinear_tf=True,
        norm="l2"
    )
    tfidf_matrix = vectorizer.fit_transform(corpus)
    dense_embeddings = np.ascontiguousarray(tfidf_matrix.toarray(), dtype=np.float32)

    dim = dense_embeddings.shape[1]
    print(f"Building FAISS IndexFlatIP (dim={dim}, items={dense_embeddings.shape[0]})...")
    # IndexFlatIP on L2-normalized vectors calculates exact Cosine Similarity
    index = faiss.IndexFlatIP(dim)
    index.add(dense_embeddings)

    faiss.write_index(index, str(FAISS_DIR / "index.faiss"))
    joblib.dump(vectorizer, str(FAISS_DIR / "vectorizer.joblib"))

    with open(FAISS_DIR / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"[SUCCESS] Indexed {len(metadata)} chunks across {len(pdf_files)} PDFs into {FAISS_DIR} (100% offline).")

if __name__ == "__main__":
    build_vector_store()
