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

> 📖 **Looking for step-by-step instructions and where to put API keys?**  
> Check the dedicated [**`SETUP.md`**](SETUP.md) for full configuration details!

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
| **3** | **Who is allowed to remove a lockout lock from a machine?** | `True` | • **Normal Rule:** Only the **authorised person who applied the lock** may remove it upon completion of work.<br>• **Emergency / Absent Rule:** If the owner has left the plant, only the **Shift In-charge** may remove it with written authorization from the **Safety Officer** on Form `SF-12`. | `SAF-SOP-003_Lockout_Tagout_Procedure.pdf` (Page 1 & 2) |
| **4** | **What is the outer diameter tolerance for the BH-220 bearing housing?** | `True` | Nominal: **90.000 mm**, Tolerance: **+/- 0.050 mm** (Range: 89.950 to 90.050 mm). Inspection method: Digital caliper (Major characteristic). | `QC-SOP-014_Rev04_Incoming_Material_Inspection.pdf` (Page 2) |
| **5** | **How often should spindle runout be checked, and who does it?** | `True` | • **Frequency:** **Monthly** (limit: 0.005 mm max at chuck face using dial indicator).<br>• **Done by:** **Maintenance technician**. | `MNT-MAN-CNC-02_TX-200_Preventive_Maintenance.pdf` (Page 1) |

---

### Part B: The 5 Custom Questions (Including Out-of-Scope Refusal)

| # | Custom Question Type | Question | Answerable? | Safety Alert Triggered | Cited Source & Page |
|:-:|:---|:---|:---:|:---:|:---|
| **6** | **Safety (LOTO Isolation)** | *What are the mandatory Lockout/Tagout (LOTO) and PPE requirements before performing maintenance?* | `True` | ⚠️ *Always isolate machines as per Lockout/Tagout procedures before maintenance.* | `SAF-SOP-003_Lockout_Tagout_Procedure.pdf` (Page 1), `MNT-MAN-CNC-02` (Page 1) |
| **7** | **Maintenance (PM Routine)** | *What is the standard preventive maintenance and lubrication schedule for the shop-floor equipment?* | `True` | ⚠️ *Ensure hydraulic pressure is fully bled to zero before opening lines.* | `MNT-MAN-CNC-02_TX-200_Preventive_Maintenance.pdf` (Page 1) |
| **8** | **Quality (Revision Audit)** | *What are the quality inspection criteria and actions required when an out-of-tolerance defect is detected?* | `True` | *None* | `QC-SOP-014_Rev03` (Page 1), `QC-SOP-014_Rev04` (Page 1-2) |
| **9** | **Troubleshooting (Alarms)** | *What steps should a supervisor follow when an abnormal pressure, temperature, or machine fault occurs?* | `True` | ⚠️ *Verify Lockout/Tagout (LOTO) isolation before touching equipment.* | `MNT-MAN-CNC-02_TX-200_Preventive_Maintenance.pdf` (Page 2) |
| **10** | **Out-of-Scope (Refusal)** | *What is the corporate reimbursement policy for international business class flights and hotel stays?* | `False` | *None (Refused)* | **None (Refused - Out of Scope)** |

#### Out-of-Scope Refusal Verification:
> **Question:** *"What is the corporate reimbursement policy for international business class flights and hotel stays?"*  
> **Copilot Answer:**  
> *"This information is not found in the provided plant SOPs and manuals. Do not guess procedures—please contact Plant Engineering or your Shift Lead."*  
> **Sources:** `None (Refused)` | **Latency:** `0ms` (Rejected by cosine threshold guardrail $< 0.085$)

---

## 🐳 Docker Deployment (Bonus)

```bash
docker-compose up --build
```
- Backend is available on `http://0.0.0.0:8000`
- Frontend is available on `http://0.0.0.0:5173`
- `./data` is volume-mounted for instant vector store persistence.
