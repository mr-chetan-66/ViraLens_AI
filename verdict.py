def compute_verdict_and_confidence(claim: str, evaluated_evidence: list) -> dict:
    """
    Computes enhanced verdict with news type awareness:
      - Verdict: Supported, Contradicted, or Unclear (with sub-types)
      - Confidence Score: 0-100%
      - Source Type Breakdown: Confirmed Official vs Confirmed News vs Rumor/Insider
      - Validated Citations: Real sources that directly support or contradict
    """
    if not evaluated_evidence:
        return {
            "verdict": "Unclear",
            "verdict_icon": "⚠️",
            "confidence": 20,
            "verdict_label": "⚠️ Unclear",
            "verdict_sub_type": "Insufficient Evidence",
            "rationale": "No relevant or credible sources could be retrieved to verify this claim.",
            "source_breakdown": {
                "confirmed_official": 0,
                "confirmed_news": 0,
                "rumor_insider": 0,
                "unverified": 0
            },
            "supporting_sources": [],
            "contradicting_sources": [],
            "all_citations": []
        }

    # Filter out sources that are not directly relevant
    relevant_evidence = [e for e in evaluated_evidence if e["stance"] in ("Supporting", "Contradicting")]

    if not relevant_evidence:
        return {
            "verdict": "Unclear",
            "verdict_icon": "⚠️",
            "confidence": 25,
            "verdict_label": "⚠️ Unclear",
            "verdict_sub_type": "No Direct Evidence",
            "rationale": "Retrieved sources discuss related topics but do not directly confirm or refute the specific details.",
            "source_breakdown": {
                "confirmed_official": 0,
                "confirmed_news": 0,
                "rumor_insider": 0,
                "unverified": 0
            },
            "supporting_sources": [],
            "contradicting_sources": [],
            "all_citations": []
        }

    # Separate into supporting and contradicting
    supporting = [e for e in relevant_evidence if e["stance"] == "Supporting"]
    contradicting = [e for e in relevant_evidence if e["stance"] == "Contradicting"]

    # Count source types for breakdown
    def count_source_types(evidence_list):
        breakdown = {
            "confirmed_official": 0,
            "confirmed_news": 0,
            "rumor_insider": 0,
            "unverified": 0
        }
        for e in evidence_list:
            news_type = e.get("news_type", "Unverified")
            if news_type == "Confirmed Official":
                breakdown["confirmed_official"] += 1
            elif news_type == "Confirmed News":
                breakdown["confirmed_news"] += 1
            elif news_type == "Rumor/Insider":
                breakdown["rumor_insider"] += 1
            else:
                breakdown["unverified"] += 1
        return breakdown

    # Check for presence of strong tiers and source types
    has_tier1_contra = any(e["tier"] == 1 for e in contradicting)
    has_tier2_contra = any(e["tier"] == 2 for e in contradicting)
    has_tier1_supp = any(e["tier"] == 1 for e in supporting)
    has_tier2_supp = any(e["tier"] == 2 for e in supporting)
    
    # Check for confirmed official sources
    has_confirmed_official_contra = any(e.get("news_type") == "Confirmed Official" for e in contradicting)
    has_confirmed_official_supp = any(e.get("news_type") == "Confirmed Official" for e in supporting)
    
    # Check if only rumor/insider sources support
    only_rumor_support = (
        len(supporting) > 0 and 
        all(e.get("news_type") in ("Rumor/Insider", "Unverified") for e in supporting) and
        len([e for e in supporting if e.get("news_type") == "Confirmed Official"]) == 0
    )

    # Determine Verdict with enhanced logic
    if contradicting and not supporting:
        verdict = "Contradicted"
        verdict_icon = "❌"
        if has_confirmed_official_contra:
            verdict_sub_type = "Officially Debunked"
        elif has_tier2_contra:
            verdict_sub_type = "Fact-Checked as False"
        else:
            verdict_sub_type = "Contradicted by Sources"
    elif supporting and not contradicting:
        # CRITICAL FIX: Check if sources are actually credible
        tier_1_2_count = sum(1 for e in supporting if e["tier"] in (1, 2))
        tier_3_count = sum(1 for e in supporting if e["tier"] == 3)
        tier_4_count = sum(1 for e in supporting if e["tier"] == 4)
        
        # If only Tier 4 (unverified) sources, mark as unclear
        if tier_4_count > 0 and tier_1_2_count == 0 and tier_3_count == 0:
            verdict = "Unclear"
            verdict_icon = "⚠️"
            verdict_sub_type = "Rumor-Based Claims"
        elif only_rumor_support:
            verdict = "Unclear"
            verdict_icon = "⚠️"
            verdict_sub_type = "Unverified Claims"
        elif has_confirmed_official_supp:
            verdict = "Supported"
            verdict_icon = "✅"
            verdict_sub_type = "Officially Confirmed"
        elif has_tier2_supp:
            verdict = "Supported"
            verdict_icon = "✅"
            verdict_sub_type = "Fact-Checked as True"
        elif tier_3_count > 0:
            verdict = "Supported"
            verdict_icon = "✅"
            verdict_sub_type = "Reported by News Sources"
        else:
            verdict = "Unclear"
            verdict_icon = "⚠️"
            verdict_sub_type = "Unverified Claims"
    elif contradicting and supporting:
        # Conflict between sources - prioritize confirmed official
        if has_confirmed_official_contra and not has_confirmed_official_supp:
            verdict = "Contradicted"
            verdict_icon = "❌"
            verdict_sub_type = "Official Sources Contradict"
        elif has_confirmed_official_supp and not has_confirmed_official_contra:
            verdict = "Supported"
            verdict_icon = "✅"
            verdict_sub_type = "Official Sources Confirm"
        elif has_tier1_contra or (has_tier2_contra and not has_tier1_supp):
            verdict = "Contradicted"
            verdict_icon = "❌"
            verdict_sub_type = "Stronger Contradicting Evidence"
        elif has_tier1_supp and not has_tier1_contra:
            verdict = "Supported"
            verdict_icon = "✅"
            verdict_sub_type = "Stronger Supporting Evidence"
        else:
            verdict = "Unclear"
            verdict_icon = "⚠️"
            verdict_sub_type = "Conflicting Evidence"
    else:
        verdict = "Unclear"
        verdict_icon = "⚠️"
        verdict_sub_type = "Insufficient Evidence"

    # Compute Confidence Score (0-100%) with enhanced factors
    if verdict == "Unclear":
        base_confidence = 35
        if only_rumor_support or verdict_sub_type == "Rumor-Based Claims":
            base_confidence = 15  # Very low confidence for rumor-based claims
        elif verdict_sub_type == "Unverified Claims":
            base_confidence = 20  # Low confidence for unverified claims
        confidence = base_confidence
        if verdict_sub_type == "Rumor-Based Claims":
            rationale = "Claim is only supported by unverified social media posts and rumors. No credible news or official sources found."
        elif verdict_sub_type == "Unverified Claims":
            rationale = "Available evidence is conflicting or insufficient to draw a definitive conclusion."
        else:
            rationale = "Available evidence is conflicting or insufficient to draw a definitive conclusion."
    elif verdict == "Contradicted":
        active_sources = contradicting
        base_score = 50
        
        # Source type quality boost
        if any(e.get("news_type") == "Confirmed Official" for e in active_sources):
            base_score += 30
        elif any(e.get("news_type") == "Confirmed News" for e in active_sources):
            base_score += 20
        elif any(e.get("news_type") == "Rumor/Insider" for e in active_sources):
            base_score += 10
        
        # Tier quality boost (complementary to source type)
        if any(e["tier"] == 1 for e in active_sources):
            base_score += 15
        elif any(e["tier"] == 2 for e in active_sources):
            base_score += 10
        elif any(e["tier"] == 3 for e in active_sources):
            base_score += 5

        # Corroboration boost (more than 1 independent source)
        if len(active_sources) >= 2:
            base_score += 12
        if any(e.get("matches_specifics") for e in active_sources):
            base_score += 8

        confidence = min(base_score, 96)
        official_count = sum(1 for e in active_sources if e.get("news_type") == "Confirmed Official")
        rationale = f"Contradicted by {len(active_sources)} source(s) ({official_count} official) indicating factual inaccuracies."
    else: # Supported
        active_sources = supporting
        base_score = 50
        
        # Source type quality boost
        if any(e.get("news_type") == "Confirmed Official" for e in active_sources):
            base_score += 30
        elif any(e.get("news_type") == "Confirmed News" for e in active_sources):
            base_score += 20
        elif any(e.get("news_type") == "Rumor/Insider" for e in active_sources):
            base_score += 10
        
        # Tier quality boost
        if any(e["tier"] == 1 for e in active_sources):
            base_score += 15
        elif any(e["tier"] == 2 for e in active_sources):
            base_score += 10
        elif any(e["tier"] == 3 for e in active_sources):
            base_score += 5

        # Corroboration boost
        if len(active_sources) >= 2:
            base_score += 12
        if any(e.get("matches_specifics") for e in active_sources):
            base_score += 8

        confidence = min(base_score, 95)
        official_count = sum(1 for e in active_sources if e.get("news_type") == "Confirmed Official")
        rationale = f"Supported by {len(active_sources)} source(s) ({official_count} official) confirming the details."

    # Compile source breakdown
    total_breakdown = count_source_types(relevant_evidence)

    # Compile verified citations with clickable URLs and enhanced metadata
    all_citations = []
    seen_urls = set()
    for e in relevant_evidence:
        if e["url"] and e["url"] not in seen_urls:
            all_citations.append({
                "title": e.get("title", "Source Link"),
                "url": e["url"],
                "tier": e.get("tier"),
                "tier_name": e.get("tier_name"),
                "news_type": e.get("news_type", "Unverified"),
                "stance": e["stance"],
                "finding": e.get("key_finding", ""),
                "credibility_weight": e.get("credibility_weight", "Medium")
            })
            seen_urls.add(e["url"])

    return {
        "verdict": verdict,
        "verdict_icon": verdict_icon,
        "verdict_label": f"{verdict_icon} {verdict}",
        "verdict_sub_type": verdict_sub_type,
        "confidence": confidence,
        "rationale": rationale,
        "source_breakdown": total_breakdown,
        "supporting_sources": [c for c in all_citations if c["stance"] == "Supporting"],
        "contradicting_sources": [c for c in all_citations if c["stance"] == "Contradicting"],
        "all_citations": all_citations
    }
