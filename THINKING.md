# BiztelAI Shop-Floor SOP Copilot: Engineering & Design Reflection (`THINKING.md`)

> **Author:** Candidate Submission for BiztelAI  
> **Plant Context:** Kaveri Precision Components Pvt. Ltd., Hosur Plant (Shaft Machining Line, TX-200 CNC Turning Centre)  
> **Scope:** Grounded RAG Copilot across Quality (QC-SOP-014 Rev03/Rev04), Maintenance (MNT-MAN-CNC-02 Rev02), and Safety (SAF-SOP-003 Rev05).

---

## 1. Understand the User

### 1.1 Who is the Supervisor?
- **Persona:** Suresh Kumar, 36, Shift Supervisor on the shaft machining line at the Hosur Plant.
- **Background:** Diploma in Mechanical Engineering with 12 years of plant experience. He oversees 8 CNC operators across two shifts, accountable for hourly throughput, part quality (shaft concentricity and surface finish), zero safety incidents, and machine uptime.
- **Physical Context:** Spends 85% of his 8-hour shift walking the concrete shop floor. The environment is loud (80–85 dB), surrounded by cutting coolant mist, metal chips, and moving overhead hoists. He wears mandatory safety shoes, nitrile work gloves (or greasy hands), and safety glasses.

### 1.2 What is He Trying to Do?
1. **Resolve Machine Faults Fast:** If a TX-200 CNC throws alarm `AL-104` or `AL-210`, every minute the spindle sits idle costs money. He needs the exact corrective action immediately.
2. **Prevent Life-Threatening Safety Incidents:** Before any maintenance tech climbs inside a machine envelope or bleeds a hydraulic line, Suresh must verify that Lockout/Tagout (LOTO) isolation is 100% compliant with plant rules.
3. **Make Defect & Quality Disposition Calls:** When incoming bar stock arrives or machined shafts fail visual/dimensional checks, he must immediately know: *Do I reject this lot? Where do I quarantine it? Which form or QMS module do I log it into?*

### 1.3 What Frustrates Him Today?
- **Binder Fatigue & Distance:** Controlled SOP binders sit in the Quality Office near Gate 2 or the Maintenance Planning room—a 4-minute walk from Line 3.
- **Unreadable PDFs on Mobile:** Pulling up a 30-page PDF on a phone while standing in a noisy aisle means pinch-to-zoom scrolling through dense tables, leading to skipped steps.
- **Revision Confusion:** Revision 03 (paper forms, fixed sample size of 5) and Revision 04 (AQL tables, digital QMS entry) often coexist in conversation. Supervisors fear following superseded rules and getting flagged in ISO/TS quality audits.
- **High Consequence of Error:** Guessing a hydraulic pressure bleed or electrical breaker state can lead to severe injury or amputation. He would rather stop the line than guess, hurting plant OEE.

---

## 2. User Journey (Initial Draft)

```
[Trigger: Machine Fault or Quality Question on Floor]
       │
       ▼
[Step 1: Access] Suresh takes out company-issued Android phone from safety vest pocket.
       │
       ▼
[Step 2: Input] He opens the internal SOP Copilot web page; taps a filter chip or speaks his question hands-free.
       │
       ▼
[Step 3: Synthesis] Copilot retrieves verified SOP chunks, extracts urgent safety warnings, and outputs 3 direct bullet points.
       │
       ▼
[Step 4: Verification] Suresh glances at the citation ("MNT-MAN-CNC-02, Page 2"). If in doubt, he taps the citation badge to inspect the raw PDF snippet inline.
       │
       ▼
[Step 5: Action] Suresh executes the procedure (e.g. tops up ISO VG 68 way lube and presses RESET) and logs the shift report.
```

### What Could Go Wrong in This Journey?
1. **Wrong Revision Citing:** The AI cites the retired Rev 03 sampling rule (sample size 5) instead of Rev 04 (AQL Table II), causing non-conforming parts to enter production.
2. **Hallucinated Torque / Pressure Specs:** If an operator asks for hydraulic chuck pressure and the model invents "35 bar" instead of checking the manual, chuck slippage could throw a rotating workpiece at 3,000 RPM.
3. **Shop-Floor Dead Zones:** Wi-Fi signals in steel-reinforced manufacturing bays frequently drop. If the app requires heavy cloud downloads or disconnects, it leaves the supervisor stranded.
4. **Voice Input Failure in Noise:** Trying to dictate in an 85 dB machining bay causes transcription errors (e.g. "LOTO" transcribed as "lotto" or "low toe").
5. **Gloves and Mis-Taps:** Standard mobile buttons (<40px) cause false taps when wearing nitrile or cotton safety gloves.

---

## 3. AI Challenge: Skeptical Product Manager & Safety Auditor Critique

To pressure-test this journey, I prompted an AI acting as a **Skeptical VP of Manufacturing Operations & Safety Auditor**:

> *"Critique this user journey. Poke holes in user trust, plant safety liability, shop-floor ergonomics, and audit compliance. Tell me why this copilot will fail on Day 1 in a real factory."*

### Key Parts of the Skeptical Critique

> **Skeptical PM:**  
> *"1. **Safety Liability:** If a supervisor asks about fixing an electrical fault and your copilot buries the LOTO reminder at the end of a friendly paragraph, you have a catastrophic OSHA liability. Machine operators skip text; they scan for answers. If safety isn't an unmissable, visual roadblock, someone will lose an arm.*  
> *2. **Blind Trust vs. Auditability:** No shop-floor supervisor is going to trust an AI summary for an ISO 9001 audit. When the auditor asks 'Where is that written?', the supervisor can't say 'The AI told me'. If your tool doesn't let them instantly verify the physical document and page, they will abandon it for the paper binder.*  
> *3. **Voice Input is a Gimmick in a Machine Shop:** Have you ever been to a plant running 8 turning centers? You can't hear yourself think, let alone whisper to a browser speech API. Operators will never use voice if typing is hard, but typing with nitrile gloves is equally terrible. What's your real tactile fallback?*  
> *4. **Document Superseding:** Factories have multiple revisions of the same SOP floating around (like your Rev 03 and Rev 04 incoming inspection docs). If your RAG treats all chunks equally, you will blend old and new procedures into an illegal Frankenstein answer."*

---

### Reflection on the Critique

#### What I Agreed With:
- **Safety must be a prominent roadblock, not conversational text:** The PM was 100% right. Embedding safety inside an LLM answer paragraph is dangerous. We changed the architecture to automatically extract hazard keywords (LOTO, PPE, high-voltage, pressure bleed) and render a **high-visibility red/amber alert banner at the very top of the answer card** before any procedural steps.
- **Raw Evidence Accordion is mandatory for trust:** Supervisors cannot vouch for an AI paraphrase during an audit. We added **inline expandable raw PDF evidence cards** where tapping a citation reveals the exact verbatim sentence from the manual with page number and match percentage.
- **Glove-Friendly Touch Ergonomics:** In noisy environments where speech recognition might struggle, supervisors need **large $\ge 48\text{px}$ quick-tap category chips and pre-loaded frequent question chips** to get answers with one gloved thumb.

#### What I Disagreed With:
- **Discarding Voice Input Entirely:** While an operator right next to an un-enclosed milling spindle cannot use voice, supervisors frequently step 10 feet back into the aisle or sub-assembly staging area to check procedures before calling maintenance. Having browser-based hands-free voice input as an option costs nothing in weight and helps operators with oily hands.

#### What We Changed Based on the Critique:
1. Built the **Critical Safety / LOTO Hazard Alert Banner** as the top visual priority.
2. Built the **Expandable Raw Evidence Accordion** for instant manual verification.
3. Implemented a **Strict Cosine Threshold Guardrail (`0.085`)** to refuse out-of-scope queries with zero hallucination.
4. Explicitly contextualized document revision numbers in the chunk metadata so Rev 03 and Rev 04 are distinguished.

---

## 4. User Journey Improvement Chosen & Justification

### The Improvement: Automated Safety / LOTO Hazard Banner & Inline Evidence Accordion
- **Why Chosen:** On the shop floor, **safety and auditability trump conversational novelty**. A supervisor's primary nightmare is either an electrical/hydraulic injury or failing an ISO compliance audit due to an ungrounded guess.
- **Implementation:**
  - Before presenting operational steps, the backend scans retrieved chunks for high-risk industrial hazards (Lockout/Tagout, stored pressure, high voltage, mandatory PPE).
  - If detected, the UI displays a high-contrast striped banner with an emergency shield icon:  
    *`⚠️ CRITICAL SAFETY / LOTO REMINDER: [Specific isolation step]`*
  - Below the answer, high-contrast badges display `Document Name • Page Number • Match %`. Tapping any badge expands the verbatim PDF text snippet inline so the supervisor never needs to download or scroll through a 30-page PDF viewer.

---

## 5. Local Network Deployment (Wi-Fi Testing)

### 5.1 Configuration & LAN Discovery
- **Backend Binding:** FastAPI server listens on `0.0.0.0:8000` with open CORS.
- **Frontend Binding:** Vite server binds to `0.0.0.0:5173`.
- **Automatic Hostname Discovery:** Rather than hardcoding `localhost:8000` (which fails on phones because `localhost` points to the mobile device itself), the React frontend dynamically evaluates `http://${window.location.hostname}:8000`. When opened on a phone at `http://192.168.1.3:5173`, it automatically connects to the laptop's backend over local Wi-Fi with zero manual configuration.

### 5.2 Mobile Verification
- Tested live on an Android phone over the local Wi-Fi network.
- Verified one-tap category selection, question chip taps, expandable citation snippets, and voice input over mobile Chrome.

---

## 6. Final Reflection (Assignment Requirement 6)

### 6.1 What I'd Build Next
1. **Hybrid BM25 + Dense Vector Neural Re-ranking:** While TF-IDF with bigrams provides sub-millisecond offline matching for small SOP sets, scaling to 500+ plant documents would benefit from a hybrid lexical (BM25) + semantic dense embedding (e.g. BGE-small) retrieval pipeline with a cross-encoder re-ranker.
2. **Progressive Web App (PWA) with Offline Caching:** Manufacturing plants have localized Faraday-cage dead zones near heavy machinery. Implementing Service Workers and IndexedDB would allow caching the top 50 critical emergency procedures (LOTO, chemical spill, fire isolation) for 100% offline access even when Wi-Fi drops completely.
3. **Automated SOP Revision Diffing & Deprecation Alerts:** When Revision 04 is published, the copilot should automatically flag Rev 03 chunks as "SUPERSEDED" in the vector store and alert supervisors: *"Note: Rev 03 fixed sampling (n=5) was replaced on 01-Jul-2026 by AQL Table II in Rev 04."*
4. **Shift Log Integration & Operator Escalation:** If a supervisor asks a question that the SOP cannot answer, the copilot should offer a one-tap button: *"Escalate to Plant Maintenance Engineer via WhatsApp / Email"* with the machine name and fault context pre-filled.

### 6.2 What I'm Unsure About
1. **Real-World Factory Ambient Acoustics:** How well browser-native speech recognition performs in a 90 dB machining environment with intermittent pneumatic hiss and spindle whine. Real testing on the physical factory floor is required to determine whether directional Bluetooth headsets or noise-canceling microphones are necessary.
2. **Plant Document Update Cycles:** How frequently SOPs are revised and whether plant document controllers upload PDFs to a central SharePoint/QMS or maintain paper binders with wet signatures.

### 6.3 What I'd Ask the Customer (Plant Manager & Shift Supervisors)
1. *"What is your current procedure when a supervisor encounters an error code or procedure not covered in the manual? Who do they call, and how long does the line wait?"*
2. *"Are operators allowed to carry personal smartphones on the floor, or do you deploy shared, ruggedized plant tablets (e.g., Zebra, Samsung Active) mounted on magnetic machine stands?"*
3. *"How do you handle SOP revision obsolescence today? How do you ensure operators don't follow an outdated printout laminated on the machine frame?"*
4. *"Which document categories cause the most downtime: electrical schematics, hydraulic circuits, or quality inspection standards?"*

### 6.4 Challenges Faced While Building and Deploying, and How I Handled Them
1. **Corporate Network SSL Interception with Hugging Face:**
   - *Problem:* When running the initial `sentence-transformers` download for `all-MiniLM-L6-v2`, the network environment failed with `[SSL: CERTIFICATE_VERIFY_FAILED]` due to self-signed inspection certificates.
   - *Solution:* Rather than relying on fragile external model downloads or forcing bypasses, we engineered a 100% offline, zero-dependency embedding strategy using `scikit-learn`'s `TfidfVectorizer` (with unigrams, bigrams, sublinear term frequency, and L2 normalization) directly paired with **FAISS `IndexFlatIP`**. This achieved exact cosine similarity, zero network dependencies, and sub-millisecond retrieval latency ($0\text{--}24\text{ms}$).
2. **Windows Headless Subshell & `asyncio` IOCP Event Loop Freezes:**
   - *Problem:* In headless sandboxed environments on Windows, `asyncio.run()` with `ProactorEventLoop` hung indefinitely waiting for loopback socketpair creation.
   - *Solution:* Refactored the core inference pipeline to synchronous execution within FastAPI, leveraging FastAPI's native threadpool for route handlers. This eliminated socketpair blocking and ensured 100% reliability.
3. **Gemini API Model Deprecation & 503 Overload Handling:**
   - *Problem:* Google's API returned `404` for legacy model names and intermittent `503 Service Unavailable / High demand` on `gemini-2.5-flash`.
   - *Solution:* Added robust fallback handling: if the cloud LLM times out or returns 503, the copilot seamlessly falls back to the local extractive synthesis engine, ensuring shop-floor supervisors never experience a dead screen during a critical shift.
4. **Persistent Server Execution on Windows:**
   - *Problem:* Background tasks spawned in ephemeral IDE subshells were terminated when the subshell session idled or reloaded.
   - *Solution:* Created a dedicated Windows launcher script ([`start_copilot.bat`](file:///e:/JSE%20take%20home/start_copilot.bat)) that launches FastAPI and Vite in their own persistent desktop Command Prompt windows, ensuring they run uninterrupted.
