import os
import io
import base64
from PIL import Image
import pytesseract
from dotenv import load_dotenv
from llm import GROQ_VISION_MODEL

load_dotenv()

# Configure custom tesseract path if specified in .env or default locations
tesseract_cmd = os.getenv("TESSERACT_CMD")
if tesseract_cmd and os.path.exists(tesseract_cmd):
    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
else:
    # Common default paths on Windows
    win_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
    ]
    for p in win_paths:
        if os.path.exists(p):
            pytesseract.pytesseract.tesseract_cmd = p
            break

VIDEO_EXTENSIONS = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".flv", ".wmv"}

def is_video_file(filename: str) -> bool:
    """Check if the provided filename has a video extension."""
    if not filename:
        return False
    _, ext = os.path.splitext(filename.lower())
    return ext in VIDEO_EXTENSIONS

def _extract_via_groq_vision(image: Image.Image) -> str | None:
    """Fallback OCR using Groq Vision API if local Tesseract is not installed."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None

    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        
        completion = client.chat.completions.create(
            model=GROQ_VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Extract and transcribe all readable text, claim sentences, headers, and captions from this image verbatim. Do not add commentary or interpretations. Return ONLY the transcribed text."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{img_str}"
                            }
                        }
                    ]
                }
            ],
            temperature=0.0
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"[OCR] Groq vision fallback error: {e}")
        return None

def extract_text_from_image(file_or_bytes) -> dict:
    """
    Extracts text from an uploaded image or image bytes using OCR.
    Prioritizes local Tesseract; seamlessly falls back to Groq Vision if Tesseract is not installed.
    Returns:
        dict: {"success": bool, "text": str, "error": str | None}
    """
    try:
        if isinstance(file_or_bytes, bytes):
            image = Image.open(io.BytesIO(file_or_bytes))
        elif hasattr(file_or_bytes, "read"):
            bytes_data = file_or_bytes.read()
            if hasattr(file_or_bytes, "seek"):
                file_or_bytes.seek(0)
            image = Image.open(io.BytesIO(bytes_data))
        else:
            image = Image.open(file_or_bytes)

        if image.mode not in ("L", "RGB"):
            image = image.convert("RGB")

        # Try Tesseract OCR first
        try:
            extracted = pytesseract.image_to_string(image)
            cleaned_text = extracted.strip()
            if cleaned_text:
                return {"success": True, "text": cleaned_text, "error": None}
        except (pytesseract.TesseractNotFoundError, Exception):
            pass

        # Try Groq Vision fallback
        vision_text = _extract_via_groq_vision(image)
        if vision_text:
            return {"success": True, "text": vision_text, "error": None}

        return {
            "success": False,
            "text": "",
            "error": "No readable text could be found, or OCR engine is not configured. Please paste the claim as text."
        }
    except Exception as e:
        return {
            "success": False,
            "text": "",
            "error": f"Failed to process image: {str(e)}"
        }
