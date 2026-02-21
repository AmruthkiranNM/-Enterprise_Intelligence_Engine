"""
signals.py — Consolidated Signal Extraction
=============================================
Thin wrapper around scraper.py that exposes a clean signal summary
for both Region and Domain pipelines.

The scraper does the heavy lifting (fetching + parsing). This module
provides:
  - extract_signals()  → dict of detected/not-detected per signal type
  - summarize_signals() → flat list of detected signal descriptions
"""

import logging
from typing import Dict, Any, List

from company_discovery.scraper import scrape_signals

logger = logging.getLogger(__name__)


def extract_signals(website_url: str) -> Dict[str, Dict[str, Any]]:
    """
    Extract all 7 revenue-proxy signals from a company's homepage.
    Delegates to scraper.scrape_signals() — this function exists
    so that other modules import from signals.py, not scraper.py directly.
    """
    return scrape_signals(website_url)


def summarize_signals(signals: Dict[str, Dict[str, Any]]) -> List[str]:
    """
    Return a flat list of human-readable descriptions for
    all detected signals. Used for output formatting.
    """
    return [
        result["details"]
        for result in signals.values()
        if result.get("detected", False)
    ]


def count_positive_signals(signals: Dict[str, Dict[str, Any]]) -> int:
    """Count how many signals were detected."""
    return sum(1 for r in signals.values() if r.get("detected", False))
