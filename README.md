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

### 1. Backend Setup
```bash
# Navigate to project root
cd "e:/AIML/ViraLens AI"

# Install Python requirements
pip install -r requirements.txt
```

### 2. Configure API Keys
Copy `.env.example` to `.env`:
```bash
copy .env.example .env
```
Fill in your free keys:
- `GROQ_API_KEY`: Get a free key at [console.groq.com](https://console.groq.com)
- `TAVILY_API_KEY`: Get a free search key at [tavily.com](https://tavily.com)
*(Note: You can also enter or change keys directly in the web UI sidebar/drawer)*

### 3. Running the App

#### Option A: Unified Full-Stack Server (Recommended)
Since the production frontend is pre-built into `frontend/dist`, you can simply run:
```bash
python api.py
```
Then open your browser at **http://127.0.0.1:8000**!

#### Option B: Development Mode (with Vite Hot Reload)
1. In terminal 1 (Backend):
   ```bash
   python api.py
   ```
2. In terminal 2 (Frontend with live reload):
   ```bash
   cd frontend
   npm run dev
   ```
   Open **http://localhost:5173**.
