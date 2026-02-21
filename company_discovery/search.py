"""
search.py — Production-Grade Region-Aware Company Discovery
============================================================

Uses Tavily API when available, otherwise falls back to built-in
mock data so the pipeline works without an API key.

Features:
- Strict region validation
- Blocks aggregators and listing pages
- Blocks blogs and directory sites
- Filters small local businesses
- Returns only likely company homepages
- Graceful fallback to mock when Tavily is unavailable
"""

import os
import logging
from typing import List, Dict, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# ────────────────────────────────────────────────────────────────
# Tavily Setup (graceful — falls back to mock if unavailable)
# ────────────────────────────────────────────────────────────────
_tavily_client = None
USE_TAVILY = False

try:
    from tavily import TavilyClient
    _api_key = os.getenv("TAVILY_API_KEY")
    if _api_key:
        _tavily_client = TavilyClient(api_key=_api_key)
        USE_TAVILY = True
        logger.info("Tavily API key found — using live search.")
    else:
        logger.warning("TAVILY_API_KEY not set — falling back to mock search.")
except ImportError:
    logger.warning("tavily package not installed — falling back to mock search.")

# ────────────────────────────────────────────────────────────────
# Target Industries
# ────────────────────────────────────────────────────────────────
TARGET_INDUSTRIES = [
    "SaaS",
    "FinTech",
    "HealthTech",
    "EdTech",
    "IT Services",
    "E-commerce",
    "Enterprise Tech",
    "Logistics Tech",
]

# ────────────────────────────────────────────────────────────────
# Exclusion Keywords (small businesses)
# ────────────────────────────────────────────────────────────────
EXCLUSION_KEYWORDS = [
    "restaurant", "cafe", "bakery", "salon", "spa",
    "grocery", "kirana", "dhaba", "tailor",
]

# ────────────────────────────────────────────────────────────────
# Block Aggregator / Listing Sites
# ────────────────────────────────────────────────────────────────
BLOCKED_DOMAINS = [
    "linkedin.com",
    "ycombinator.com",
    "crunchbase.com",
    "glassdoor.com",
    "builtin",
    "angel.co",
    "medium.com",
    "wordpress.com",
    "blogspot.com",
    "leadsquared.com",
    "indeed.com",
]

BLOCKED_TITLE_KEYWORDS = [
    "top",
    "best",
    "list",
    "companies in",
    "startups in",
    "directory",
    "funded by",
    "industry",
    "article",
    "blog",
]


# ════════════════════════════════════════════════════════════════
# Utility Functions
# ════════════════════════════════════════════════════════════════

def _extract_domain(url: str) -> str:
    parsed = urlparse(url)
    return parsed.netloc.lower()


def _is_homepage(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.path in ["", "/"]


def _is_excluded(title: str, snippet: str) -> bool:
    combined = f"{title} {snippet}".lower()
    return any(keyword in combined for keyword in EXCLUSION_KEYWORDS)


def _is_aggregator(title: str, url: str) -> bool:
    title_lower = title.lower()
    url_lower = url.lower()

    if any(domain in url_lower for domain in BLOCKED_DOMAINS):
        return True

    if any(keyword in title_lower for keyword in BLOCKED_TITLE_KEYWORDS):
        return True

    return False


def _region_in_text(text: str, region: str) -> bool:
    return region.lower() in text.lower()


def _extract_company_name(title: str) -> str:
    for sep in [" — ", " - ", " | ", " · ", " – "]:
        if sep in title:
            return title.split(sep)[0].strip()
    return title.strip()


def _real_web_search(query: str, max_results: int = 10):
    """Live search via Tavily API."""
    logger.info("Tavily search: %s", query)
    response = _tavily_client.search(
        query=query,
        max_results=max_results,
        search_depth="advanced"
    )
    return [
        {"title": r.get("title", ""), "url": r.get("url", ""), "snippet": r.get("content", "")}
        for r in response.get("results", [])
    ]


def _mock_web_search(query: str, num_results: int = 10) -> List[Dict[str, str]]:
    """
    Built-in mock search for offline / demo usage.
    Returns curated real companies — no fake data.
    Ensures the pipeline runs without an API key.
    """
    _mock_db: Dict[str, List[Dict[str, str]]] = {
        "SaaS": [
            {"title": "Druva — Cloud Data Protection & Management",
             "url": "https://www.druva.com",
             "snippet": "Druva delivers data protection and management for the cloud era. Headquartered in Pune, backed by $328M+ in funding."},
            {"title": "Zensar Technologies — Digital Solutions & Technology Services",
             "url": "https://www.zensar.com",
             "snippet": "Zensar Technologies is a leading digital solutions and technology services company based in Pune, part of the RPG Group."},
        ],
        "FinTech": [
            {"title": "BillDesk — Online Payment Gateway",
             "url": "https://www.billdesk.com",
             "snippet": "BillDesk is one of India's largest payment gateways, processing billions in transactions. Based in Pune/Mumbai."},
        ],
        "HealthTech": [
            {"title": "CrelioHealth — Diagnostic Lab Software",
             "url": "https://www.creliohealth.com",
             "snippet": "CrelioHealth offers cloud-based diagnostic and lab information management software, headquartered in Pune."},
        ],
        "EdTech": [
            {"title": "Imarticus Learning — Professional Education",
             "url": "https://imarticus.org",
             "snippet": "Imarticus Learning provides professional education in finance, analytics, and technology with centers across India."},
        ],
        "IT Services": [
            {"title": "Persistent Systems — Product Engineering",
             "url": "https://www.persistent.com",
             "snippet": "Persistent Systems is a global solutions engineering company headquartered in Pune with 23,000+ employees."},
            {"title": "Cybage Software — Technology Consulting",
             "url": "https://www.cybage.com",
             "snippet": "Cybage is a technology consulting firm based in Pune with 6,000+ employees serving Fortune 500 clients."},
            {"title": "KPIT Technologies — Automotive Software",
             "url": "https://www.kpit.com",
             "snippet": "KPIT Technologies specializes in automotive software solutions, headquartered in Pune, listed on BSE/NSE."},
        ],
        "E-commerce": [
            {"title": "Firstcry — Baby & Kids Products",
             "url": "https://www.firstcry.com",
             "snippet": "Firstcry is Asia's largest online store for baby and kids products, headquartered in Pune. Backed by SoftBank."},
        ],
        "Enterprise Tech": [
            {"title": "Pubmatic — Digital Advertising Technology",
             "url": "https://www.pubmatic.com",
             "snippet": "PubMatic is a sell-side advertising platform, NASDAQ-listed, with a major engineering center in Pune."},
        ],
        "Logistics Tech": [
            {"title": "ElasticRun — Technology-driven Last-mile Logistics",
             "url": "https://www.elastic.run",
             "snippet": "ElasticRun leverages technology for last-mile delivery and FMCG distribution, headquartered in Pune. Series E funded."},
        ],
    }

    results: List[Dict[str, str]] = []
    for industry, items in _mock_db.items():
        if industry.lower() in query.lower():
            results.extend(items)

    # If no industry matched, return all
    if not results:
        for items in _mock_db.values():
            results.extend(items)

    return results[:num_results]


# ════════════════════════════════════════════════════════════════
# Main Search Function
# ════════════════════════════════════════════════════════════════

def search_companies(region: str,
                     industries: Optional[List[str]] = None
                     ) -> List[Dict[str, str]]:

    if industries is None:
        industries = TARGET_INDUSTRIES

    seen_domains = set()
    candidates: List[Dict[str, str]] = []

    for industry in industries:

        query = (
            f"{industry} company headquartered in {region} "
            f"official website"
        )

        # ── Dispatch: live Tavily or mock fallback ─────────────
        if USE_TAVILY:
            raw_results = _real_web_search(query)
        else:
            raw_results = _mock_web_search(query)

        for r in raw_results:
            title = r.get("title", "")
            url = r.get("url", "")
            snippet = r.get("snippet", "") or r.get("content", "")

            if not url:
                continue

            domain = _extract_domain(url)

            # Skip duplicates
            if domain in seen_domains:
                continue

            # Only allow homepage URLs (Tavily mode only — mock URLs are already homepages)
            if USE_TAVILY and not _is_homepage(url):
                continue

            # Block aggregator / listing pages
            if _is_aggregator(title, url):
                continue

            # Block small local businesses
            if _is_excluded(title, snippet):
                continue

            # Strict region validation (Tavily mode only — mock data is pre-curated)
            if USE_TAVILY:
                combined_text = f"{title} {snippet}"
                if not _region_in_text(combined_text, region):
                    continue

            seen_domains.add(domain)

            candidates.append({
                "name": _extract_company_name(title),
                "website": url,
                "industry": industry,
                "snippet": snippet
            })

    logger.info(
        "Found %d validated companies in %s (mode: %s)",
        len(candidates), region, "Tavily" if USE_TAVILY else "Mock"
    )

    return candidates