"""
search.py — Production-Grade Region-Aware Company Discovery
============================================================

Uses Tavily API to discover REAL company websites
headquartered in a specified region.

Features:
- Strict region validation
- Blocks aggregators and listing pages
- Blocks blogs and directory sites
- Filters small local businesses
- Returns only likely company homepages
"""

import os
import logging
from typing import List, Dict, Optional
from urllib.parse import urlparse
from tavily import TavilyClient

logger = logging.getLogger(__name__)

# ────────────────────────────────────────────────────────────────
# Tavily Setup
# ────────────────────────────────────────────────────────────────
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
if not TAVILY_API_KEY:
    raise ValueError("TAVILY_API_KEY environment variable not set.")

tavily = TavilyClient(api_key=TAVILY_API_KEY)

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
    logger.info("Tavily search: %s", query)

    response = tavily.search(
        query=query,
        max_results=max_results,
        search_depth="advanced"
    )

    return response.get("results", [])


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

        results = _real_web_search(query)

        for r in results:
            title = r.get("title", "")
            url = r.get("url", "")
            snippet = r.get("content", "")

            if not url:
                continue

            domain = _extract_domain(url)

            # Skip duplicates
            if domain in seen_domains:
                continue

            # Only allow homepage URLs
            if not _is_homepage(url):
                continue

            # Block aggregator / listing pages
            if _is_aggregator(title, url):
                continue

            # Block small local businesses
            if _is_excluded(title, snippet):
                continue

            # Strict region validation
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
        "Found %d validated companies in %s",
        len(candidates), region
    )

    return candidates