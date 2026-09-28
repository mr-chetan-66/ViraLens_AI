import os
import re
import json
import requests
from time import monotonic
from datetime import datetime, timezone
from urllib.parse import urlparse
from dotenv import load_dotenv
from cancellation import check_cancelled

load_dotenv()

# Tier definitions
TIER_1_DOMAINS = {
    "gov", "nic.in", "gov.in", "who.int", "rbi.org.in", "un.org",
    "censusindia.gov.in", "sec.gov", "supremecourtofindia.info",
    "sci.gov.in", "cdc.gov", "fda.gov", "nih.gov", "pib.gov.in"
}

TIER_2_DOMAINS = {
    "altnews.in", "boomlive.in", "snopes.com", "factcheck.org",
    "fullfact.org", "politifact.com", "vishvasnews.com", "thip.media",
    "newsmobile.in", "logicalindian.com"
}

TIER_3_DOMAINS = {
    "reuters.com", "apnews.com", "bbc.com", "bbc.co.uk", "thehindu.com",
    "indianexpress.com", "ptinews.com", "pti.in", "bloomberg.com",
    "wsj.com", "nytimes.com", "theguardian.com", "ndtv.com",
    "hindustantimes.com", "timesofindia.indiatimes.com", "economictimes.com",
    "gulfnews.com", "timesofindia.com", "indiatoday.com", "news18.com",
    "cricbuzz.com", "espncricinfo.com", "icc-cricket.com"
}

# Rumor/Insider news domains - need special handling
RUMOR_INSIDER_DOMAINS = {
    "insider.com", "businessinsider.com", "techcrunch.com",
    "theverge.com", "gizmodo.com", "engadget.com",
    "indianinsider.com", "techinsider.in"
}

RECENCY_KEYWORDS = {
    "day": ["today", "yesterday", "last 24 hours", "just now", "this morning", "today's", "breaking"],
    "week": ["last week", "this week", "past week", "latest", "recently", "new", "just announced"],
    "month": ["last month", "this month", "past month", "recent"],
    "year": ["in 2022", "in 2023", "in 2024", "in 2025", "last year", "in 2021"]
}
SEARCH_BUDGET_SECONDS = 15


class _TimeoutSession(requests.Session):
    def request(self, method, url, **kwargs):
        kwargs.setdefault("timeout", 8)
        return super().request(method, url, **kwargs)


def detect_time_window(claim: str) -> str:
    """Detect a likely freshness window for a claim so recent evidence can be weighted appropriately."""
    text = (claim or "").lower()
    if not text:
        return "m"

    if re.search(r"\b(today|yesterday|last 24 hours|just now|this morning|breaking)\b", text):
        return "d"
    if re.search(r"\b(last week|this week|past week|latest|recently|just announced|new)\b", text):
        return "w"
    if re.search(r"\b(last month|this month|past month|recent)\b", text):
        return "m"
    if re.search(r"\b(19\d{2}|20\d{2})\b", text):
        return "y"
    return "m"


def normalize_published_date(value) -> datetime | None:
    """Normalize common publication strings into a timezone-aware datetime."""
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None

    candidates = [text]
    if text.endswith("Z"):
        candidates.append(text[:-1] + "+00:00")

    patterns = [
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%d %H:%M:%S%z",
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d %b %Y",
        "%d %B %Y",
        "%b %d, %Y",
        "%B %d, %Y",
        "%d-%m-%Y",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
    ]

    for candidate in candidates:
        try:
            parsed = datetime.fromisoformat(candidate)
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except ValueError:
            pass

        try:
            if candidate.lower().endswith(" utc"):
                candidate = candidate[:-4] + "+00:00"
            parsed = datetime.strptime(candidate, "%Y-%m-%dT%H:%M:%S%z")
            return parsed.astimezone(timezone.utc)
        except ValueError:
            pass

        for fmt in patterns:
            try:
                parsed = datetime.strptime(candidate, fmt)
                if parsed.tzinfo is None:
                    return parsed.replace(tzinfo=timezone.utc)
                return parsed.astimezone(timezone.utc)
            except ValueError:
                continue

    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        pass

    try:
        from email.utils import parsedate_to_datetime
        parsed = parsedate_to_datetime(text)
        if parsed is not None:
            return parsed.astimezone(timezone.utc)
    except Exception:
        pass

    return None


def map_time_window_to_serper(window: str) -> str:
    mapping = {"d": "d", "w": "w", "m": "m", "y": "y"}
    return mapping.get((window or "").lower(), "m")


def map_time_window_to_tavily(window: str) -> str:
    mapping = {"d": "day", "w": "week", "m": "month", "y": "year"}
    return mapping.get((window or "").lower(), "month")


def result_age_days(published_at) -> int | None:
    dt = normalize_published_date(published_at)
    if not dt:
        return None
    age = datetime.now(timezone.utc) - dt
    return max(0, int(age.total_seconds() // 86400))


def classify_source_tier(url: str) -> tuple[int, str, str]:
    """
    Classifies a URL into Tier 1, 2, 3, or 4 with news type classification.
    Returns: (tier_number: int, tier_name: str, news_type: str)
    news_type can be: "Confirmed Official", "Confirmed News", "Rumor/Insider", "Unverified"
    """
    if not url:
        return 4, "Tier 4 — Unverified / General", "Unverified"

    parsed = urlparse(url.lower())
    hostname = parsed.netloc or parsed.path
    # Strip port if present
    hostname = hostname.split(":")[0]

    # Special paths for fact check sections of major news wires
    full_url = url.lower()
    if "reuters.com/fact-check" in full_url or "apnews.com/hub/ap-fact-check" in full_url:
        return 2, "Tier 2 — Established Fact-Checker", "Confirmed Official"

    # Check for rumor/insider sources first
    if any(d in hostname for d in RUMOR_INSIDER_DOMAINS):
        return 3, "Tier 3 — News (Rumor/Insider)", "Rumor/Insider"

    # Tier 1 check (.gov, .nic.in, official bodies)
    if any(hostname.endswith("." + d) or hostname == d for d in TIER_1_DOMAINS) or hostname.endswith(".gov") or hostname.endswith(".gov.in") or hostname.endswith(".nic.in"):
        return 1, "Tier 1 — Primary / Official", "Confirmed Official"

    # Tier 2 check (Fact-checkers)
    if any(d in hostname for d in TIER_2_DOMAINS) or "factcheck" in hostname:
        return 2, "Tier 2 — Established Fact-Checker", "Confirmed Official"

    # Tier 3 check (Reputable news outlets)
    if any(d in hostname for d in TIER_3_DOMAINS):
        return 3, "Tier 3 — Reputable News Wire / Outlet", "Confirmed News"

    return 4, "Tier 4 — General / Unverified", "Unverified"

def clean_query_text(claim: str) -> str:
    """Creates a direct factual search query from a claim."""
    # Remove quotes and extra punctuation
    cleaned = re.sub(r'["\']', '', claim)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

def reformulate_query(claim: str) -> str:
    """Reformulates query by appending fact check / official terms."""
    base = clean_query_text(claim)
    return f"{base} fact check official"

def generate_multiple_queries(claim: str) -> list:
    """
    Generates multiple search query strategies for better source coverage.
    Returns list of query strings to try in order.
    """
    base_claim = clean_query_text(claim)
    
    # Extract key terms (numbers, names, dates)
    numbers = re.findall(r'\b\d+(?:,\d+)*(?:\.\d+)?\b', claim)
    years = re.findall(r'\b(20\d{2}|19\d{2})\b', claim)
    
    queries = []
    
    # Query 1: Direct claim search
    queries.append(base_claim)
    
    # Query 2: Fact check focused
    queries.append(f"{base_claim} fact check")
    
    # Query 3: Official/verification focused
    queries.append(f"{base_claim} official verification")
    
    # Query 4: If there are numbers, search with them
    if numbers:
        queries.append(f"{base_claim} {' '.join(numbers[:2])}")
    
    # Query 5: Debunking focused
    queries.append(f"{base_claim} debunk fake hoax")
    
    # Query 6: News focused
    queries.append(f"{base_claim} news report")
    
    return queries[:4]  # Limit to 4 most effective queries

def _pack_result(title: str, url: str, content: str, engine: str, published_at: str | None = None) -> dict:
    tier_num, tier_name, news_type = classify_source_tier(url)
    normalized_date = normalize_published_date(published_at)
    return {
        "title": title or "No Title",
        "url": url,
        "content": content or "",
        "tier": tier_num,
        "tier_name": tier_name,
        "news_type": news_type,
        "engine": engine,
        "published_at": published_at,
        "published_date_iso": normalized_date.isoformat() if normalized_date else None,
        "published_age_days": result_age_days(published_at)
    }


def _merge_unique(all_results: list, existing_urls: set, incoming: list) -> None:
    for r in incoming:
        url = r.get("url")
        if url and url not in existing_urls:
            all_results.append(r)
            existing_urls.add(url)


def run_ddg_search(query: str, max_results: int = 6) -> list:
    """
    Keyless DuckDuckGo search fallback (no API key).
    Used when Tavily/Serper are missing or return thin coverage.
    """
    if not query or not query.strip():
        return []
    try:
        from ddgs import DDGS
        raw = DDGS(timeout=8).text(query, max_results=max_results) or []
        results = []
        for item in raw:
            url = item.get("href") or item.get("url") or ""
            if not url:
                continue
            results.append(_pack_result(
                item.get("title", "No Title"),
                url,
                item.get("body") or item.get("snippet") or "",
                engine="duckduckgo"
            ))
        return results
    except Exception as e:
        print(f"[Search Engine] DuckDuckGo search error: {e}")
        return []


def run_tavily_search(query: str, max_results: int = 6, time_filter: str | None = None) -> list:
    """
    Runs web search using Tavily API.
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return []

    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=api_key, session=_TimeoutSession())
        params = {
            "query": query,
            "search_depth": "advanced",
            "max_results": max_results,
            "include_answer": False,
        }
        if time_filter:
            params["time_range"] = map_time_window_to_tavily(time_filter)
        response = client.search(**params)
        results = []
        for r in response.get("results", []):
            url = r.get("url", "")
            results.append(_pack_result(
                r.get("title", "No Title"),
                url,
                r.get("content", ""),
                engine="tavily",
                published_at=r.get("published_date") or r.get("published_at") or r.get("date")
            ))
        return results
    except Exception as e:
        print(f"[Search Engine] Tavily search error: {e}")
        return []

def run_serper_search(query: str, max_results: int = 6, time_filter: str | None = None) -> list:
    """
    Runs web search using Serper API (Google Search API).
    """
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        return []

    try:
        url = "https://google.serper.dev/search"
        payload = {
            "q": query,
            "num": max_results,
        }
        if time_filter:
            payload["tbs"] = f"qdr:{map_time_window_to_serper(time_filter)}"
        headers = {
            'X-API-KEY': api_key,
            'Content-Type': 'application/json'
        }
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=(3, 7))
        if response.status_code != 200:
            print(f"[Search Engine] Serper API error: {response.status_code}")
            return []

        data = response.json()
        results = []

        # Process organic results
        for item in data.get("organic", []):
            url = item.get("link", "")
            published_at = item.get("date") or item.get("publishedDate") or item.get("snippet")
            results.append(_pack_result(
                item.get("title", "No Title"),
                url,
                item.get("snippet", ""),
                engine="serper",
                published_at=published_at
            ))

        # Add answerBox if available (often contains authoritative info)
        if "answerBox" in data:
            answer = data["answerBox"]
            answer_url = answer.get("link", answer.get("source", ""))
            if answer_url:
                results.append(_pack_result(
                    answer.get("title", "Direct Answer"),
                    answer_url,
                    answer.get("answer", answer.get("snippet", "")),
                    engine="serper",
                    published_at=answer.get("date") or answer.get("publishedDate")
                ))

        return results
    except Exception as e:
        print(f"[Search Engine] Serper search error: {e}")
        return []


def run_gemini_search(query: str, max_results: int = 6, time_filter: str | None = None) -> list:
    """Optional Gemini-backed Google Search retriever. Returns ranked source dicts compatible with the pipeline."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return []

    try:
        from google import genai
        from google.genai import types
        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=10000),
        )
        config = {"tools": [{"google_search": {}}]}
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=query,
            config=config,
        )

        citations = []
        for item in getattr(response, "candidates", []) or []:
            ground = getattr(item, "grounding_metadata", None)
            if not ground:
                continue
            for chunk in getattr(ground, "grounding_chunks", []) or []:
                web = getattr(chunk, "web", None)
                if not web:
                    continue
                title = getattr(web, "title", "") or "Source"
                url = getattr(web, "uri", "") or getattr(web, "url", "") or ""
                if not url:
                    continue
                citations.append(_pack_result(title, url, web.get("snippet", "") if isinstance(web, dict) else "", engine="gemini"))

        if not citations:
            return []
        return citations[:max_results]
    except Exception as e:
        print(f"[Search Engine] Gemini search error: {e}")
        return []

def search_sources_for_claim(claim: str, cancel_event=None) -> tuple[list, int]:
    """
    Multi-engine search with early stopping.
    Once the pipeline has enough high-quality evidence, it exits quickly instead of
    burning time on redundant searches across every provider.
    """
    search_started = monotonic()
    check_cancelled(cancel_event)
    all_results = []
    attempts = 0
    existing_urls = set()
    queries = generate_multiple_queries(claim)
    claim_numbers = re.findall(r'\b\d+(?:,\d+)*(?:\.\d+)?\b', claim)
    time_window = detect_time_window(claim)

    primary = queries[0]
    if claim_numbers and len(queries) > 3:
        secondary = queries[3]
        tertiary = queries[1]
    else:
        secondary = queries[1] if len(queries) > 1 else queries[0]
        tertiary = queries[2] if len(queries) > 2 else queries[0]

    tavily_key = os.getenv("TAVILY_API_KEY")
    serper_key = os.getenv("SERPER_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")

    def high_quality() -> bool:
        return any(r["tier"] in (1, 2) for r in all_results)

    def confirmed_count() -> int:
        return sum(1 for r in all_results if r["news_type"] in ("Confirmed Official", "Confirmed News"))

    def enough_quality() -> bool:
        return high_quality() and confirmed_count() >= 1 and len(all_results) >= 2

    def within_budget() -> bool:
        return monotonic() - search_started < SEARCH_BUDGET_SECONDS

    def finalize_results() -> tuple[list, int]:
        def rank_score(result):
            tier_score = (4 - result["tier"]) * 100
            if result["news_type"] == "Confirmed Official":
                type_bonus = 50
            elif result["news_type"] == "Confirmed News":
                type_bonus = 30
            elif result["news_type"] == "Rumor/Insider":
                type_bonus = 10
            else:
                type_bonus = 0

            freshness_bonus = 0
            age_days = result.get("published_age_days")
            if age_days is not None:
                if age_days <= 7:
                    freshness_bonus = 25
                elif age_days <= 30:
                    freshness_bonus = 12
                elif age_days > 365:
                    freshness_bonus = -15
            return tier_score + type_bonus + freshness_bonus

        all_results.sort(key=rank_score, reverse=True)
        ranked = all_results[:15]
        enrich_thin_snippets(
            ranked,
            max_fetch=1,
            cancel_event=cancel_event,
            started_at=search_started,
        )
        return ranked, attempts

    if tavily_key and within_budget():
        check_cancelled(cancel_event)
        _merge_unique(all_results, existing_urls, run_tavily_search(primary, max_results=6, time_filter=time_window))
        attempts += 1
        check_cancelled(cancel_event)
        if enough_quality():
            return finalize_results()

    if serper_key and not enough_quality() and within_budget():
        check_cancelled(cancel_event)
        _merge_unique(all_results, existing_urls, run_serper_search(secondary, max_results=6, time_filter=time_window))
        attempts += 1
        check_cancelled(cancel_event)
        if enough_quality():
            return finalize_results()

    if gemini_key and not enough_quality() and within_budget():
        check_cancelled(cancel_event)
        _merge_unique(all_results, existing_urls, run_gemini_search(primary, max_results=5, time_filter=time_window))
        attempts += 1
        check_cancelled(cancel_event)
        if enough_quality():
            return finalize_results()

    if not enough_quality() and attempts < 4 and within_budget():
        check_cancelled(cancel_event)
        ddg_query = secondary if tavily_key or serper_key or gemini_key else primary
        _merge_unique(all_results, existing_urls, run_ddg_search(ddg_query, max_results=6))
        attempts += 1
        check_cancelled(cancel_event)

    if not enough_quality() and attempts < 4 and within_budget():
        check_cancelled(cancel_event)
        extra_query = tertiary
        if tavily_key:
            _merge_unique(all_results, existing_urls, run_tavily_search(extra_query, max_results=4, time_filter=time_window))
            attempts += 1
        elif serper_key:
            _merge_unique(all_results, existing_urls, run_serper_search(extra_query, max_results=4, time_filter=time_window))
            attempts += 1
        elif gemini_key:
            _merge_unique(all_results, existing_urls, run_gemini_search(extra_query, max_results=4, time_filter=time_window))
            attempts += 1
        else:
            _merge_unique(all_results, existing_urls, run_ddg_search(extra_query, max_results=4))
            attempts += 1

    check_cancelled(cancel_event)
    return finalize_results()


def enrich_thin_snippets(results: list, max_fetch: int = 3, cancel_event=None, started_at=None) -> None:
    """Pull a bit more page text when a search snippet is too short to evaluate."""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return

    fetched = 0
    for r in results:
        check_cancelled(cancel_event)
        if started_at is not None and monotonic() - started_at >= SEARCH_BUDGET_SECONDS:
            break
        if fetched >= max_fetch:
            break
        if len((r.get("content") or "").strip()) >= 220:
            continue
        url = r.get("url")
        if not url or not url.startswith("http"):
            continue
        try:
            resp = requests.get(
                url,
                timeout=(2, 3),
                headers={"User-Agent": "Mozilla/5.0 (compatible; ViraLensAI/1.0)"},
            )
            if resp.status_code != 200 or not resp.text:
                continue
            soup = BeautifulSoup(resp.text, "html.parser")
            for tag in soup(["script", "style", "noscript"]):
                tag.decompose()
            paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
            extra = " ".join(p for p in paragraphs if len(p) > 40)[:1200]
            if len(extra) > len(r.get("content") or ""):
                r["content"] = extra
                fetched += 1
        except Exception:
            continue
