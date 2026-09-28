"""
End-to-End Pipeline Sanity Checks for ViraLens AI
"""
import sys
import io

# Ensure UTF-8 output handling on Windows consoles
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from ocr import is_video_file
from claim_extractor import extract_and_classify_claims
from search_engine import classify_source_tier
from verdict import compute_verdict_and_confidence
from reporter import generate_plain_report
import os

def run_tests():
    print("=" * 60)
    print("Running ViraLens AI Unit & Pipeline Sanity Tests")
    print("=" * 60)

    # 1. Video detection test
    print("\n[Test 1] Video Detection Check:")
    assert is_video_file("whatsapp_forward.mp4") == True
    assert is_video_file("reel.mov") == True
    assert is_video_file("screenshot.png") == False
    assert is_video_file("poster.jpeg") == False
    print("[PASS] Video detection passed.")

    # 2. Claim Extraction test
    print("\n[Test 2] Claim Extraction & Classification Check:")
    sample_text = "The government gave every student ₹50,000 last month. This is the best scheme ever."
    extracted = extract_and_classify_claims(sample_text)
    print(f"Extracted {len(extracted)} statements from sample text:")
    for item in extracted:
        status = "Factual" if item.get("is_factual") else "Opinion"
        print(f" - [{status}] {item.get('text')} -> {item.get('reason')}")
    
    assert any(s.get("is_factual") for s in extracted), "Should have extracted at least 1 factual statement"
    assert any(not s.get("is_factual") for s in extracted), "Should have classified opinion statement"
    print("[PASS] Claim extraction passed.")

    # 3. Source Tier Ranking check with news type classification
    print("\n[Test 3] Source Tier & News Type Classification Check:")
    t1_tier, t1_name, t1_news_type = classify_source_tier("https://www.education.gov.in/schemes")
    t2_tier, t2_name, t2_news_type = classify_source_tier("https://www.altnews.in/viral-claim-check")
    t3_tier, t3_name, t3_news_type = classify_source_tier("https://www.reuters.com/world/india/article-123")
    t4_tier, t4_name, t4_news_type = classify_source_tier("https://myrandomblog.wordpress.com/post")
    t5_tier, t5_name, t5_news_type = classify_source_tier("https://www.insider.com/tech-news")

    assert t1_tier == 1, f"Expected Tier 1, got {t1_tier}"
    assert t2_tier == 2, f"Expected Tier 2, got {t2_tier}"
    assert t3_tier == 3, f"Expected Tier 3, got {t3_tier}"
    assert t4_tier == 4, f"Expected Tier 4, got {t4_tier}"
    assert t5_tier == 3, f"Expected Tier 3, got {t5_tier}"
    assert t1_news_type == "Confirmed Official", f"Expected 'Confirmed Official', got {t1_news_type}"
    assert t5_news_type == "Rumor/Insider", f"Expected 'Rumor/Insider', got {t5_news_type}"
    
    print(f"[PASS] Tier 1: {t1_name} ({t1_news_type})")
    print(f"[PASS] Tier 2: {t2_name} ({t2_news_type})")
    print(f"[PASS] Tier 3: {t3_name} ({t3_news_type})")
    print(f"[PASS] Tier 4: {t4_name} ({t4_news_type})")
    print(f"[PASS] Tier 3 (Rumor): {t5_name} ({t5_news_type})")
    print("[PASS] Source tier and news type classification passed.")

    # 4. Verdict & Scoring check with enhanced metadata
    print("\n[Test 4] Enhanced Verdict & Confidence Calculation Check:")
    mock_contradicting_evidence = [
        {
            "url": "https://pib.gov.in/PressReleasePage.aspx?PRID=123",
            "title": "PIB Press Release: Clarification on Student Scholarship",
            "tier": 1,
            "tier_name": "Tier 1 — Primary / Official",
            "news_type": "Confirmed Official",
            "stance": "Contradicting",
            "key_finding": "Official scholarship grants ₹15,000 per student, not ₹50,000.",
            "matches_specifics": True,
            "credibility_weight": "High"
        },
        {
            "url": "https://www.altnews.in/fact-check-student-grant",
            "title": "AltNews Fact Check",
            "tier": 2,
            "tier_name": "Tier 2 — Established Fact-Checker",
            "news_type": "Confirmed Official",
            "stance": "Contradicting",
            "key_finding": "Fake viral claim about ₹50,000 grant debunked.",
            "matches_specifics": True,
            "credibility_weight": "High"
        }
    ]
    verdict_data = compute_verdict_and_confidence(
        "The government gave every student ₹50,000 last month.",
        mock_contradicting_evidence
    )
    assert verdict_data["verdict"] == "Contradicted"
    assert verdict_data["confidence"] >= 80
    assert "verdict_sub_type" in verdict_data
    assert "source_breakdown" in verdict_data
    print(f"[PASS] Calculated Verdict: {verdict_data['verdict_label']} ({verdict_data['verdict_sub_type']}), Confidence: {verdict_data['confidence']}%")
    print(f"[PASS] Source Breakdown: {verdict_data['source_breakdown']}")
    
    # Test rumor-based claims (should be Unclear with low confidence)
    print("\n[Test 4b] Rumor-Based Claims Detection Check:")
    mock_rumor_evidence = [
        {
            "url": "https://www.facebook.com/post/123",
            "title": "Facebook Post About Rumor",
            "tier": 4,
            "tier_name": "Tier 4 — General / Unverified",
            "news_type": "Unverified",
            "stance": "Supporting",
            "key_finding": "Source mentions confirmed figures matching the claim.",
            "matches_specifics": True,
            "credibility_weight": "Low"
        },
        {
            "url": "https://www.instagram.com/p/123",
            "title": "Instagram Post About Rumor",
            "tier": 4,
            "tier_name": "Tier 4 — General / Unverified",
            "news_type": "Unverified",
            "stance": "Supporting",
            "key_finding": "Source mentions confirmed figures matching the claim.",
            "matches_specifics": True,
            "credibility_weight": "Low"
        }
    ]
    rumor_verdict = compute_verdict_and_confidence(
        "Celebrity will join new team in 2027",
        mock_rumor_evidence
    )
    assert rumor_verdict["verdict"] == "Unclear", f"Expected Unclear for rumor-only evidence, got {rumor_verdict['verdict']}"
    assert rumor_verdict["verdict_sub_type"] == "Rumor-Based Claims", f"Expected 'Rumor-Based Claims', got {rumor_verdict['verdict_sub_type']}"
    assert rumor_verdict["confidence"] <= 20, f"Expected low confidence for rumors, got {rumor_verdict['confidence']}"
    print(f"[PASS] Rumor Verdict: {rumor_verdict['verdict_label']} ({rumor_verdict['verdict_sub_type']}), Confidence: {rumor_verdict['confidence']}%")
    print("[PASS] Enhanced verdict & confidence calculation passed.")

    # 5. Plain Report Check
    print("\n[Test 5] Plain-Language Report Generation Check:")
    report = generate_plain_report(
        "The government gave every student ₹50,000 last month.",
        verdict_data
    )
    assert "in_simple_terms" in report
    assert "what_we_found" in report
    assert report.get("verdict_sub_type") == verdict_data.get("verdict_sub_type")
    assert report.get("source_breakdown") == verdict_data.get("source_breakdown")
    print(f"[PASS] In Simple Terms: \"{report['in_simple_terms']}\"")
    print("[PASS] Report generation passed.")

    print("\n[Test 6] Local history store:")
    from storage import init_db, save_check, list_checks, get_check
    init_db()
    sample = {
        "success": True,
        "input_text": "Sample stored claim for history.",
        "reports": [{"verdict": "Unclear", "confidence": 25, "claim": "Sample stored claim for history."}],
        "skipped_opinions": []
    }
    row_id = save_check(sample, input_type="text")
    assert row_id, "History row should be saved"
    items = list_checks(limit=5)
    assert any(i["id"] == row_id for i in items)
    loaded = get_check(row_id)
    assert loaded["input_text"] == sample["input_text"]
    print("[PASS] SQLite history save/load passed.")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
