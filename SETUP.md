# BiztelAI Shop-Floor SOP Copilot — Setup & Quickstart Guide (`SETUP.md`)

This guide walks you through setting up, configuring API keys, and launching the **BiztelAI Shop-Floor SOP Copilot** on your laptop and local network (Wi-Fi).

---

## 🔑 1. API Key Configuration (Where to put your keys)

The copilot backend reads its configuration from the **`backend/.env`** file.

### Step 1.1: Create your `backend/.env` file
A template is provided at [`backend/.env.example`](backend/.env.example). If `backend/.env` does not exist yet, copy the template:

**Windows (Command Prompt):**
```cmd
copy backend\.env.example backend\.env
```

**macOS / Linux:**
```bash
cp backend/.env.example backend/.env
```

### Step 1.2: Add your API Key into `backend/.env`
Open `backend/.env` in any text editor (Notepad, VS Code, etc.). 

By default, the copilot uses **Google Gemini 2.5 Flash** because it is extremely fast and has a free API tier:

```env
# -------------------------------------------------------------
# LLM Provider Configuration
# -------------------------------------------------------------
LLM_PROVIDER=gemini

# Paste your Gemini API key from https://aistudio.google.com/app/apikey
GEMINI_API_KEY=AIzaSyYourActualKeyGoesHere

# -------------------------------------------------------------
# Retrieval & Grounding Guardrails
# -------------------------------------------------------------
EMBEDDING_MODEL=tfidf-vectorizer
SIMILARITY_THRESHOLD=0.085
TOP_K=4
```

> [!TIP]
> **No API Key? No problem!**  
> If you don't have a Gemini API key or want to run 100% offline without external internet calls, set:
> ```env
> LLM_PROVIDER=extractive
> ```
> The system will automatically use its built-in deterministic extractive synthesis engine.
> 
> You can also run **LM Studio** (`LLM_PROVIDER=lmstudio`) or **Ollama** (`LLM_PROVIDER=ollama`) if you prefer fully offline neural generation.

---

## ⚡ 2. Quickstart: 1-Click Desktop Launcher (Windows)

The simplest way to run both the FastAPI backend and React frontend:

1. Double-click **`start_copilot.bat`** in the project root directory.
2. Two dedicated command windows will open:
   - **Backend API:** `http://localhost:8000` (API Docs: `http://localhost:8000/docs`)
   - **Frontend UI:** `http://localhost:5173`
3. Leave both command windows running.

---

## 🛠️ 3. Manual Step-by-Step Setup

If you prefer to run services manually or are on macOS/Linux:

### Prerequisites:
- **Python 3.10, 3.11, or 3.12**
- **Node.js (v18+) & npm**

### 3.1 Backend Setup
```bash
# 1. Navigate to backend
cd backend

# 2. Create virtual environment
python -m venv .venv

# 3. Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Build/Verify the FAISS vector index from PDFs (data/pdfs/)
python -m app.ingest

# 6. Start the FastAPI server on 0.0.0.0:8000
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3.2 Frontend Setup
In a separate terminal:
```bash
# 1. Navigate to frontend
cd frontend

# 2. Install dependencies
npm install

# 3. Start Vite dev server on 0.0.0.0:5173
npm run dev -- --host 0.0.0.0 --port 5173
```

---

## 📱 4. Opening on Mobile / Tablet over Local Network (Wi-Fi)

To test the copilot from a mobile phone or shop-floor tablet (Requirement 5):

1. Connect your phone to the **same Wi-Fi network** as your laptop.
2. Find your laptop's local IPv4 address:
   - **Windows:** Run `ipconfig` (look for `IPv4 Address` under your Wi-Fi adapter, e.g. `192.168.1.3`).
   - **macOS / Linux:** Run `ifconfig` or `ip a`.
3. Open your mobile browser (Chrome or Safari) and navigate to:
   ```text
   http://<YOUR-LAPTOP-IP>:5173
   ```
   *(For example: `http://192.168.1.3:5173`)*

> [!IMPORTANT]
> **Mobile Browser Troubleshooting:**
> 1. Make sure to type **`http://`** and NOT `https://`.
> 2. On Windows, make sure your Wi-Fi network profile is set to **Private network** in Windows Settings (Windows blocks incoming phone connections on "Public" networks).
> 3. Temporarily disable Mobile Data (4G/5G) on your phone if it defaults to cellular instead of local Wi-Fi.

---

## 🧪 5. Testing the Sample & Custom Questions

Once loaded, you can test by:
1. Tapping any of the **pre-loaded question chips** at the top of the interface.
2. Tapping the **Microphone** button for hands-free voice dictation.
3. Typing any custom question.

### The 5 Official Sample Questions & Expected Answers:
1. **Coolant concentration for TX-200:** Returns `6 - 8 %` (`MNT-MAN-CNC-02`, Page 1).
2. **Alarm AL-104:** Returns `Way lube oil level low; top up ISO VG 68 to MAX and press RESET` (`MNT-MAN-CNC-02`, Page 2).
3. **Lockout lock removal:** Returns `Authorised person who applied it; or Shift In-charge with Safety Officer SF-12 authorization` (`SAF-SOP-003`, Page 1 & 2).
4. **BH-220 Outer diameter tolerance:** Returns `90.000 mm +/- 0.050 mm` (`QC-SOP-014_Rev04`, Page 2).
5. **Spindle runout frequency & owner:** Returns `Monthly, 0.005 mm max by Maintenance technician` (`MNT-MAN-CNC-02`, Page 1).

### Out-of-Scope Test (Zero-Hallucination Refusal):
- Try asking: *"What is the reimbursement policy for international business class flights?"*
- **Result:** Copilot immediately refuses: *"This information is not found in the provided plant SOPs and manuals. Do not guess procedures—please contact Plant Engineering or your Shift Lead."*

---

## 🐳 6. Docker Deployment (Optional Bonus)

If you have Docker and Docker Compose installed:
```bash
docker-compose up --build
```
Both backend (`:8000`) and frontend (`:5173`) will launch automatically in containers with `./data` volume-mounted.
