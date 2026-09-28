# 🔍 ViraLens AI — A Straight-Answer Fact Checker (Text + Photo)

ViraLens AI is a fact-checking tool designed for people who don't want to blindly believe what they read online, but also don't have the time or inclination to dig through sources themselves.

Give it a claim — typed or in a screenshot/photo — and it returns a **clear verdict**, a **confidence score**, and the **exact trustworthy sources** behind that verdict.

> **Note:** This is NOT a chatbot. It does not chat, debate, or give opinions. It takes a claim in, and returns a verdict + evidence out.

---

## 🎨 Frontend & Design

- **Modern Architecture**: Fast React 18 + Vite frontend replacing Streamlit.
- **Minimal Theme**: Clean, distraction-free interface with glassmorphism (`backdrop-filter: blur`, luminous borders, subtle glows).
- **Green Shade Palette**: Deep emerald background (`#070b09`), mint/jade accents (`#10b981`, `#34d399`), and colored status indicators.

---

## 🚀 Core Features

- **Only Two Inputs**:
  1. **Text**: Paste any claim, sentence, forwarded message, or news post.
  2. **Photo / Screenshot**: Upload an image containing a claim (WhatsApp forward, news screenshot, poster, infographic, meme with text). Runs OCR with Groq Vision fallback.
  - *Video Rejection*: Displays a clear message: `"Video isn't supported — please paste the claim as text or a screenshot."`
- **Claim Extraction & Filtering**: Breaks paragraphs into individual sentences and classifies each:
  - Verifiable factual claims $\rightarrow$ sent to verification.
  - Opinions / predictions / rhetorical statements $\rightarrow$ skipped and labeled with reasons.
- **Strict 4-Tier Source Hierarchy**:
  - **Tier 1 (Primary / Official)**: Government sites (`.gov`, `.nic.in`, PIB), official filings, census, RBI, WHO.
  - **Tier 2 (Established Fact-Checkers)**: PIB Fact Check, AltNews, BOOM, Snopes, FactCheck.org, Full Fact, Reuters Fact Check, AP Fact Check.
  - **Tier 3 (Reputable News Wires / Outlets)**: Reuters, AP, BBC, PTI, The Hindu, Indian Express.
  - **Tier 4 (General / Unverified)**: Blogs, social media (used only for context, never for verdict).
- **Evidence Evaluation**: Verifies specific numbers, dates, and names.
- **Verdicts & Confidence**:
  - ✅ **Supported**
  - ❌ **Contradicted**
  - ⚠️ **Unclear**
  - Plus 0–100% confidence score and real, clickable source links.
- **Plain-Language Summary**: Built for non-experts ("WHAT WE FOUND" and "IN SIMPLE TERMS").

---

## 🛠️ Tech Stack

- **Frontend**: React 18, Vite, Lucide Icons, Glassmorphism CSS
- **Backend API**: FastAPI, Uvicorn
- **LLM**: Groq (Free-tier fast inference: LLaMA 3.3 70B / 8B / LLaMA 3.2 Vision)
- **Web Search**: Tavily API (Free tier)
- **OCR**: Tesseract OCR via `pytesseract` + Groq Vision fallback

---

## 📋 Installation & Running

### Prerequisites
- Python 3.10 or newer
- Node.js and npm
- API keys for Groq and Tavily (at minimum)
- Optional: Tesseract OCR for local image text extraction. Without it, image OCR uses Groq Vision.

Run the following commands in PowerShell from the project root.

### 1. Install Dependencies
```bash
# Create and activate a Python virtual environment
py -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install backend dependencies
python -m pip install -r requirements.txt

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### 2. Configure API Keys
Create your local `.env` file from the example:
```bash
Copy-Item .env.example .env
```
Add your keys to `.env`:
- `GROQ_API_KEY`: [console.groq.com](https://console.groq.com)
- `TAVILY_API_KEY`: [tavily.com](https://tavily.com)

The example also includes optional Serper and Gemini keys. If Tesseract is installed outside a standard Windows location, set `TESSERACT_CMD` in `.env` to its executable path. Keys can also be entered or changed in the web UI.

### 3. Running the App

#### Option A: Single server
Build the frontend, then start the backend (run both commands from the project root):
```bash
npm --prefix frontend run build
python api.py
```
Open **http://127.0.0.1:8000**.

#### Option B: Development mode with hot reload
Open two PowerShell terminals, both starting in the project root.

Terminal 1, start the backend:
   ```bash
   python api.py
   ```

Terminal 2, start the Vite frontend:
   ```bash
   cd frontend
   npm run dev
   ```
Open **http://localhost:5173**.
