"""
context_agent.py — Context Hunter Agent
Collects external signals.
"""

from company_discovery.search import search_web
from company_discovery.intelligence import _detect_trigger_events, _detect_growth_signals

def run_context_hunter(domain: str, raw_text: str = "") -> list:
    """
    Find why-now signals (expansion, hiring, funding, etc).
    """
    signals = _detect_trigger_events(raw_text) + _detect_growth_signals(raw_text)
    
    # Try web search for news
    news_results = search_web(f"{domain} news funding expansion", num_results=3)
    for r in news_results:
        snippet = r.get("snippet", "").lower()
        if "funding" in snippet or "raised" in snippet:
            signals.append("Funding announcement detected in recent news")
        if "expand" in snippet or "new office" in snippet:
            signals.append("Expansion news detected")
            
    # Unique signals
    signals = list(set(signals))
    
    if not signals:
        signals.append("Stable operations (no acute trigger events detected)")
        
    return signals
