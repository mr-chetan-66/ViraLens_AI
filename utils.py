import os
from ocr import extract_text_from_image, is_video_file
from claim_extractor import extract_and_classify_claims
from search_engine import search_sources_for_claim
from evaluator import evaluate_sources_against_claim
from verdict import compute_verdict_and_confidence
from reporter import generate_plain_report

def process_single_claim(claim_text: str, progress_callback=None) -> dict:
    """
    Executes the fact-checking pipeline for a single factual claim:
    1. Search trusted sources (with Tier 1-4 ranking)
    2. Check & evaluate evidence
    3. Verify citations & compute verdict/confidence
    4. Generate plain-language report
    """
    if progress_callback:
        progress_callback("Searching trusted sources...")
    sources, attempts = search_sources_for_claim(claim_text)
    engines = sorted({s.get("engine") for s in sources if s.get("engine")})

    if progress_callback:
        progress_callback("Checking evidence...")
    evaluated = evaluate_sources_against_claim(claim_text, sources)

    if progress_callback:
        progress_callback("Verifying citations...")
    verdict_data = compute_verdict_and_confidence(claim_text, evaluated)

    if progress_callback:
        progress_callback("Preparing report...")
    report = generate_plain_report(claim_text, verdict_data)
    report["search_attempts"] = attempts
    report["search_engines"] = engines

    return report

def process_claim_text(text: str, progress_callback=None) -> dict:
    """
    Takes arbitrary text (WhatsApp forward, news paragraph, etc.),
    extracts factual claims vs opinions, verifies each factual claim,
    and returns a complete structured verdict result.
    """
    if not text or not text.strip():
        return {
            "success": False,
            "error": "No text provided to verify.",
            "reports": [],
            "skipped_opinions": []
        }

    if progress_callback:
        progress_callback("Reading claim...")

    if progress_callback:
        progress_callback("Extracting factual statements...")
    classified_statements = extract_and_classify_claims(text)

    factual_claims = [s for s in classified_statements if s.get("is_factual")]
    skipped_opinions = [s for s in classified_statements if not s.get("is_factual")]

    if not factual_claims and not skipped_opinions:
        # Fallback if no specific sentences parsed
        factual_claims = [{"text": text.strip(), "is_factual": True, "category": "Claim"}]

    reports = []
    for item in factual_claims:
        rep = process_single_claim(item["text"], progress_callback=progress_callback)
        reports.append(rep)

    result = {
        "success": True,
        "input_text": text,
        "reports": reports,
        "skipped_opinions": skipped_opinions,
        "total_claims_checked": len(reports),
        "total_opinions_skipped": len(skipped_opinions)
    }
    if not reports and skipped_opinions:
        result["notice"] = "No verifiable factual claims were found. Opinion-style statements were skipped."
    return result

def process_claim_image(uploaded_file, progress_callback=None, filename: str = "") -> dict:
    """
    Processes an uploaded image/screenshot or detects rejected video formats.
    Runs OCR and passes the extracted text into the fact-checking pipeline.
    """
    filename = filename or getattr(uploaded_file, "name", "")
    if is_video_file(filename):
        return {
            "success": False,
            "error": "Video isn't supported — please paste the claim as text or a screenshot.",
            "reports": [],
            "skipped_opinions": []
        }

    if progress_callback:
        progress_callback("Running OCR on image / screenshot...")

    ocr_result = extract_text_from_image(uploaded_file)
    if not ocr_result["success"]:
        return {
            "success": False,
            "error": ocr_result["error"],
            "reports": [],
            "skipped_opinions": []
        }

    extracted_text = ocr_result["text"]
    result = process_claim_text(extracted_text, progress_callback=progress_callback)
    result["ocr_extracted_text"] = extracted_text
    result["from_image"] = True
    result["authenticity_warning"] = (
        "A screenshot can be cropped, edited, or faked. We only checked the extracted text "
        "against independent sources — not whether the image itself is authentic."
    )
    return result
