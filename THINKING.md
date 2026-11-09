# Engineering Thought Process & Design Decisions (`THINKING.md`)

## 1. Problem Context & Shop-Floor Operational Reality

In a discrete manufacturing or precision component plant (e.g., Kaveri Precision Components, Hosur Plant), machine operators and shop-floor shift supervisors operate under intense physical and temporal constraints:
- **Harsh Environment:** Noisy machinery, bright factory lighting or dim maintenance bays, oily hands, and mandatory safety work gloves.
- **High Consequence of Error:** An ungrounded guess on a hydraulic pressure bleed, high-voltage breaker, or spindle torque can result in severe physical injury or equipment destruction worth millions.
- **Speed & Accessibility:** Supervisors do not have the time or screen real estate to read 30-page PDF manuals on small phone screens during shifts. Answers must be immediate, bulleted, and strictly verifiable against physical manuals.

---

## 2. Core Architectural Decisions

### 2.1 Embedding & Vector Search Strategy: 100% Offline TF-IDF + FAISS `IndexFlatIP`
- **Initial Plan vs. Production Reality:** The initial blueprint proposed `all-MiniLM-L6-v2` via Hugging Face. In real plant environments and corporate networks, outbound connections to Hugging Face often fail due to firewalls, SSL inspection proxies, or air-gapped security policies.
- **The Solution:** For ~4–10 core plant SOPs (~25–100 chunks total), we implemented `scikit-learn`'s `TfidfVectorizer` (with unigram + bigram features, sublinear term-frequency scaling, and L2 normalization) coupled directly with **FAISS `IndexFlatIP`** (Inner Product on L2-normalized vectors).
- **Benefits:**
  1. **Zero External Network Dependencies:** No model downloads, zero Hugging Face dependency, zero SSL verification issues.
  2. **Exact Cosine Similarity:** In L2-normalized space, inner product is mathematically identical to cosine similarity.
  3. **Deterministic & Ultra-Fast:** Sub-millisecond vector indexing and query retrieval ($0\text{--}24\text{ms}$).
  4. **Sharp Refusal Boundary:** Domain queries score $0.11\text{--}0.18$, whereas out-of-scope queries (e.g., flight reimbursement) score $< 0.06$. Setting `SIMILARITY_THRESHOLD = 0.085` provides a clean mathematical guardrail.

### 2.2 Multi-Tier Grounded Generation (Local LLM $\to$ Hosted API $\to$ Extractive Fallback)
To ensure 100% uptime regardless of connectivity or hardware tier, the system employs a three-tier execution hierarchy:
1. **Tier 1 (Local LLM via Ollama):** When configured, queries `llama3.2:3b` or `qwen2.5:3b` locally on `http://localhost:11434`.
2. **Tier 2 (Hosted API via Groq / Gemini):** Fast sub-second inference via `llama-3.1-8b-instant` when an API key is provided.
3. **Tier 3 (Deterministic Extractive Fallback):** If neither Ollama nor an API key is active, the engine directly extracts and synthesizes the top verified SOP bullet points with inline page and document citations. The app remains 100% functional offline with zero keys.

### 2.3 Strict Grounding & Zero-Hallucination Guardrail
- Every retrieved snippet is explicitly tagged with `source_file`, `page_number`, and `category`.
- If FAISS retrieval returns no chunks above the similarity threshold (`0.085`), or if the LLM identifies that the excerpts lack the answer, `is_answerable` is immediately set to `False`.
- Refusal answers are standardized:
  > *"This information is not found in the provided plant SOPs and manuals. Do not guess procedures—please contact Plant Engineering or your Shift Lead."*

---

## 3. Shop-Floor User Journey Innovations

### 3.1 Automated Safety / Lockout-Tagout (LOTO) Hazard Banner
- Whenever retrieved evidence mentions critical industrial hazards (`LOTO`, `Lockout`, `PPE`, `Safety Goggles`, `High Voltage`, `Pressure Bleed`), the copilot extracts an urgent, highlighted warning banner rendered in high-contrast red/amber stripes at the top of the screen.
- A supervisor glancing at their phone instantly sees the mandatory isolation steps before proceeding with any mechanical disassembly.

### 3.2 Expandable Raw Evidence Accordion
- AI summaries can sometimes obscure nuanced machine specs. Below every answer, high-contrast citation badges show the source file, page number, and similarity percentage.
- Tapping a badge expands the exact verbatim PDF sentence block inline, allowing supervisors to verify physical manual text without downloading or opening a heavy PDF viewer.

### 3.3 Rugged Mobile-First Ergonomics & Voice Input
- High-contrast industrial dark palette (`#090D16` background, `#F59E0B` safety amber, `#EF4444` emergency red).
- All touch targets (category pills, question chips, submit buttons) are strictly $\ge 48\text{px}$ high, ensuring workers wearing work gloves do not experience mis-taps.
- One-tap hands-free voice input via the browser's `SpeechRecognition` API allows supervisors with dirty or occupied hands to speak questions directly.

### 3.4 Zero-Config Local Area Network (LAN) Auto-Discovery
- Mobile browsers connecting over Wi-Fi (e.g., `http://192.168.1.45:5173`) cannot access `localhost:8000` because `localhost` refers to the mobile device itself.
- The React client dynamically evaluates `http://${window.location.hostname}:8000`, seamlessly routing API calls from the phone to the host laptop without manual configuration.

---

## 4. SOP Document Revision Handling

The repository includes both `QC-SOP-014_Rev03` and `QC-SOP-014_Rev04` for incoming material inspection:
- In real plant environments, multiple revisions frequently coexist during transition audits.
- The chunking and vector indexing system explicitly embeds the revision and document name into the searchable context (`Document: QC-SOP-014_Rev04 (Page 1) | Content: ...`).
- When answering quality questions, the copilot cites both revisions transparently, highlighting revision history changes (e.g., sample size change from 5 to AQL table).

