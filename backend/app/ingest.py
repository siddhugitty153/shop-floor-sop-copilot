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
    if any(k in combined for k in ["quality", "inspection", "tolerance", "defect", "calibration", "bh-220"]):
        return "Quality"
    if any(k in combined for k in ["maintenance", "repair", "lubrication", "preventive", "hydraulic", "valve", "tx-200"]):
        return "Maintenance"
    return "General"

def clean_line(s: str) -> str:
    return re.sub(r'\s+', ' ', s).strip()

def is_inside_any_table(bbox, table_bboxes) -> bool:
    x0, y0, x1, y1 = bbox
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    for tx0, ty0, tx1, ty1 in table_bboxes:
        if tx0 - 2 <= cx <= tx1 + 2 and ty0 - 2 <= cy <= ty1 + 2:
            return True
    return False

def format_table(rows: list) -> str:
    if not rows:
        return ""
    first_cell = clean_line(str(rows[0][0] or ""))
    # Detect 4-column key-value metadata table at top of page
    if first_cell == "Document No.":
        pairs = []
        for r in rows:
            cells = [clean_line(str(c or "")) for c in r]
            for i in range(0, len(cells) - 1, 2):
                if cells[i] and cells[i + 1] and cells[i + 1] != "See footer":
                    pairs.append(f"{cells[i]}: {cells[i + 1]}")
        return " | ".join(pairs)

    headers = [clean_line(str(h or "")) for h in rows[0]]
    formatted_rows = []
    for r in rows[1:]:
        cells = [clean_line(str(c or "")) for c in r]
        pairs = []
        for h, c in zip(headers, cells):
            if c:
                pairs.append(f"{h}: {c}" if h else c)
        if pairs:
            formatted_rows.append("• " + " | ".join(pairs))
    return "\n".join(formatted_rows)

def extract_page_elements(page) -> list[str]:
    tabs = page.find_tables()
    table_bboxes = [t.bbox for t in tabs.tables]
    elements = []  # (y_pos, text)

    # 1. Extract prose outside tables
    for b in page.get_text("blocks"):
        x0, y0, x1, y1, txt, block_no, block_type = b
        if block_type != 0:
            continue
        if is_inside_any_table((x0, y0, x1, y1), table_bboxes):
            continue
        cleaned = clean_line(txt)
        if not cleaned or len(cleaned) < 5:
            continue
        if "Uncontrolled copy when printed" in cleaned or re.match(r'^Page \d+$', cleaned):
            continue
        elements.append((y0, cleaned))

    # 2. Extract tables with explicit column headers preserved
    for t in tabs.tables:
        formatted = format_table(t.extract())
        if formatted:
            elements.append((t.bbox[1], formatted))

    elements.sort(key=lambda x: x[0])
    return [e[1] for e in elements]

def group_into_sections(elements: list[str], max_chunk_chars: int = 1100) -> list[str]:
    """Group page elements into coherent logical sections without cutting tables or words."""
    sections = []
    current_parts = []
    current_len = 0

    for el in elements:
        is_heading = bool(re.match(r'^\d+\.\s+[A-Z]', el))
        # Start a new chunk when a major numbered heading appears and current chunk has meaningful content
        if is_heading and current_len > 250:
            sections.append("\n".join(current_parts))
            current_parts = [el]
            current_len = len(el)
        elif current_len + len(el) > max_chunk_chars and current_parts:
            sections.append("\n".join(current_parts))
            # If the previous item was a heading, carry it over so context is preserved
            if len(current_parts[-1]) < 90 and re.match(r'^\d+\.\s+', current_parts[-1]):
                carried_heading = current_parts[-1]
                current_parts = [carried_heading, el]
                current_len = len(carried_heading) + len(el)
            else:
                current_parts = [el]
                current_len = len(el)
        else:
            current_parts.append(el)
            current_len += len(el)

    if current_parts:
        sections.append("\n".join(current_parts))

    return sections

def build_vector_store():
    FAISS_DIR.mkdir(parents=True, exist_ok=True)
    PDF_DIR.mkdir(parents=True, exist_ok=True)

    pdf_files = sorted([f for f in PDF_DIR.iterdir() if f.suffix.lower() == ".pdf"])
    if not pdf_files:
        print(f"[WARNING] No PDFs found in {PDF_DIR}. Place the plant PDFs in data/pdfs/ first.")
        return

    print("Reading and chunking PDFs with structure-aware table extraction...")
    metadata = []
    corpus = []

    for pdf_path in pdf_files:
        doc = fitz.open(pdf_path)
        print(f"Parsing {pdf_path.name} ({len(doc)} pages)...")
        # Extract document title from Page 1 first non-meta line if available
        doc_title = pdf_path.stem.replace("_", " ")

        for page_idx in range(len(doc)):
            elements = extract_page_elements(doc[page_idx])
            if not elements:
                continue
            if page_idx == 0 and len(elements[0]) < 150 and "Kaveri Precision" in elements[0]:
                doc_title = elements[0]

            section_chunks = group_into_sections(elements)
            for c_idx, chunk_str in enumerate(section_chunks):
                if len(chunk_str) < 25:
                    continue
                cat = infer_category(pdf_path.name, chunk_str)
                # Keep contextual vector text focused on content + title keywords (avoid over-weighting boilerplate filename)
                contextualized_chunk = f"{doc_title} | {chunk_str}"
                corpus.append(contextualized_chunk)
                metadata.append({
                    "chunk_id": f"{pdf_path.stem}_p{page_idx+1}_c{c_idx+1}",
                    "source_file": pdf_path.name,
                    "page_number": page_idx + 1,
                    "category": cat,
                    "text": chunk_str
                })

    print(f"Encoding {len(corpus)} structured chunks with 100% offline TfidfVectorizer (L2 normalized)...")
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
    index = faiss.IndexFlatIP(dim)
    index.add(dense_embeddings)

    faiss.write_index(index, str(FAISS_DIR / "index.faiss"))
    joblib.dump(vectorizer, str(FAISS_DIR / "vectorizer.joblib"))

    with open(FAISS_DIR / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"[SUCCESS] Indexed {len(metadata)} structured chunks across {len(pdf_files)} PDFs into {FAISS_DIR}.")

if __name__ == "__main__":
    build_vector_store()
