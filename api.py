import os
from threading import Event, Lock
from uuid import uuid4
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from utils import process_claim_text, process_claim_image
from ocr import is_video_file
from cancellation import ProcessingCancelled

active_checks: dict[str, Event] = {}
active_checks_lock = Lock()


def register_check(request_id: str | None) -> tuple[str, Event]:
    request_id = request_id or uuid4().hex
    with active_checks_lock:
        if request_id in active_checks:
            raise HTTPException(status_code=409, detail="A check with this request ID is already active.")
        cancel_event = Event()
        active_checks[request_id] = cancel_event
    return request_id, cancel_event


def unregister_check(request_id: str, cancel_event: Event) -> None:
    with active_checks_lock:
        if active_checks.get(request_id) is cancel_event:
            active_checks.pop(request_id, None)

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
    request_id: str | None = None

@app.get("/api/health")
def health_check():
    return {
        "status": "online",
        "has_duckduckgo": True
    }

@app.post("/api/check-text")
def check_text_claim(req: TextClaimRequest):
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="Claim text cannot be empty.")

    request_id, cancel_event = register_check(req.request_id)
    try:
        return process_claim_text(req.text, cancel_event=cancel_event)
    except ProcessingCancelled as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    finally:
        unregister_check(request_id, cancel_event)


@app.post("/api/check/cancel/{request_id}")
def cancel_check(request_id: str):
    with active_checks_lock:
        cancel_event = active_checks.get(request_id)
    if cancel_event is None:
        return {"cancelled": False}
    cancel_event.set()
    return {"cancelled": True}

@app.post("/api/check-image")
async def check_image_claim(
    file: UploadFile = File(...),
    request_id: str | None = Form(None),
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

    file_bytes = await file.read()
    request_id, cancel_event = register_check(request_id)
    try:
        return process_claim_image(file_bytes, filename=file.filename, cancel_event=cancel_event)
    except ProcessingCancelled as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    finally:
        unregister_check(request_id, cancel_event)

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
