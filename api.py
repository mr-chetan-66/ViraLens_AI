import os
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

from utils import process_claim_text, process_claim_image
from ocr import is_video_file
from storage import init_db, save_check, list_checks, get_check

init_db()

app = FastAPI(
    title="ViraLens AI API",
    description="A Straight-Answer Fact Checker Backend (Text + Photo)",
    version="1.0.0"
)

# Enable CORS for React/Vite development server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TextClaimRequest(BaseModel):
    text: str
    groq_api_key: Optional[str] = None
    tavily_api_key: Optional[str] = None
    serper_api_key: Optional[str] = None

@app.get("/api/health")
def health_check():
    return {
        "status": "online",
        "has_groq_key": bool(os.getenv("GROQ_API_KEY")),
        "has_tavily_key": bool(os.getenv("TAVILY_API_KEY")),
        "has_serper_key": bool(os.getenv("SERPER_API_KEY")),
        "has_duckduckgo": True
    }

@app.post("/api/check-text")
def check_text_claim(req: TextClaimRequest):
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="Claim text cannot be empty.")

    # Apply temporary keys if provided by user in UI
    if req.groq_api_key:
        os.environ["GROQ_API_KEY"] = req.groq_api_key
    if req.tavily_api_key:
        os.environ["TAVILY_API_KEY"] = req.tavily_api_key
    if req.serper_api_key:
        os.environ["SERPER_API_KEY"] = req.serper_api_key

    result = process_claim_text(req.text)
    save_check(result, input_type="text")
    return result

@app.post("/api/check-image")
async def check_image_claim(
    file: UploadFile = File(...),
    groq_api_key: Optional[str] = Form(None),
    tavily_api_key: Optional[str] = Form(None),
    serper_api_key: Optional[str] = Form(None)
):
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded.")

    # Video rejection check
    if is_video_file(file.filename):
        return {
            "success": False,
            "error": "Video isn't supported — please paste the claim as text or a screenshot.",
            "reports": [],
            "skipped_opinions": []
        }

    if groq_api_key:
        os.environ["GROQ_API_KEY"] = groq_api_key
    if tavily_api_key:
        os.environ["TAVILY_API_KEY"] = tavily_api_key
    if serper_api_key:
        os.environ["SERPER_API_KEY"] = serper_api_key

    file_bytes = await file.read()
    result = process_claim_image(file_bytes, filename=file.filename)
    save_check(result, input_type="image")
    return result


@app.get("/api/history")
def history(limit: int = 20):
    return {"items": list_checks(limit=limit)}


@app.get("/api/history/{check_id}")
def history_item(check_id: int):
    item = get_check(check_id)
    if not item:
        raise HTTPException(status_code=404, detail="History item not found")
    return item

# Serve React production build if available
frontend_dist = os.path.join(os.path.dirname(__file__), "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        if full_path.startswith("api"):
            raise HTTPException(status_code=404, detail="API endpoint not found")
        index_file = os.path.join(frontend_dist, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        raise HTTPException(status_code=404, detail="Frontend build index.html not found")

if __name__ == "__main__":
    import uvicorn
    print("\n[ViraLens AI] Starting server at http://127.0.0.1:8000 ...")
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)
