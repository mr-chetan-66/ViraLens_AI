import re
import json
from dotenv import load_dotenv

load_dotenv()

from llm import get_groq_client, GROQ_TEXT_MODEL

EVALUATION_SYSTEM_PROMPT = """You are a rigorous, objective fact-checking evidence evaluator with advanced nuance detection.
Your role is to evaluate whether retrieved source snippets support, contradict, or are not directly relevant to a specific factual claim.

CRITICAL RULES:
1. Exact Match Requirement: Check if the evidence directly addresses the specific numbers, dates, amounts, and names in the claim — not just the general topic.
   - Example: Claim says "₹50,000", evidence says "₹15,000" -> CONTRADICTING (the number is wrong).
   - Example: Claim says "Government banned X", evidence says "Debate continues on X" -> NOT DIRECTLY RELEVANT or CONTRADICTING.
2. Source Credibility Awareness: Consider the source type when evaluating evidence strength:
   - "Confirmed Official" sources (government, official fact-checkers) carry highest weight
   - "Confirmed News" sources (established news wires) carry high weight
   - "Rumor/Insider" sources should be treated as less authoritative, need corroboration
   - "Unverified" sources carry minimal weight
3. Evidence Stance Categories (must choose one):
   - "Supporting": Explicitly verifies that the claim's facts, figures, and details are true.
   - "Contradicting": Explicitly shows the claim is false, fabricated, exaggerated, or specifies contrary facts/numbers.
   - "Not directly relevant": Mentions the topic or keywords but does not confirm or refute the specific assertion.
4. Nuance Detection: Look for partial truths, context that changes meaning, or misleading framing:
   - If a claim is technically true but misleading, classify as "Contradicting" with explanation
   - If evidence provides important context missing from claim, note this in key_finding
5. Be completely objective and strict.
6. Output ONLY valid JSON with this structure:
[
  {
    "source_index": 0,
    "stance": "Supporting" | "Contradicting" | "Not directly relevant",
    "key_finding": "1-2 sentences stating the specific fact discovered from this source",
    "matches_specifics": true | false,
    "credibility_weight": "High" | "Medium" | "Low"
  }
]"""

def evaluate_evidence_fallback(claim: str, sources: list) -> list:
    """
    Deterministic rule-based fallback if LLM is unavailable with enhanced credibility scoring.
    """
    evaluated = []
    claim_nums = set(re.findall(r'\b\d+(?:,\d+)*(?:\.\d+)?\b', claim))
    
    for idx, s in enumerate(sources):
        content = s.get("content", "").lower()
        title = s.get("title", "").lower()
        full_text = f"{title} {content}"
        news_type = s.get("news_type", "Unverified")
        tier = s.get("tier", 4)

        # Check for debunking signals
        contradict_words = ["false", "fake", "hoax", "debunk", "misleading", "fabricated", "denies", "myth", "not true", "incorrect", "wrong"]
        is_contradicting = any(re.search(r'\b' + re.escape(w) + r'\b', full_text) for w in contradict_words)

        # Check for supporting signals
        support_words = ["confirmed", "official", "verified", "announced", "stated", "reported", "true", "correct"]
        is_supporting = any(re.search(r'\b' + re.escape(w) + r'\b', full_text) for w in support_words)

        # Check numbers
        source_nums = set(re.findall(r'\b\d+(?:,\d+)*(?:\.\d+)?\b', full_text))

        # A credible source discussing the same topic but citing different
        # figures is a contradiction on its own — no "debunked" keyword needed.
        # (Claim says ₹50,000, source says ₹15,000 -> Contradicted, per spec.)
        credible_source = news_type in ("Confirmed Official", "Confirmed News") or tier in (1, 2, 3)
        number_mismatch = bool(
            claim_nums and source_nums and not (claim_nums & source_nums)
            and credible_source and len(content) > 60
        )
        
        stance = "Not directly relevant"
        key_finding = s.get("content", "")[:180] + "..." if len(s.get("content", "")) > 180 else s.get("content", "")
        
        # Determine credibility weight based on news type
        if news_type == "Confirmed Official":
            credibility_weight = "High"
        elif news_type == "Confirmed News":
            credibility_weight = "Medium"
        elif news_type == "Rumor/Insider":
            credibility_weight = "Low"
        else:
            credibility_weight = "Low"

        if is_contradicting:
            stance = "Contradicting"
            key_finding = f"Source indicates the claim contains false or debunked assertions: {s.get('title', '')}"
        elif number_mismatch:
            stance = "Contradicting"
            mismatched = ", ".join(sorted(source_nums)[:3])
            key_finding = f"A credible source cites different figures ({mismatched}) than the claim states."
        elif is_supporting and not is_contradicting:
            # Be more strict - only mark as supporting if it's a credible source
            if news_type in ("Confirmed Official", "Confirmed News") or tier in (1, 2, 3):
                if claim_nums and claim_nums.issubset(source_nums):
                    stance = "Supporting"
                    key_finding = f"Source mentions confirmed figures matching the claim."
                elif "official" in full_text or "confirmed" in full_text:
                    stance = "Supporting"
                    key_finding = f"Source provides official confirmation of related information."
                else:
                    stance = "Not directly relevant"
                    key_finding = f"Source discusses topic but doesn't provide specific confirmation."
            else:
                # For unverified sources, be very conservative
                stance = "Not directly relevant"
                key_finding = f"Unverified source mentions topic but lacks credible confirmation."
        elif claim_nums and claim_nums.issubset(source_nums):
            # Only support if credible source
            if news_type in ("Confirmed Official", "Confirmed News") or tier in (1, 2, 3):
                stance = "Supporting"
                key_finding = f"Source mentions confirmed figures matching the claim."
            else:
                stance = "Not directly relevant"
                key_finding = f"Unverified source mentions numbers but lacks credible verification."
        elif len(content) > 60:
            stance = "Not directly relevant"  # Default to not relevant for unverified sources

        evaluated.append({
            "source_index": idx,
            "url": s.get("url"),
            "title": s.get("title"),
            "tier": s.get("tier"),
            "tier_name": s.get("tier_name"),
            "news_type": news_type,
            "stance": stance,
            "key_finding": key_finding,
            "matches_specifics": stance in ("Supporting", "Contradicting"),
            "credibility_weight": credibility_weight
        })
    return evaluated

def evaluate_sources_against_claim(claim: str, sources: list) -> list:
    """
    Evaluates each source against the claim using Groq LLM (or fallback).
    Returns list of evaluated evidence dicts.
    """
    if not sources:
        return []

    client = get_groq_client()
    if not client:
        return evaluate_evidence_fallback(claim, sources)

    # Prepare snippets for the prompt with enhanced metadata
    sources_payload = []
    for idx, s in enumerate(sources):
        sources_payload.append({
            "source_index": idx,
            "title": s.get("title"),
            "url": s.get("url"),
            "tier": s.get("tier_name"),
            "news_type": s.get("news_type", "Unverified"),
            "snippet": s.get("content", "")[:500]
        })

    prompt_content = f"CLAIM TO VERIFY:\n\"{claim}\"\n\nRETRIEVED SOURCES:\n{json.dumps(sources_payload, indent=2)}"

    try:
        completion = client.chat.completions.create(
            model=GROQ_TEXT_MODEL,
            messages=[
                {"role": "system", "content": EVALUATION_SYSTEM_PROMPT},
                {"role": "user", "content": prompt_content}
            ],
            temperature=0.0
        )
        resp_text = completion.choices[0].message.content.strip()
        if resp_text.startswith("```"):
            resp_text = re.sub(r"^```(?:json)?\n?", "", resp_text)
            resp_text = re.sub(r"\n?```$", "", resp_text)

        evaluations = json.loads(resp_text)
        
        # Merge LLM evaluations back with original source metadata
        results = []
        for ev in evaluations:
            idx = ev.get("source_index")
            if idx is not None and 0 <= idx < len(sources):
                orig = sources[idx]
                results.append({
                    "source_index": idx,
                    "url": orig.get("url"),
                    "title": orig.get("title"),
                    "tier": orig.get("tier"),
                    "tier_name": orig.get("tier_name"),
                    "news_type": orig.get("news_type", "Unverified"),
                    "stance": ev.get("stance", "Not directly relevant"),
                    "key_finding": ev.get("key_finding", orig.get("content", "")[:180]),
                    "matches_specifics": ev.get("matches_specifics", False),
                    "credibility_weight": ev.get("credibility_weight", "Medium")
                })
        return results if results else evaluate_evidence_fallback(claim, sources)
    except Exception as e:
        print(f"[Evaluator] LLM evaluation error: {e}")
        return evaluate_evidence_fallback(claim, sources)
