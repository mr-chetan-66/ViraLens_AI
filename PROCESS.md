# ViraLens AI — Development Process Record & Chunk Tracking

> **Goal:** Build ViraLens AI — a straight-answer fact checker for text and photos/screenshots. No chat, no debates, no opinions. Input: Claim (Text or Photo). Output: Verdict + Confidence Score + Trustworthy Clickable Sources + Plain-Language Summary.

---

## 📌 Current Project State: **FULLY READY & ENHANCED (REACT + FASTAPI)** ✅
- **Architecture**: Modern React 18 + Vite Frontend with FastAPI Backend (Streamlit removed for performance and customized design).
- **Design System**: Minimal theme, Glassmorphism panels, Emerald green color palette (`#070b09`, `#10b981`, `#34d399`), Lucide iconography.
- **Python Dependencies**: Installed (`fastapi`, `uvicorn`, `python-multipart`, `pytesseract`, `pillow`, `groq`, `tavily-python`, `beautifulsoup4`, `tldextract`, `python-dotenv`, `requests`).
- **Node Dependencies**: Installed (`react`, `react-dom`, `lucide-react`, `vite`). Production build compiled successfully into `frontend/dist/`.
- **Sanity Test Suite**: Passed 100% (`python test_pipeline.py`).
- **Unified Launch Command**: `python api.py` (serves both API and React frontend at `http://127.0.0.1:8000`).

---

## 🚀 **MAJOR ENHANCEMENTS (Phase 3 - Advanced Fact-Checking Engine)**

### **Multi-API Search Architecture**
- **Dual Search Engines**: Integrated both Tavily and Serper (Google Search) APIs for comprehensive source coverage
- **Smart Fallback System**: Automatically switches between search APIs if one fails or returns insufficient results
- **Enhanced Query Generation**: Multiple search query strategies (direct claim, fact-check, official verification, debunking)
- **Advanced Source Ranking**: Intelligent scoring system considering tier, news type, and relevance

### **News Type Classification System**
- **Source Categorization**: Classifies sources into 4 credibility types:
  - `Confirmed Official`: Government sites, official fact-checkers (highest trust)
  - `Confirmed News`: Established news wires and reputable outlets (high trust)
  - `Rumor/Insider`: Insider reports, tech blogs (medium trust, needs corroboration)
  - `Unverified`: General blogs, social posts (low trust)
- **Smart Verdict Logic**: Enhanced verdict system that prioritizes official sources over rumors
- **Source Breakdown Display**: UI shows credibility breakdown of sources used

### **Advanced Evaluation & Verdict System**
- **Nuanced Verdict Categories**: 
  - `Officially Debunked` / `Officially Confirmed` (when official sources contradict/confirm)
  - `Fact-Checked as True/False` (when established fact-checkers verify)
  - `Unverified Claims` (when only rumors support a claim)
  - `Conflicting Evidence` (when credible sources disagree)
- **Enhanced Confidence Scoring**: Factors in source credibility, corroboration, and specificity
- **Credibility Weighting**: Evidence from official sources carries more weight than rumors

### **Improved LLM Prompts**
- **Advanced Claim Extraction**: Better detection of factual vs. opinion statements with nuance awareness
- **Enhanced Evidence Evaluation**: Prompts now consider source credibility and detect partial truths
- **Credibility-Aware Reporting**: Summaries emphasize source types and distinguish between official vs. unofficial sources

### **API Configuration**
- **Optional Serper API**: Added support for Serper Search API as secondary search engine
- **Environment Variables**: Updated `.env.example` to include `SERPER_API_KEY`
- **Frontend Integration**: Added Serper API key input in UI configuration drawer

---

## 📊 Development Progress Tracker

| Chunk # | Chunk Name & Description | Status | Target Files |
| :--- | :--- | :---: | :--- |
| **Chunk 1** | **Project Setup & Environment**: Dependencies (`requirements.txt`), project configuration, environment variable handling (`.env.example`, `.env`). | **DONE** | [`requirements.txt`](file:///e:/AIML/ViraLens%20AI/requirements.txt), [`.env.example`](file:///e:/AIML/ViraLens%20AI/.env.example), [`README.md`](file:///e:/AIML/ViraLens%20AI/README.md) |
| **Chunk 2** | **Architecture & OCR Pipeline**: Screenshot/photo text extraction using OCR (Tesseract + Groq Vision fallback), video rejection logic. | **DONE** | [`ocr.py`](file:///e:/AIML/ViraLens%20AI/ocr.py) |
| **Chunk 3** | **Claim Extraction & Filtering**: Split text into sentences, classify each as Verifiable Factual Claim vs Opinion / Prediction / Rhetorical / Satire. | **DONE** | [`claim_extractor.py`](file:///e:/AIML/ViraLens%20AI/claim_extractor.py) |
| **Chunk 4** | **Search Engine & Source Tier Ranking**: Query generation, Tavily search, strict Tier 1–4 domain ranking and filtering (max 2 search attempts). | **DONE** | [`search_engine.py`](file:///e:/AIML/ViraLens%20AI/search_engine.py) |
| **Chunk 5** | **Evidence Evaluation & Verification**: Match specific numbers/dates/names against claim. Classify evidence as Supporting / Contradicting / Not directly relevant. | **DONE** | [`evaluator.py`](file:///e:/AIML/ViraLens%20AI/evaluator.py) |
| **Chunk 6** | **Verdict, Confidence Score & Citation Checker**: Calculate Supported / Contradicted / Unclear verdict, calculate 0–100% confidence score, ensure real clickable citations. | **DONE** | [`verdict.py`](file:///e:/AIML/ViraLens%20AI/verdict.py) |
| **Chunk 7** | **Final Report Generator & Plain-Language Summary**: Generate non-expert plain English report (Claim, Verdict, Confidence, What We Found, In Simple Terms). | **DONE** | [`reporter.py`](file:///e:/AIML/ViraLens%20AI/reporter.py) |
| **Chunk 8** | **Backend API (FastAPI)**: REST endpoints for claim text and photo/screenshot verification with CORS and static hosting. | **DONE** | [`api.py`](file:///e:/AIML/ViraLens%20AI/api.py) |
| **Chunk 9** | **Modern Glassmorphic React Frontend**: Minimal UI, green shade palette, live progress stepper, tabs, video rejection, verdict cards, expandable verified sources. | **DONE** | [`frontend/`](file:///e:/AIML/ViraLens%20AI/frontend/) |
| **Chunk 10** | **Integration Testing & Edge Case Hardening**: Automated pipeline tests, build verification, and graceful fallbacks. | **DONE** | [`test_pipeline.py`](file:///e:/AIML/ViraLens%20AI/test_pipeline.py) |

---

## 🔍 Detailed Breakdown of Phase 2 (Frontend Modernization)

### Chunk 8: FastAPI Backend ([`api.py`](file:///e:/AIML/ViraLens%20AI/api.py))
- Replaces Streamlit process execution with high-throughput asynchronous REST API endpoints:
  - `GET /api/health` — Service health and key detection.
  - `POST /api/check-text` — Text claim analysis.
  - `POST /api/check-image` — Multipart upload analysis with OCR.
- Auto-serves compiled React frontend from `frontend/dist` at the root path (`/`).

### Chunk 9: React 18 + Vite Minimal Glassmorphic UI ([`frontend/`](file:///e:/AIML/ViraLens%20AI/frontend/))
- **Theme & Palette**:
  - Deep obsidian-emerald base: `#070b09`
  - Glass panels: `rgba(14, 26, 20, 0.65)` with `backdrop-filter: blur(16px)` and subtle emerald borders (`rgba(52, 211, 153, 0.18)`)
  - Accent Green: `#10b981`, `#34d399`, and `#059669`
- **Features**:
  - Two input tabs: **Paste Text** or **Upload Photo/Screenshot**
  - Instant client-side video file rejection
  - 6-step live progress stepper
  - Verdict badge with status icons (✅ Supported, ❌ Contradicted, ⚠️ Unclear)
  - Animated confidence progress bar
  - **WHAT WE FOUND** bulleted breakdown
  - **IN SIMPLE TERMS** highlight box
  - Expandable **🔗 See Sources** with tier badges, stance, and clickable URLs
  - Skipped non-factual statements panel with category explanations
  - Optional in-browser API key drawer
