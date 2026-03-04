"""
discovery_agent.py — Dual Mode Discovery
Wraps existing search logic. Supports:
1. Domain Search
2. Regional Search
"""

import logging
from company_discovery.search import search_companies, USE_TAVILY, _real_web_search

logger = logging.getLogger(__name__)

def discover_prospects(mode: str, query: str = None, region: str = None) -> list:
    """
    mode: "domain" or "region"
    """
    if mode == "domain":
        if not query:
            return []
        logger.info(f"Domain Search: '{query}'")
        
        results = []
        if USE_TAVILY:
            raw = _real_web_search(query, max_results=10)
            for r in raw:
                # Add formatting
                results.append({
                    "name": r.get("title", "").split()[0] if r.get("title") else "Unknown",
                    "website": r.get("url", ""),
                    "snippet": r.get("snippet", "")
                })
        else:
            # Mock fallback for domain mode
            results = [
                {"name": "Postman", "website": "https://postman.com", "snippet": "API Platform"},
                {"name": "BrowserStack", "website": "https://browserstack.com", "snippet": "Software testing platform"}
            ]
        return results
        
    elif mode == "region":
        if not region:
            return []
        logger.info(f"Regional Search: '{region}'")
        return search_companies(region)
    
    return []
