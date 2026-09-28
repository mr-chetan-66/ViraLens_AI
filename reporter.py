import re
import json
from dotenv import load_dotenv

load_dotenv()

from llm import get_groq_client, GROQ_TEXT_MODEL

REPORT_SYSTEM_PROMPT = """You are a master communicator who writes plain-language, non-expert fact-check summaries with enhanced credibility awareness.
The reader is an everyday person with zero time who will not read jargon, technical lingo, or chain-of-thought.

Format rules:
1. "what_we_found": 2 to 3 concise, bulleted factual findings summarizing what the credible evidence discovered, referencing the actual source names and their credibility levels (official sources, fact-checkers, etc.).
2. "in_simple_terms": 1 to 2 clear, punchy sentences explaining the bottom line with emphasis on source credibility (e.g. "Official government sources and fact-checkers confirm this claim is false. The real scheme exists, but the amount being shared is wrong.").
3. Distinguish between confirmed official information vs. rumors or insider reports in your summary.
4. NEVER invent or hallucinate facts or URLs. Use strictly what is provided.
5. If the verdict is based on official sources, emphasize this in the summary.
6. Output strictly valid JSON with this structure:
{
  "what_we_found": [
    "Key finding line 1 with context and source credibility",
    "Key finding line 2 with context and source credibility"
  ],
  "in_simple_terms": "One or two short sentences in plain everyday language with source credibility emphasis."
}"""

def fallback_summary(claim: str, verdict_data: dict) -> dict:
    verdict = verdict_data["verdict"]
    verdict_sub_type = verdict_data.get("verdict_sub_type", "")
    citations = verdict_data["all_citations"]
    source_breakdown = verdict_data.get("source_breakdown", {})
    
    findings = []
    if citations:
        # Prioritize official and confirmed sources in findings
        confirmed_sources = [c for c in citations if c.get("news_type") in ("Confirmed Official", "Confirmed News")]
        sources_to_show = confirmed_sources[:2] if len(confirmed_sources) >= 2 else citations[:3]
        
        for c in sources_to_show:
            source_credibility = c.get("news_type", "Source")
            findings.append(f"{c['finding']} [{source_credibility}: {c['title']}]")
    else:
        findings.append("No verifiable official or independent reports were found to substantiate or refute this claim.")

    # Enhanced simple terms with source credibility
    official_count = source_breakdown.get("confirmed_official", 0)
    confirmed_news_count = source_breakdown.get("confirmed_news", 0)
    rumor_count = source_breakdown.get("rumor_insider", 0)
    unverified_count = source_breakdown.get("unverified", 0)
    
    if verdict == "Contradicted":
        if official_count > 0:
            in_simple = f"Official government sources and {official_count} official report(s) directly contradict this claim."
        elif confirmed_news_count > 0:
            in_simple = f"Established fact-checkers and {confirmed_news_count} news outlet(s) confirm this claim is false."
        else:
            in_simple = "The facts found in credible reports directly contradict what is being claimed."
    elif verdict == "Supported":
        if official_count > 0:
            in_simple = f"Official government sources and {official_count} official report(s) confirm this claim is accurate."
        elif confirmed_news_count > 0:
            in_simple = f"Established fact-checkers and {confirmed_news_count} news outlet(s) confirm this claim is true."
        else:
            in_simple = "Credible reports and sources confirm that this claim is accurate."
    else:
        if verdict_sub_type == "Rumor-Based Claims":
            in_simple = f"This claim is only supported by {unverified_count} unverified social media post(s) and rumors. No credible news or official sources found."
        elif verdict_sub_type == "Unverified Claims":
            in_simple = "Only unverified or rumor-based sources mention this; no official confirmation available."
        else:
            in_simple = "There is not enough credible evidence online to confirm whether this is true or false."

    return {
        "what_we_found": findings,
        "in_simple_terms": in_simple
    }

def generate_plain_report(claim: str, verdict_data: dict) -> dict:
    """
    Builds the final user-facing report structure with real verified source links.
    """
    client = get_groq_client()
    summary = None

    if client and verdict_data.get("all_citations"):
        citations_summary = [
            {
                "title": c["title"], 
                "url": c["url"], 
                "stance": c["stance"], 
                "finding": c["finding"], 
                "tier": c["tier_name"],
                "news_type": c.get("news_type", "Unverified"),
                "credibility": c.get("credibility_weight", "Medium")
            }
            for c in verdict_data["all_citations"]
        ]
        user_prompt = (
            f"CLAIM: \"{claim}\"\n"
            f"VERDICT: {verdict_data['verdict']} ({verdict_data.get('verdict_sub_type', '')})\n"
            f"SOURCE BREAKDOWN: {json.dumps(verdict_data.get('source_breakdown', {}), indent=2)}\n"
            f"EVIDENCE FOUND:\n{json.dumps(citations_summary, indent=2)}"
        )
        try:
            completion = client.chat.completions.create(
                model=GROQ_TEXT_MODEL,
                messages=[
                    {"role": "system", "content": REPORT_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2
            )
            raw = completion.choices[0].message.content.strip()
            if raw.startswith("```"):
                raw = re.sub(r"^```(?:json)?\n?", "", raw)
                raw = re.sub(r"\n?```$", "", raw)
            summary = json.loads(raw)
        except Exception as e:
            print(f"[Reporter] LLM generation error: {e}")
            summary = None

    if not summary:
        summary = fallback_summary(claim, verdict_data)

    return {
        "claim": claim,
        "verdict": verdict_data["verdict"],
        "verdict_icon": verdict_data["verdict_icon"],
        "verdict_label": verdict_data.get("verdict_label", verdict_data["verdict"]),
        "verdict_sub_type": verdict_data.get("verdict_sub_type", ""),
        "confidence": verdict_data["confidence"],
        "source_breakdown": verdict_data.get("source_breakdown", {
            "confirmed_official": 0,
            "confirmed_news": 0,
            "rumor_insider": 0,
            "unverified": 0
        }),
        "what_we_found": summary.get("what_we_found", []),
        "in_simple_terms": summary.get("in_simple_terms", ""),
        "citations": verdict_data.get("all_citations", [])
    }
