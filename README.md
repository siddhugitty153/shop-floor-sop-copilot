# BiztelAI Shop-Floor SOP Copilot

> **Rugged, Grounded Manufacturing SOP Copilot for Shop-Floor Supervisors**  
> Strictly grounded RAG assistant built for mobile phones & tablets in precision manufacturing environments (Kaveri Precision Components, Hosur Plant).

---

## 📑 Assignment Deliverables Cross-Check

This submission fulfills all **6 requirements** specified in the BiztelAI Take-Home prompt:

| # | Requirement | Deliverable / Implementation | Status |
|:-:|:---|:---|:---:|
| **1** | **Understand the User** | Documented persona (Suresh Kumar, Hosur Plant), shift goals, and daily frustrations in [THINKING.md (Section 1)](THINKING.md#1-understand-the-user). | ✅ Complete |
| **2** | **User Journey & Failure Modes** | 5-step journey from floor trigger to verified action + 5 real failure modes in [THINKING.md (Section 2)](THINKING.md#2-user-journey-initial-draft). | ✅ Complete |
| **3** | **AI Challenge & Reflection** | Rigorous dialogue with a skeptical VP of Operations / Safety Auditor and reflection on changes in [THINKING.md (Section 3)](THINKING.md#3-ai-challenge-skeptical-product-manager--safety-auditor-critique). | ✅ Complete |
| **4** | **Build the Copilot & Improvements** | FastAPI + React RAG pipeline with strict page citations, zero-hallucination refusal, **Automated Safety/LOTO Banner**, **Inline Evidence Accordion**, and **Glove-Friendly Touch / Voice Input**. | ✅ Complete |
| **5** | **Deploy on Local Network** | Configured for `0.0.0.0` with dynamic LAN auto-discovery; tested live on phone via Wi-Fi (`http://192.168.1.3:5173`). | ✅ Complete |
| **6** | **Final Reflection (~1 page)** | In-depth reflection on future roadmap, shop-floor uncertainties, customer interview questions, and engineering challenges in [THINKING.md (Section 6)](THINKING.md#6-final-reflection-assignment-requirement-6). | ✅ Complete |
| **+** | **Sample & Custom Questions** | All 5 official Google Drive sample questions + 5 custom questions (including out-of-scope refusal) evaluated with exact answers below. | ✅ Complete |
| **Bonus** | **Local LLM / Multi-Tier** | Multi-tier LLM support (Gemini 2.5 Flash / LM Studio / Ollama / Offline Fallback). | ⭐ Complete |
| **Bonus** | **Docker & Compose** | Full Docker setup in `docker-compose.yml`. | ⭐ Complete |

---

## 📐 Architecture Diagram

```mermaid
flowchart TD
    subgraph Client["Mobile / Tablet Browser (LAN Wi-Fi)"]
        UI["React 18 + Tailwind UI"]
        MIC["Hands-Free Voice Input (Web Speech API)"]
        CHIPS["Glove-Friendly Question Chips (>=48px)"]
        ACC["Inline Evidence Accordion"]
    end

    subgraph Backend["FastAPI Server (0.0.0.0:8000)"]
        ROUTER["REST Endpoints (/health, /documents, /ask)"]
        GUARD["Similarity Threshold Guardrail (0.085)"]
        RETRIEVER["SOP Retriever (FAISS IndexFlatIP)"]
        
        subgraph Synthesis["Multi-Tier Generation"]
            TIER1["Tier 1: Google Gemini 2.5 Flash (Hosted)"]
            TIER2["Tier 2: LM Studio / Ollama (100% Local Neural Net)"]
            TIER3["Tier 3: Deterministic Offline Extractive Engine"]
        end
    end

    subgraph Data["Plant Documents & Vector Store"]
        PDFS["4 Plant PDFs (MNT, QC Rev03, QC Rev04, SAF)"]
        FAISS["FAISS Index + TF-IDF Vectorizer + metadata.json"]
    end

    UI -->|POST /ask| ROUTER
    MIC --> UI
    CHIPS --> UI
    ROUTER --> RETRIEVER
    RETRIEVER --> FAISS
    FAISS --> GUARD
    GUARD -->|In-Scope Chunks| Synthesis
    GUARD -->|Out-of-Scope (Score < 0.085)| ROUTER
    Synthesis --> ROUTER
    ROUTER --> UI
    UI --> ACC
```

---

## 🚀 Quick Start & Setup Guide

> 📖 **Full Setup Documentation:** See [**`SETUP.md`**](SETUP.md) for comprehensive network and offline details.

### 🔑 Where to Put Your LLM API Key

The copilot backend reads credentials from **`backend/.env`**.

1. Copy the provided template to create your `.env` file:
   ```bash
   # Windows:
   copy backend\.env.example backend\.env

   # macOS / Linux:
   cp backend/.env.example backend/.env
   ```
2. Open **`backend/.env`** and paste your API key:
   ```env
   LLM_PROVIDER=gemini
   GEMINI_API_KEY=AIzaSyYourGeminiApiKeyHere
   ```
   *(Get a free key in 30 seconds at [Google AI Studio](https://aistudio.google.com/app/apikey)).*

> [!TIP]
> **No API Key?** Set `LLM_PROVIDER=extractive` in `backend/.env` to run the copilot 100% offline using its built-in deterministic rule engine! You can also use local neural models like **LM Studio** (`LLM_PROVIDER=lmstudio`) or **Ollama** (`LLM_PROVIDER=ollama`).

---

### Option A: 1-Click Desktop Launcher (Windows)
Double-click **`start_copilot.bat`** in the project root. It opens two dedicated desktop command windows that will keep running persistently without being interrupted:
- Backend: `http://localhost:8000`
- Frontend: `http://localhost:5173`
- Phone access on Wi-Fi: `http://<your-lan-ip>:5173` (e.g. `http://192.168.1.3:5173`)

---

### Option B: Manual Command Line

#### 1. Ingest PDFs & Build FAISS Vector Store
```powershell
$env:PYTHONPATH = "backend"
backend\.venv\Scripts\python -m app.ingest
```

#### 2. Start the FastAPI Backend
```powershell
$env:PYTHONPATH = "backend"
backend\.venv\Scripts\uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 3. Start the Mobile-First Frontend
```powershell
cd frontend
npm run dev
```
- Laptop: `http://localhost:5173`
- Phone / Tablet: `http://192.168.1.3:5173` (Zero-config automatic discovery)

---

## 🧪 Comprehensive Evaluation Report

### Part A: The 5 Official Google Drive Sample Questions

| # | Question | Answerable? | Copilot Grounded Answer | Cited Source & Page |
|:-:|:---|:---:|:---|:---|
| **1** | **What is the recommended coolant concentration for the TX-200 CNC turning centre?** | `True` | **6 - 8 %** (measured via Refractometer reading x 1.0 factor). Topped up if low as per alarm `AL-412`. | `MNT-MAN-CNC-02_TX-200_Preventive_Maintenance.pdf` (Page 1) |
| **2** | **The machine is showing alarm AL-104. What does it mean and what should the operator do?** | `True` | **Meaning:** `Way lube oil level low`.<br>**Operator action:** Top up with ISO VG 68 oil to the MAX mark, then press RESET. Machine can continue after reset. | `MNT-MAN-CNC-02_TX-200_Preventive_Maintenance.pdf` (Page 2) |
| **3** | **Who is allowed to remove a lockout lock from a machine?** | `True` | • **Normal Rule:** Only the **authorised person who applied the lock** may remove it (`Nobody may remove another person's lock`).<br>• **Emergency / Absent Rule:** If the owner has left the plant and cannot be reached by phone, **both the Production Manager and the Safety Officer** must authorise removal after physical inspection, recorded on Form `SF-12`. | `SAF-SOP-003_Lockout_Tagout_Procedure.pdf` (Page 1 & 2) |
| **4** | **What is the outer diameter tolerance for the BH-220 bearing housing?** | `True` | Nominal: **90.000 mm**, Tolerance: **+/- 0.050 mm** (Range: 89.950 to 90.050 mm). Inspection method: Digital caliper (Major characteristic). | `QC-SOP-014_Rev04_Incoming_Material_Inspection.pdf` (Page 2) |
| **5** | **How often should spindle runout be checked, and who does it?** | `True` | • **Frequency:** **Monthly** (limit: 0.005 mm max at chuck face using dial indicator).<br>• **Done by:** **Maintenance technician**. | `MNT-MAN-CNC-02_TX-200_Preventive_Maintenance.pdf` (Page 1) |

---

### Part B: The 5 Custom Questions (Including Out-of-Scope Refusal)

As requested by BiztelAI, here are the 5 custom questions developed to test Safety, Maintenance, Quality revisions, Machine Troubleshooting, and Out-of-Scope refusal, along with the copilot's exact grounded responses:

| # | Question & Category | Answerable? | Copilot Grounded Answer | Cited Source & Page |
|:-:|:---|:---:|:---|:---|
| **6** | **Safety (LOTO Isolation):**<br>*What are the mandatory Lockout/Tagout (LOTO) and PPE requirements before performing maintenance?* | `True` | **⚠️ Alert:** *Mandatory Lockout/Tagout (LOTO) required before servicing.*<br>• De-energize main electrical breaker and apply personal lockout padlock with standardized red tag before opening any protective panel `[SAF-SOP-003, Page 1]`.<br>• Mandatory PPE: Safety glasses with side shields, cut-resistant nitrile gloves, and steel-toe boots `[MNT-MAN-CNC-02, Page 1]`.<br>• Bleed residual hydraulic pressure to zero before loosening any fluid coupling `[SAF-SOP-003, Page 2]`. | `SAF-SOP-003_Lockout_Tagout_Procedure.pdf` (Page 1 & 2)<br>`MNT-MAN-CNC-02` (Page 1) |
| **7** | **Maintenance (PM Schedule):**<br>*What is the standard preventive maintenance and lubrication schedule for the shop-floor equipment?* | `True` | • **Daily:** Check coolant concentration (maintain 6–8%) and way lube oil reservoir level (ISO VG 68) before shift start `[MNT-MAN-CNC-02, Page 1]`.<br>• **Weekly:** Clean chip conveyor tray, inspect pneumatic filter bowl for moisture accumulation `[MNT-MAN-CNC-02, Page 1]`.<br>• **Monthly:** Check spindle runout (0.005 mm max) performed by a maintenance technician `[MNT-MAN-CNC-02, Page 1]`. | `MNT-MAN-CNC-02_TX-200_Preventive_Maintenance.pdf` (Page 1) |
| **8** | **Quality (Revision Audit):**<br>*What are the quality inspection criteria and actions required when an out-of-tolerance defect is detected?* | `True` | • Under **Revision 04**, inspect lot according to **AQL 1.0 Table II** sampling plan and verify supplier Mill Test Certificate (MTC) `[QC-SOP-014_Rev04, Page 1]`.<br>• If a single dimensional non-conformance is identified (e.g. BH-220 OD outside 90.000 mm ± 0.050 mm), affix a red **HOLD / REJECT** physical tag and log the non-conformance into digital form **QF-07A** `[QC-SOP-014_Rev04, Page 2]`. | `QC-SOP-014_Rev04_Incoming_Material_Inspection.pdf` (Page 1 & 2) |
| **9** | **Troubleshooting (Fault Alarms):**<br>*What steps should a supervisor follow when an abnormal pressure, temperature, or machine fault occurs?* | `True` | • **Alarm AL-104 (Way lube level low):** Refill reservoir with ISO VG 68 oil to the MAX line and press RESET `[MNT-MAN-CNC-02, Page 2]`.<br>• **Alarm AL-210 (Hydraulic pressure fault):** Verify pressure gauge is between 30–35 bar; check for line leakage before restarting `[MNT-MAN-CNC-02, Page 2]`.<br>• **Alarm AL-412 (Coolant level low):** Add fresh water/soluble oil emulsion mixed to 6–8% concentration `[MNT-MAN-CNC-02, Page 2]`. | `MNT-MAN-CNC-02_TX-200_Preventive_Maintenance.pdf` (Page 2) |
| **10** | **Out-of-Scope (Mandatory Refusal):**<br>*What is the corporate reimbursement policy for international business class flights and hotel stays?* | `False` | **Strict Refusal (0ms Latency):**<br>*"This information is not found in the provided plant SOPs and manuals. Do not guess procedures—please contact Plant Engineering or your Shift Lead."* | **None (Refused - Out of Scope)**<br>Guardrail rejected (Cosine score $< 0.085$) |

---

## 🐳 Docker Deployment (Bonus)

```bash
docker-compose up --build
```
- Backend is available on `http://0.0.0.0:8000`
- Frontend is available on `http://0.0.0.0:5173`
- `./data` is volume-mounted for instant vector store persistence.
