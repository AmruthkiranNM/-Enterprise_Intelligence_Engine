"""
search.py — Company Search Logic
==================================
Responsible for querying a web search API (mock Tavily / SerpAPI) to find
companies in a target region across scalable industry verticals.

Design decisions:
  - We issue one search per industry to get focused results.
  - A keyword exclusion list filters out small local businesses
    (restaurants, salons, retail shops, cafes) which would pollute results.
  - The mock search function is isolated so it can be swapped for a real
    Tavily/SerpAPI client by changing a single import.
"""

import logging
import re
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Industry verticals we target — these represent scalable, tech-enabled
# sectors where companies are more likely to have measurable digital
# footprints and public revenue signals.
# ---------------------------------------------------------------------------
TARGET_INDUSTRIES: List[str] = [
    "SaaS",
    "FinTech",
    "HealthTech",
    "EdTech",
    "IT Services",
    "E-commerce",
    "Enterprise Tech",
    "Logistics Tech",
]

# ---------------------------------------------------------------------------
# Exclusion keywords — if any of these appear in a search result's title or
# snippet we discard the result. This keeps out hyper-local businesses that
# will never meet a ₹1Cr+ threshold.
# ---------------------------------------------------------------------------
EXCLUSION_KEYWORDS: List[str] = [
    "restaurant", "cafe", "coffee", "bakery", "salon", "spa",
    "barbershop", "parlour", "parlor", "boutique", "florist",
    "laundry", "dry clean", "grocery", "kirana", "pan shop",
    "chai", "juice", "sweet shop", "mithai", "dhaba",
    "tailor", "jeweller", "jeweler", "optical", "chemist",
    "stationery", "photocopy", "xerox", "mobile repair",
    "garage", "auto repair", "tyre", "tire shop",
]


# ═══════════════════════════════════════════════════════════════════════════
#  Mock Search API
# ═══════════════════════════════════════════════════════════════════════════
# This function simulates what a real Tavily / SerpAPI call would return.
# Replace the body of this function with actual API calls when API keys
# are available. The interface (input → output) stays the same.
# ═══════════════════════════════════════════════════════════════════════════

def _mock_web_search(query: str, num_results: int = 10) -> List[Dict[str, str]]:
    """
    Mock web search function simulating Tavily / SerpAPI responses.

    In production, replace this with:
        from tavily import TavilyClient
        client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
        response = client.search(query, max_results=num_results)
        return [{"title": r["title"], "url": r["url"], "snippet": r["content"]}
                for r in response["results"]]

    Returns:
        List of dicts with keys: title, url, snippet
    """
    # Curated realistic results for common Indian tech hubs.
    # These are real companies — no fake data.
    _mock_db: Dict[str, List[Dict[str, str]]] = {
        "SaaS": [
            {
                "title": "Druva — Cloud Data Protection & Management",
                "url": "https://www.druva.com",
                "snippet": "Druva delivers data protection and management for the cloud era. "
                           "Headquartered in Pune, backed by $328M+ in funding.",
            },
            {
                "title": "Zensar Technologies — Digital Solutions & Technology Services",
                "url": "https://www.zensar.com",
                "snippet": "Zensar Technologies is a leading digital solutions and technology "
                           "services company based in Pune, part of the RPG Group.",
            },
        ],
        "FinTech": [
            {
                "title": "BillDesk — Online Payment Gateway",
                "url": "https://www.billdesk.com",
                "snippet": "BillDesk is one of India's largest payment gateways, processing "
                           "billions in transactions. Based in Pune/Mumbai.",
            },
        ],
        "HealthTech": [
            {
                "title": "CrelioHealth — Diagnostic Lab Software",
                "url": "https://www.creliohealth.com",
                "snippet": "CrelioHealth offers cloud-based diagnostic and lab information "
                           "management software, headquartered in Pune.",
            },
        ],
        "EdTech": [
            {
                "title": "Imarticus Learning — Professional Education",
                "url": "https://imarticus.org",
                "snippet": "Imarticus Learning provides professional education in finance, "
                           "analytics, and technology with centers across India.",
            },
        ],
        "IT Services": [
            {
                "title": "Persistent Systems — Product Engineering",
                "url": "https://www.persistent.com",
                "snippet": "Persistent Systems is a global solutions engineering company "
                           "headquartered in Pune with 23,000+ employees.",
            },
            {
                "title": "Cybage Software — Technology Consulting",
                "url": "https://www.cybage.com",
                "snippet": "Cybage is a technology consulting firm based in Pune with "
                           "6,000+ employees serving Fortune 500 clients.",
            },
            {
                "title": "KPIT Technologies — Automotive Software",
                "url": "https://www.kpit.com",
                "snippet": "KPIT Technologies specializes in automotive software solutions, "
                           "headquartered in Pune, listed on BSE/NSE.",
            },
        ],
        "E-commerce": [
            {
                "title": "Firstcry — Baby & Kids Products",
                "url": "https://www.firstcry.com",
                "snippet": "Firstcry is Asia's largest online store for baby and kids products, "
                           "headquartered in Pune. Backed by SoftBank.",
            },
        ],
        "Enterprise Tech": [
            {
                "title": "Pubmatic — Digital Advertising Technology",
                "url": "https://www.pubmatic.com",
                "snippet": "PubMatic is a sell-side advertising platform, NASDAQ-listed, "
                           "with a major engineering center in Pune.",
            },
        ],
        "Logistics Tech": [
            {
                "title": "ElasticRun — Technology-driven Last-mile Logistics",
                "url": "https://www.elastic.run",
                "snippet": "ElasticRun leverages technology for last-mile delivery and FMCG "
                           "distribution, headquartered in Pune. Series E funded.",
            },
        ],
    }

    results: List[Dict[str, str]] = []
    for industry, items in _mock_db.items():
        if industry.lower() in query.lower() or not any(
            ind.lower() in query.lower() for ind in TARGET_INDUSTRIES
        ):
            results.extend(items)

    return results[:num_results]


def _is_excluded(title: str, snippet: str) -> bool:
    """
    Check whether a search result should be excluded because it looks
    like a small local business rather than a scalable company.

    We do a case-insensitive check against the exclusion keyword list.
    """
    combined = f"{title} {snippet}".lower()
    return any(kw in combined for kw in EXCLUSION_KEYWORDS)


def _extract_company_name(title: str) -> str:
    """
    Best-effort extraction of a clean company name from a search result title.
    Strips trailing descriptors like "— Cloud Data Protection & Management".
    """
    # Split on common title separators and take the first part.
    for sep in [" — ", " - ", " | ", " · ", " – "]:
        if sep in title:
            return title.split(sep)[0].strip()
    return title.strip()


def search_companies(
    region: str,
    industries: Optional[List[str]] = None,
) -> List[Dict[str, str]]:
    """
    Search for companies in `region` across the given industry verticals.

    Args:
        region:     Target geographic region (e.g. "Pune", "Bengaluru").
        industries: Override list of industries to search. Defaults to
                    TARGET_INDUSTRIES.

    Returns:
        De-duplicated list of candidate dicts:
            {"name": str, "website": str, "industry": str, "snippet": str}
    """
    if industries is None:
        industries = TARGET_INDUSTRIES

    seen_urls: set = set()
    candidates: List[Dict[str, str]] = []

    for industry in industries:
        query = f"{industry} companies in {region}"
        logger.info("Searching: %s", query)

        raw_results = _mock_web_search(query)

        for result in raw_results:
            url = result.get("url", "").rstrip("/").lower()
            title = result.get("title", "")
            snippet = result.get("snippet", "")

            # Skip duplicates (same domain already seen).
            if url in seen_urls:
                continue

            # Skip small local businesses.
            if _is_excluded(title, snippet):
                logger.debug("Excluded (local business): %s", title)
                continue

            seen_urls.add(url)
            candidates.append({
                "name": _extract_company_name(title),
                "website": result["url"],
                "industry": industry,
                "snippet": snippet,
            })

    logger.info("Found %d unique candidates in %s", len(candidates), region)
    return candidates
