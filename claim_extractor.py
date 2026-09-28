import re
import json
from dotenv import load_dotenv

load_dotenv()

# We can use Groq client if installed and configured
from llm import get_groq_client, GROQ_TEXT_MODEL

EXTRACTION_SYSTEM_PROMPT = """You are an expert fact-checking claim analyzer with advanced nuance detection.
Your job is to break the given input text into individual distinct statements and classify each sentence/statement into one of two categories:
1. "factual": A verifiable factual claim (e.g. contains specific actions, events, numbers, dates, statistics, quotes, government policies, scientific claims that can be proven true or false).
2. "opinion": An opinion, prediction, rhetorical statement, personal belief, or satire that cannot be verified against objective facts.

Advanced Detection Rules:
- Distinguish between specific factual claims vs. general statements or opinions
- Identify claims that contain verifiable data points (numbers, dates, names, locations)
- Be careful with statements that are partially factual but primarily opinion-based
- Look for speculative language ("might", "could", "possibly", "allegedly") that makes something unverified
- Identify rhetorical questions, sarcasm, and satire
- Separate compound claims into individual verifiable components

Rules:
- Do not combine multiple factual claims into one. Break them down.
- Be precise about what makes something factual vs. opinion
- Output ONLY valid JSON in this exact structure:
[
  {
    "text": "Exact or cleaned statement from the input",
    "is_factual": true,
    "category": "Verifiable factual claim",
    "reason": "Brief explanation why it is factual"
  },
  {
    "text": "Exact or cleaned statement from the input",
    "is_factual": false,
    "category": "Opinion / Rhetorical / Satire",
    "reason": "Brief explanation why it is an opinion or non-factual and skipped"
  }
]
No markdown wrapping, no commentary outside the JSON list."""

def fallback_extract_claims(text: str) -> list:
    """
    Fallback deterministic splitter when LLM API key is not configured.
    """
    sentences = [s.strip() for s in re.split(r'(?<=[.!?\n])\s+', text) if s.strip()]
    if not sentences:
        if text.strip():
            sentences = [text.strip()]
        else:
            return []

    opinion_keywords = ["best", "worst", "great", "terrible", "amazing", "horrible", "i think", "i believe", "should", "must", "love", "hate", "pathetic", "awesome"]
    results = []
    for s in sentences:
        lower = s.lower()
        has_opinion = any(re.search(r'\b' + re.escape(w) + r'\b', lower) for w in opinion_keywords)
        has_numbers_or_date = bool(re.search(r'\d+', s))
        
        if has_opinion and not has_numbers_or_date:
            results.append({
                "text": s,
                "is_factual": False,
                "category": "Opinion / Subjective statement",
                "reason": "Contains subjective value judgment or opinion words."
            })
        else:
            results.append({
                "text": s,
                "is_factual": True,
                "category": "Verifiable factual claim",
                "reason": "Presents an objective assertion regarding people, events, or numbers."
            })
    return results

def extract_and_classify_claims(text: str) -> list:
    """
    Extracts statements from text and classifies each as factual or opinion.
    Returns:
        list of dicts: [{"text": str, "is_factual": bool, "category": str, "reason": str}]
    """
    cleaned_input = text.strip()
    if not cleaned_input:
        return []

    client = get_groq_client()
    if not client:
        return fallback_extract_claims(cleaned_input)

    try:
        completion = client.chat.completions.create(
            model=GROQ_TEXT_MODEL,
            messages=[
                {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": cleaned_input}
            ],
            temperature=0.0
        )
        content = completion.choices[0].message.content.strip()
        # Clean any accidental markdown code fence
        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?\n?", "", content)
            content = re.sub(r"\n?```$", "", content)
        
        parsed = json.loads(content)
        if isinstance(parsed, list):
            return parsed
        elif isinstance(parsed, dict) and "claims" in parsed and isinstance(parsed["claims"], list):
            return parsed["claims"]
        else:
            return fallback_extract_claims(cleaned_input)
    except Exception as e:
        # Fall back gracefully on error
        return fallback_extract_claims(cleaned_input)
