"""
scraper.py — Homepage Signal Extraction
=========================================
Fetches a company's homepage and extracts indirect revenue signals
using requests + BeautifulSoup.

Reasoning:
  We never try to find exact revenue figures (they're rarely public).
  Instead, we look for *proxy signals* that correlate with scale:
    - Hiring pages → company is growing and investing in people.
    - Funding mentions → external validation of business viability.
    - Team size → larger teams correlate with higher revenue.
    - Enterprise clients → B2B at scale implies significant contracts.
    - Years in operation → longevity suggests sustainable revenue.
    - Multi-location → geographic spread implies scale.
    - Press mentions → media coverage correlates with visibility/scale.
"""

import logging
import re
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
REQUEST_TIMEOUT: int = 15  # seconds
USER_AGENT: str = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# ---------------------------------------------------------------------------
# Signal-specific keyword / pattern banks
# ---------------------------------------------------------------------------

# Careers / hiring page link patterns
CAREERS_PATTERNS: List[str] = [
    "careers", "jobs", "hiring", "work with us", "join us",
    "join our team", "open positions", "work-with-us", "join-us",
    "openings", "vacancies",
]

# Funding-related keywords
FUNDING_KEYWORDS: List[str] = [
    "funded", "raised", "series a", "series b", "series c", "series d",
    "series e", "series f", "seed round", "pre-seed", "angel round",
    "venture capital", "vc backed", "investment", "investor",
    "million funding", "crore funding", "fundraise",
    "sequoia", "accel", "tiger global", "softbank", "a16z",
    "lightspeed", "matrix partners", "nexus venture",
]

# Team size indicator patterns
TEAM_SIZE_PATTERNS: List[str] = [
    r"\d{2,}[\+]?\s*(?:employees|team members|people|engineers|professionals)",
    r"team\s+of\s+\d{2,}",
    r"\d{2,}\+?\s*(?:strong|member)",
    r"(?:over|more than)\s+\d{2,}\s+(?:employees|people|team)",
    r"\d{3,}\+?\s+(?:globally|worldwide|across)",
]

# Enterprise client keywords
ENTERPRISE_KEYWORDS: List[str] = [
    "trusted by", "our clients", "our customers", "client logos",
    "fortune 500", "fortune 100", "enterprise", "global brands",
    "leading companies", "partners include", "customers include",
    "microsoft", "google", "amazon", "ibm", "oracle", "cisco",
    "walmart", "deloitte", "accenture", "infosys", "tcs",
    "wipro", "samsung", "hp", "dell", "intel", "salesforce",
]

# Years in operation patterns
YEARS_PATTERNS: List[str] = [
    r"(?:founded|established|since|started)\s*(?:in\s+)?\d{4}",
    r"\d{1,2}\+?\s*years\s+(?:of\s+)?(?:experience|expertise|in operation|in business)",
    r"(?:over|more than)\s+\d{1,2}\s+years",
    r"since\s+\d{4}",
]

# Multi-location keywords
LOCATION_KEYWORDS: List[str] = [
    "offices in", "locations in", "headquartered",
    "global presence", "worldwide", "across countries",
    "multiple offices", "branches in", "centers in",
    "usa", "uk", "europe", "asia pacific", "apac",
    "north america", "global offices", "international",
    "new york", "london", "singapore", "san francisco",
    "bangalore", "bengaluru", "mumbai", "hyderabad", "delhi",
]

# Press mention keywords
PRESS_KEYWORDS: List[str] = [
    "featured in", "as seen on", "in the news", "press",
    "media coverage", "mentioned in", "covered by",
    "forbes", "techcrunch", "bloomberg", "reuters",
    "economic times", "mint", "business standard",
    "yourstory", "inc42", "moneycontrol", "cnbc",
    "the hindu", "times of india", "ndtv", "bbc",
    "wall street journal", "wired", "venturebeat",
]


# ═══════════════════════════════════════════════════════════════════════════
#  Core Scraping Engine
# ═══════════════════════════════════════════════════════════════════════════

def _fetch_page(url: str) -> Optional[BeautifulSoup]:
    """
    Fetch and parse a webpage. Returns a BeautifulSoup object or None on error.
    Handles common failure modes gracefully so one bad URL doesn't crash
    the entire pipeline.
    """
    try:
        headers = {"User-Agent": USER_AGENT}
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT,
                                allow_redirects=True, verify=True)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
    except requests.exceptions.SSLError:
        # Retry without SSL verification for sites with cert issues.
        try:
            response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT,
                                    allow_redirects=True, verify=False)
            return BeautifulSoup(response.text, "html.parser")
        except Exception as e:
            logger.warning("SSL fallback failed for %s: %s", url, e)
            return None
    except requests.exceptions.RequestException as e:
        logger.warning("Failed to fetch %s: %s", url, e)
        return None


def _check_hiring_page(soup: BeautifulSoup, base_url: str) -> Dict[str, Any]:
    """
    Signal 1: Hiring page presence.

    A dedicated careers/jobs page suggests the company is actively investing
    in headcount, which correlates with revenue growth.
    """
    found_links: List[str] = []
    all_links = soup.find_all("a", href=True)

    for link in all_links:
        href = link["href"].lower()
        text = link.get_text(strip=True).lower()
        combined = f"{href} {text}"

        if any(pattern in combined for pattern in CAREERS_PATTERNS):
            full_url = urljoin(base_url, link["href"])
            found_links.append(full_url)

    detected = len(found_links) > 0
    return {
        "detected": detected,
        "details": f"Found {len(found_links)} career-related link(s)"
                   if detected else "No careers/hiring page found",
    }


def _check_funding_mentions(soup: BeautifulSoup) -> Dict[str, Any]:
    """
    Signal 2: Funding mentions.

    References to fundraising rounds, VC firms, or investment amounts
    indicate external validation and financial backing — strong revenue proxy.
    """
    page_text = soup.get_text(separator=" ").lower()
    found: List[str] = []

    for keyword in FUNDING_KEYWORDS:
        if keyword in page_text:
            found.append(keyword)

    detected = len(found) > 0
    return {
        "detected": detected,
        "details": f"Funding signals: {', '.join(found[:5])}"
                   if detected else "No funding mentions found",
    }


def _check_team_size(soup: BeautifulSoup) -> Dict[str, Any]:
    """
    Signal 3: Team size indicators.

    Companies mentioning large team sizes (50+, 200+, 1000+) are more
    likely to have significant revenue to support payroll.
    """
    page_text = soup.get_text(separator=" ").lower()
    matches: List[str] = []

    for pattern in TEAM_SIZE_PATTERNS:
        regex_matches = re.findall(pattern, page_text, re.IGNORECASE)
        matches.extend(regex_matches)

    detected = len(matches) > 0
    return {
        "detected": detected,
        "details": f"Team indicators: {', '.join(matches[:3])}"
                   if detected else "No team size indicators found",
    }


def _check_enterprise_clients(soup: BeautifulSoup) -> Dict[str, Any]:
    """
    Signal 4: Enterprise client presence.

    Mentions of Fortune 500 companies or large brand logos suggest the
    company operates at enterprise scale with substantial contract values.
    """
    page_text = soup.get_text(separator=" ").lower()
    found: List[str] = []

    for keyword in ENTERPRISE_KEYWORDS:
        if keyword in page_text:
            found.append(keyword)

    detected = len(found) >= 2  # Require at least 2 enterprise signals.
    return {
        "detected": detected,
        "details": f"Enterprise signals: {', '.join(found[:5])}"
                   if detected else "No enterprise client signals found",
    }


def _check_years_in_operation(soup: BeautifulSoup) -> Dict[str, Any]:
    """
    Signal 5: Years in operation.

    Companies operating for 5+ years have demonstrated sustainable revenue.
    We extract founding year mentions and compute tenure.
    """
    page_text = soup.get_text(separator=" ").lower()
    matches: List[str] = []

    for pattern in YEARS_PATTERNS:
        regex_matches = re.findall(pattern, page_text, re.IGNORECASE)
        matches.extend(regex_matches)

    detected = len(matches) > 0
    return {
        "detected": detected,
        "details": f"Longevity indicators: {', '.join(matches[:3])}"
                   if detected else "No years-in-operation signals found",
    }


def _check_multi_location(soup: BeautifulSoup) -> Dict[str, Any]:
    """
    Signal 6: Multi-location presence.

    Companies with offices in multiple cities / countries have scaled
    beyond a single market, implying higher revenue.
    """
    page_text = soup.get_text(separator=" ").lower()
    found: List[str] = []

    for keyword in LOCATION_KEYWORDS:
        if keyword in page_text:
            found.append(keyword)

    # Require 3+ location signals to avoid false positives from a single
    # "headquartered in X" mention.
    detected = len(found) >= 3
    return {
        "detected": detected,
        "details": f"Location signals: {', '.join(found[:5])}"
                   if detected else "No multi-location signals found",
    }


def _check_press_mentions(soup: BeautifulSoup) -> Dict[str, Any]:
    """
    Signal 7: Press / media mentions.

    Coverage in reputable outlets (Forbes, TechCrunch, ET, etc.) indicates
    the company has public visibility and is likely at material scale.
    """
    page_text = soup.get_text(separator=" ").lower()
    found: List[str] = []

    for keyword in PRESS_KEYWORDS:
        if keyword in page_text:
            found.append(keyword)

    detected = len(found) > 0
    return {
        "detected": detected,
        "details": f"Press signals: {', '.join(found[:5])}"
                   if detected else "No press/media mentions found",
    }


# ═══════════════════════════════════════════════════════════════════════════
#  Public API
# ═══════════════════════════════════════════════════════════════════════════

def scrape_signals(website_url: str) -> Dict[str, Dict[str, Any]]:
    """
    Scrape a company's homepage and extract 7 revenue-proxy signals.

    Args:
        website_url: Full URL of the company homepage.

    Returns:
        Dict mapping signal names to their extraction results:
        {
            "hiring_page":        {"detected": bool, "details": str},
            "funding_mentions":   {"detected": bool, "details": str},
            "team_size":          {"detected": bool, "details": str},
            "enterprise_clients": {"detected": bool, "details": str},
            "years_in_operation": {"detected": bool, "details": str},
            "multi_location":     {"detected": bool, "details": str},
            "press_mentions":     {"detected": bool, "details": str},
        }

        If the page cannot be fetched, all signals default to not detected.
    """
    logger.info("Scraping signals from: %s", website_url)

    # Default result — all signals negative (safe fallback).
    default_result = {
        signal: {"detected": False, "details": "Page could not be fetched"}
        for signal in [
            "hiring_page", "funding_mentions", "team_size",
            "enterprise_clients", "years_in_operation",
            "multi_location", "press_mentions",
        ]
    }

    soup = _fetch_page(website_url)
    if soup is None:
        logger.warning("Could not fetch %s — returning default signals", website_url)
        return default_result

    return {
        "hiring_page":        _check_hiring_page(soup, website_url),
        "funding_mentions":   _check_funding_mentions(soup),
        "team_size":          _check_team_size(soup),
        "enterprise_clients": _check_enterprise_clients(soup),
        "years_in_operation": _check_years_in_operation(soup),
        "multi_location":     _check_multi_location(soup),
        "press_mentions":     _check_press_mentions(soup),
    }
