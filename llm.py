import os
from dotenv import load_dotenv

load_dotenv()

try:
    from groq import Groq
except ImportError:
    Groq = None

# Groq retired llama-3.3-70b-versatile (developer) and Llama 3.2 vision in 2026.
# Production text: openai/gpt-oss-20b (fast) or openai/gpt-oss-120b (higher quality).
# Preview vision: qwen/qwen3.8-27b (image + text).
GROQ_TEXT_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
GROQ_VISION_MODEL = os.getenv("GROQ_VISION_MODEL", "qwen/qwen3.8-27b")
GROQ_TIMEOUT_SECONDS = 8.0


def get_groq_client():
    api_key = os.getenv("GROQ_API_KEY")
    if api_key and Groq:
        return Groq(api_key=api_key, timeout=GROQ_TIMEOUT_SECONDS, max_retries=0)
    return None
