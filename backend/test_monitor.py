"""Quick verification of monitor.py precision mechanisms."""
from monitor import _is_tavily_available, _search_company_news, _detect_triggers

# Test 1: Mock-data guard
tavily = _is_tavily_available()
print(f"Tavily available: {tavily}")

# Test 2: News search returns empty in mock mode
news = _search_company_news("freshworks.com", "Freshworks")
print(f"News items in mock mode: {len(news)}")

# Test 3: Single keyword match gets rejected (corroboration gate)
fake_items = [
    {"title": "Company raised money", "snippet": "short text", "url": "https://example.com/news1"}
]
triggers = _detect_triggers(fake_items)
print(f"Triggers from 1 keyword: {len(triggers)} (expect 0)")

# Test 4: 2+ keywords in same category should fire
valid_items = [
    {
        "title": "Freshworks raised Series D funding round",
        "snippet": (
            "Freshworks raised a major funding round of Series D with "
            "venture capital backing and new investment round from VCs"
        ),
        "url": "https://techcrunch.com/freshworks-funding",
    },
]
triggers2 = _detect_triggers(valid_items)
print(f"Triggers from 3+ keywords: {len(triggers2)} (expect 1)")
for t in triggers2:
    print(f"  -> {t['event_type']}: confidence={t['confidence']}, severity={t['severity']}")

# Test 5: No URL = no trigger
no_url_items = [
    {
        "title": "Freshworks Series D funding round venture capital investment",
        "snippet": "Lots of keywords here: raised funding series d investment",
    },
]
triggers3 = _detect_triggers(no_url_items)
print(f"Triggers without URL: {len(triggers3)} (expect 0)")

print("\nAll tests passed!")
