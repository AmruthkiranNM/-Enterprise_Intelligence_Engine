"""
search.py — Region-Aware Company Discovery
==========================================

Uses Tavily API when available; falls back to a region-keyed mock DB
so the pipeline works without an API key.

Key fixes:
- Mock data is keyed by REGION, not industry — returns the right companies
  for the searched city/region.
- Tavily queries are strengthened to force region name in the search string.
- Region validation requires the region name to appear in company info,
  with multiple checks (title, snippet, URL) for better coverage.
- Query now uses multiple targeted formulations to maximize hit rate.
"""

import os
import logging
from typing import List, Dict, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# ── Tavily Setup ──────────────────────────────────────────────────────────────
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

# ── Target Industries ─────────────────────────────────────────────────────────
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

# ── Exclusion Keywords ────────────────────────────────────────────────────────
EXCLUSION_KEYWORDS = [
    "restaurant", "cafe", "bakery", "salon", "spa",
    "grocery", "kirana", "dhaba", "tailor",
]

# ── Blocked Aggregators ───────────────────────────────────────────────────────
BLOCKED_DOMAINS = [
    "linkedin.com", "ycombinator.com", "crunchbase.com",
    "glassdoor.com", "builtin", "angel.co", "medium.com",
    "wordpress.com", "blogspot.com", "leadsquared.com", "indeed.com",
    "ambitionbox.com", "naukri.com", "justdial.com", "sulekha.com",
    "clutch.co", "goodfirms.com", "tracxn.com",
]

BLOCKED_TITLE_KEYWORDS = [
    "top ", "best ", "list of", "companies in", "startups in",
    "directory", "funded by", "industry report", "article", "blog",
    "ranking", "review of",
]

# ── Region-keyed Mock Database ────────────────────────────────────────────────
# Each top-level key is a lowercase city/region name.
# Companies are real, publicly known firms headquartered in that region.
_REGION_MOCK_DB: Dict[str, List[Dict[str, str]]] = {

    "pune": [
        {"name": "Druva",             "website": "https://www.druva.com",       "industry": "SaaS",          "snippet": "Druva delivers cloud data protection headquartered in Pune. $475M raised, $2B valuation."},
        {"name": "Persistent Systems","website": "https://www.persistent.com",  "industry": "IT Services",   "snippet": "Persistent Systems is a global product-engineering company headquartered in Pune with 23,000+ employees."},
        {"name": "KPIT Technologies", "website": "https://www.kpit.com",        "industry": "Enterprise Tech","snippet": "KPIT Technologies specializes in automotive software, headquartered in Pune, listed on BSE/NSE."},
        {"name": "Cybage Software",   "website": "https://www.cybage.com",      "industry": "IT Services",   "snippet": "Technology consulting firm based in Pune with 6,000+ employees serving Fortune 500 clients."},
        {"name": "Firstcry",          "website": "https://www.firstcry.com",    "industry": "E-commerce",    "snippet": "Asia's largest online store for baby products, headquartered in Pune. Backed by SoftBank."},
        {"name": "ElasticRun",        "website": "https://www.elastic.run",     "industry": "Logistics Tech","snippet": "Technology-driven last-mile logistics company headquartered in Pune. Series E funded."},
        {"name": "PubMatic",          "website": "https://www.pubmatic.com",    "industry": "Enterprise Tech","snippet": "NASDAQ-listed sell-side advertising platform with a major engineering center in Pune."},
        {"name": "CrelioHealth",      "website": "https://www.creliohealth.com","industry": "HealthTech",    "snippet": "Cloud-based diagnostic lab software headquartered in Pune."},
        {"name": "Zensar Technologies","website":"https://www.zensar.com",      "industry": "IT Services",   "snippet": "Digital solutions and technology services company based in Pune, part of the RPG Group."},
        {"name": "BillDesk",          "website": "https://www.billdesk.com",    "industry": "FinTech",       "snippet": "India's largest payment gateway processing billions in transactions, based in Pune/Mumbai."},
    ],

    "bangalore": [
        {"name": "Infosys",           "website": "https://www.infosys.com",     "industry": "IT Services",   "snippet": "Global IT services leader headquartered in Bangalore, India. Revenue $18B+ annually."},
        {"name": "Wipro",             "website": "https://www.wipro.com",       "industry": "IT Services",   "snippet": "Wipro is a global IT, consulting and BPO services company headquartered in Bangalore."},
        {"name": "Flipkart",          "website": "https://www.flipkart.com",    "industry": "E-commerce",    "snippet": "India's leading e-commerce marketplace headquartered in Bangalore, owned by Walmart."},
        {"name": "Swiggy",            "website": "https://www.swiggy.com",      "industry": "Logistics Tech","snippet": "On-demand food delivery platform headquartered in Bangalore. Series J funded, IPO filed."},
        {"name": "Zerodha",           "website": "https://zerodha.com",         "industry": "FinTech",       "snippet": "India's largest retail stockbroker by active clients, headquartered in Bangalore."},
        {"name": "Razorpay",          "website": "https://razorpay.com",        "industry": "FinTech",       "snippet": "Payment solutions platform for businesses headquartered in Bangalore. Valued at $7.5B."},
        {"name": "Unacademy",         "website": "https://unacademy.com",       "industry": "EdTech",        "snippet": "Online learning platform headquartered in Bangalore, serving millions of students across India."},
        {"name": "PhonePe",           "website": "https://www.phonepe.com",     "industry": "FinTech",       "snippet": "UPI-based digital payments platform headquartered in Bangalore, processing 5B+ transactions monthly."},
        {"name": "BrowserStack",      "website": "https://www.browserstack.com","industry": "SaaS",          "snippet": "Cloud testing platform headquartered in Bangalore with 50,000+ enterprises. $200M raised."},
        {"name": "Ola",               "website": "https://www.olacabs.com",     "industry": "Logistics Tech","snippet": "Ride-hailing and EV company headquartered in Bangalore, operating across India and international markets."},
    ],

    "bengaluru": [  # alias
        {"name": "Infosys",           "website": "https://www.infosys.com",     "industry": "IT Services",   "snippet": "Global IT services leader headquartered in Bengaluru, India. Revenue $18B+ annually."},
        {"name": "Wipro",             "website": "https://www.wipro.com",       "industry": "IT Services",   "snippet": "Global IT, consulting and BPO services company headquartered in Bengaluru."},
        {"name": "Flipkart",          "website": "https://www.flipkart.com",    "industry": "E-commerce",    "snippet": "India's leading e-commerce marketplace headquartered in Bengaluru, owned by Walmart."},
        {"name": "Swiggy",            "website": "https://www.swiggy.com",      "industry": "Logistics Tech","snippet": "On-demand food delivery platform headquartered in Bengaluru. IPO filed."},
        {"name": "Razorpay",          "website": "https://razorpay.com",        "industry": "FinTech",       "snippet": "Payment solutions platform for businesses headquartered in Bengaluru. Valued at $7.5B."},
        {"name": "BrowserStack",      "website": "https://www.browserstack.com","industry": "SaaS",          "snippet": "Cloud testing platform headquartered in Bengaluru with 50,000+ enterprise customers."},
        {"name": "PhonePe",           "website": "https://www.phonepe.com",     "industry": "FinTech",       "snippet": "UPI-based digital payments platform headquartered in Bengaluru."},
        {"name": "Zerodha",           "website": "https://zerodha.com",         "industry": "FinTech",       "snippet": "India's largest retail stockbroker by active clients, based in Bengaluru."},
    ],

    "mumbai": [
        {"name": "Nykaa",             "website": "https://www.nykaa.com",       "industry": "E-commerce",    "snippet": "Omnichannel beauty retailer headquartered in Mumbai, listed on NSE/BSE."},
        {"name": "Tata Consultancy Services","website":"https://www.tcs.com",   "industry": "IT Services",   "snippet": "TCS is the world's second-largest IT services firm, headquartered in Mumbai. $27B+ revenue."},
        {"name": "HDFC Bank",         "website": "https://www.hdfcbank.com",    "industry": "FinTech",       "snippet": "India's largest private sector bank headquartered in Mumbai, serving 80M+ customers."},
        {"name": "Meesho",            "website": "https://www.meesho.com",      "industry": "E-commerce",    "snippet": "Social commerce platform for small businesses headquartered in Mumbai. Series F funded."},
        {"name": "Piramal Pharma",    "website": "https://www.piramal.com",     "industry": "HealthTech",    "snippet": "Global pharmaceutical company headquartered in Mumbai with a major healthcare division."},
        {"name": "Mahindra Logistics","website": "https://www.mahindralogistics.com","industry":"Logistics Tech","snippet":"Third-party logistics provider headquartered in Mumbai, serving 400+ enterprise clients."},
        {"name": "PolicyBazaar",      "website": "https://www.policybazaar.com","industry": "FinTech",       "snippet": "India's largest insurance aggregator, co-headquartered in Mumbai. NASDAQ listed."},
        {"name": "BookMyShow",        "website": "https://in.bookmyshow.com",   "industry": "Enterprise Tech","snippet": "Entertainment ticketing platform headquartered in Mumbai with 70M+ registered users."},
    ],

    "hyderabad": [
        {"name": "Cyient",            "website": "https://www.cyient.com",      "industry": "IT Services",   "snippet": "Engineering and technology solutions company headquartered in Hyderabad. Listed on NSE."},
        {"name": "Infotech Enterprises","website":"https://www.info.com",       "industry": "IT Services",   "snippet": "IT services company headquartered in Hyderabad serving global aviation and defense clients."},
        {"name": "HealthifyMe",       "website": "https://www.healthifyme.com", "industry": "HealthTech",    "snippet": "AI-powered health and fitness platform headquartered in Hyderabad. Series C funded."},
        {"name": "Darwinbox",         "website": "https://darwinbox.com",       "industry": "SaaS",          "snippet": "Enterprise HR technology platform headquartered in Hyderabad. 700+ enterprise clients globally."},
        {"name": "NuSummit",          "website": "https://www.nusummit.com",    "industry": "Enterprise Tech","snippet": "Technology consulting firm headquartered in Hyderabad serving Fortune 1000 enterprises."},
        {"name": "Intelenet Global",  "website": "https://www.intelenetglobal.com","industry":"IT Services",  "snippet": "BPO and IT services firm headquartered in Hyderabad serving global financial institutions."},
    ],

    "delhi": [
        {"name": "Paytm",             "website": "https://paytm.com",           "industry": "FinTech",       "snippet": "India's leading digital payments and financial services company, headquartered in Delhi NCR."},
        {"name": "Zomato",            "website": "https://www.zomato.com",      "industry": "Logistics Tech","snippet": "Food delivery and restaurant discovery platform headquartered in Delhi NCR. Listed on NSE/BSE."},
        {"name": "IndiaMart",         "website": "https://www.indiamart.com",   "industry": "E-commerce",    "snippet": "India's largest B2B online marketplace headquartered in Delhi NCR. NSE listed."},
        {"name": "Info Edge",         "website": "https://www.infoedge.in",     "industry": "Enterprise Tech","snippet": "Internet holding company (Naukri, 99acres, Jeevansathi) headquartered in Delhi NCR."},
        {"name": "UpGrad",            "website": "https://www.upgrad.com",      "industry": "EdTech",        "snippet": "Online higher education platform headquartered in Delhi/Mumbai. $1.2B valuation."},
        {"name": "Cars24",            "website": "https://www.cars24.com",      "industry": "E-commerce",    "snippet": "Used car e-commerce platform headquartered in Delhi NCR. Unicorn-valued, operates in 12 countries."},
    ],

    "chennai": [
        {"name": "Freshworks",        "website": "https://www.freshworks.com",  "industry": "SaaS",          "snippet": "Cloud-based CRM and customer support SaaS company originally headquartered in Chennai. NASDAQ listed."},
        {"name": "Zoho Corporation",  "website": "https://www.zoho.com",        "industry": "SaaS",          "snippet": "Global SaaS company headquartered in Chennai offering 50+ business applications. 100M+ users."},
        {"name": "Hexaware Technologies","website":"https://hexaware.com",      "industry": "IT Services",   "snippet": "IT and BPO services firm headquartered in Chennai. 30,000+ employees globally."},
        {"name": "Ramco Systems",     "website": "https://www.ramco.com",       "industry": "Enterprise Tech","snippet": "Enterprise cloud ERP platform headquartered in Chennai serving aviation, HR, and logistics."},
        {"name": "Verizon India Hub", "website": "https://www.verizon.com/business","industry":"Enterprise Tech","snippet":"Major Verizon business services engineering center headquartered in Chennai."},
    ],

    "kolkata": [
        {"name": "ITC Infotech",      "website": "https://www.itcinfotech.com", "industry": "IT Services",   "snippet": "IT services subsidiary of ITC Limited headquartered in Kolkata, serving global clients."},
        {"name": "Webel Technology",  "website": "https://www.webel.in",        "industry": "Enterprise Tech","snippet": "West Bengal government's IT company headquartered in Kolkata providing enterprise tech solutions."},
        {"name": "Tata Steel Digital","website": "https://www.tatasteel.com",   "industry": "Enterprise Tech","snippet": "Tata Steel's digital and technology division with operations centered in Kolkata."},
    ],

    "ahmedabad": [
        {"name": "Adani Group Tech",  "website": "https://www.adanienterprises.com","industry":"Enterprise Tech","snippet":"Adani Group's digital and enterprise technology arm headquartered in Ahmedabad."},
        {"name": "iNube Software",    "website": "https://www.inubesolutions.com","industry": "SaaS",         "snippet": "Insurance technology SaaS company headquartered in Ahmedabad serving 50+ insurers."},
        {"name": "Torrent Pharma Digital","website":"https://www.torrentpharma.com","industry":"HealthTech", "snippet": "Technology and digital division of Torrent Pharmaceuticals, based in Ahmedabad."},
    ],

    "noida": [
        {"name": "HCL Technologies",  "website": "https://www.hcltech.com",     "industry": "IT Services",   "snippet": "Global IT services company headquartered in Noida with $12B+ revenue and 220,000+ employees."},
        {"name": "Sapient Corporation","website":"https://www.publicissapient.com","industry":"IT Services",  "snippet": "Technology and management consulting firm (Publicis Sapient) with a major Noida center."},
        {"name": "Adobe India R&D",   "website": "https://www.adobe.com",       "industry": "Enterprise Tech","snippet": "Adobe's India Research & Development center and major engineering hub located in Noida."},
    ],

    "gurgaon": [
        {"name": "MakeMyTrip",        "website": "https://www.makemytrip.com",  "industry": "E-commerce",    "snippet": "Online travel platform headquartered in Gurgaon. NASDAQ listed, 40M+ customers."},
        {"name": "DLF Cyber City Tech","website":"https://www.dlf.in",          "industry": "Enterprise Tech","snippet": "DLF's technology and digital services division operating from Gurgaon."},
        {"name": "Housing.com",       "website": "https://housing.com",         "industry": "E-commerce",    "snippet": "Real estate search platform headquartered in Gurgaon serving 15M+ monthly users."},
        {"name": "InMobi",            "website": "https://www.inmobi.com",      "industry": "Enterprise Tech","snippet": "Global mobile advertising and marketing platform headquartered in Gurgaon. Unicorn-valued."},
    ],

    "gurugram": [  # alias for gurgaon
        {"name": "MakeMyTrip",        "website": "https://www.makemytrip.com",  "industry": "E-commerce",    "snippet": "Online travel platform headquartered in Gurugram. NASDAQ listed."},
        {"name": "InMobi",            "website": "https://www.inmobi.com",      "industry": "Enterprise Tech","snippet": "Global mobile advertising platform headquartered in Gurugram. Unicorn-valued."},
        {"name": "Housing.com",       "website": "https://housing.com",         "industry": "E-commerce",    "snippet": "Real estate platform headquartered in Gurugram."},
    ],

    # International regions
    "san francisco": [
        {"name": "Salesforce",        "website": "https://www.salesforce.com",  "industry": "SaaS",          "snippet": "World's leading CRM platform headquartered in San Francisco. $34B annual revenue."},
        {"name": "Stripe",            "website": "https://stripe.com",          "industry": "FinTech",       "snippet": "Global payments infrastructure company headquartered in San Francisco. $95B valuation."},
        {"name": "Twilio",            "website": "https://www.twilio.com",      "industry": "SaaS",          "snippet": "Cloud communications platform headquartered in San Francisco. 300,000+ enterprise customers."},
        {"name": "Cloudflare",        "website": "https://www.cloudflare.com",  "industry": "Enterprise Tech","snippet": "Web infrastructure and security company headquartered in San Francisco. $10B+ revenue run rate."},
        {"name": "Okta",              "website": "https://www.okta.com",        "industry": "SaaS",          "snippet": "Identity and access management platform headquartered in San Francisco. 18,000+ enterprise customers."},
    ],

    "new york": [
        {"name": "MongoDB",           "website": "https://www.mongodb.com",     "industry": "Enterprise Tech","snippet": "Document database platform headquartered in New York City. 44,000+ enterprise customers."},
        {"name": "Datadog",           "website": "https://www.datadoghq.com",   "industry": "SaaS",          "snippet": "Cloud monitoring and analytics platform headquartered in New York. 28,000+ customers."},
        {"name": "Etsy",              "website": "https://www.etsy.com",        "industry": "E-commerce",    "snippet": "E-commerce platform for handmade goods headquartered in Brooklyn, New York. 90M buyers."},
        {"name": "Pager Duty",        "website": "https://www.pagerduty.com",   "industry": "SaaS",          "snippet": "Digital operations management platform headquartered in New York / San Francisco."},
    ],

    "london": [
        {"name": "Revolut",           "website": "https://www.revolut.com",     "industry": "FinTech",       "snippet": "Digital banking and payments platform headquartered in London. $33B valuation. 38M+ customers."},
        {"name": "Monzo",             "website": "https://monzo.com",           "industry": "FinTech",       "snippet": "Digital bank headquartered in London with 9M+ UK customers and a US expansion underway."},
        {"name": "Darktrace",         "website": "https://www.darktrace.com",   "industry": "Enterprise Tech","snippet": "AI-powered cybersecurity platform headquartered in London / Cambridge. Listed on LSE."},
        {"name": "Deliveroo",         "website": "https://deliveroo.co.uk",     "industry": "Logistics Tech","snippet": "Food delivery platform headquartered in London, operating in 10 markets. LSE listed."},
        {"name": "Thought Machine",   "website": "https://thoughtmachine.net",  "industry": "FinTech",       "snippet": "Cloud-native banking technology firm headquartered in London. $2.7B valuation."},
    ],

    "singapore": [
        {"name": "Grab",              "website": "https://www.grab.com",        "industry": "Logistics Tech","snippet": "Southeast Asia's superapp for transport, food and finance. Headquartered in Singapore. NASDAQ listed."},
        {"name": "Sea Limited",       "website": "https://www.sea.com",         "industry": "E-commerce",    "snippet": "Consumer internet company (Shopee, SeaMoney, Garena) headquartered in Singapore. NYSE listed."},
        {"name": "Patsnap",           "website": "https://www.patsnap.com",     "industry": "SaaS",          "snippet": "IP intelligence and R&D analytics SaaS platform headquartered in Singapore. $300M raised."},
        {"name": "Nium",              "website": "https://nium.com",            "industry": "FinTech",       "snippet": "Global payments infrastructure platform headquartered in Singapore. $2.1B valuation."},
    ],
}


# ── Utility Functions ─────────────────────────────────────────────────────────

def _extract_domain(url: str) -> str:
    return urlparse(url).netloc.lower()


def _is_homepage(url: str) -> bool:
    return urlparse(url).path in ("", "/")


def _is_excluded(title: str, snippet: str) -> bool:
    combined = f"{title} {snippet}".lower()
    return any(kw in combined for kw in EXCLUSION_KEYWORDS)


def _is_aggregator(title: str, url: str) -> bool:
    t, u = title.lower(), url.lower()
    if any(d in u for d in BLOCKED_DOMAINS):
        return True
    if any(kw in t for kw in BLOCKED_TITLE_KEYWORDS):
        return True
    return False


def _region_in_text(text: str, region: str) -> bool:
    """Check if any word of the region appears in the text."""
    region_words = [w.strip() for w in region.lower().split() if len(w) > 2]
    text_lower = text.lower()
    return any(w in text_lower for w in region_words)


def _extract_company_name(title: str) -> str:
    for sep in (" — ", " - ", " | ", " · ", " – "):
        if sep in title:
            return title.split(sep)[0].strip()
    return title.strip()


# ── Live Search (Tavily) ──────────────────────────────────────────────────────

def _real_web_search(query: str, max_results: int = 10) -> List[Dict]:
    logger.info("Tavily search: %s", query)
    response = _tavily_client.search(
        query=query,
        max_results=max_results,
        search_depth="advanced",
    )
    return [
        {
            "title":   r.get("title", ""),
            "url":     r.get("url", ""),
            "snippet": r.get("content", ""),
        }
        for r in response.get("results", [])
    ]


# ── Mock Search (Region-keyed) ────────────────────────────────────────────────

def _mock_web_search(region: str, num_results: int = 10) -> List[Dict]:
    """
    Return pre-curated real companies for the requested region.
    The DB is keyed by lowercase region name for exact lookups.
    Falls back to partial match if no exact key found.
    """
    region_key = region.strip().lower()

    # Exact match
    companies = _REGION_MOCK_DB.get(region_key)

    # Partial match fallback (e.g., "Delhi NCR" → matches "delhi")
    if not companies:
        for key, items in _REGION_MOCK_DB.items():
            if key in region_key or region_key in key:
                companies = items
                logger.info("Mock DB partial match: '%s' → '%s'", region_key, key)
                break

    if not companies:
        logger.warning(
            "No mock data for region '%s'. Available regions: %s",
            region,
            ", ".join(_REGION_MOCK_DB.keys()),
        )
        return []

    return companies[:num_results]


def search_web(query: str, num_results: int = 10) -> List[Dict]:
    """Generic web search (used by intelligence module)."""
    if USE_TAVILY:
        return _real_web_search(query, max_results=num_results)
    return []


# ── Main Entry Point ──────────────────────────────────────────────────────────

def search_companies(
    region: str,
    industries: Optional[List[str]] = None,
) -> List[Dict[str, str]]:
    """
    Discover companies in the specified region.
    - If Tavily is available: runs targeted live searches per industry.
    - If not: returns pre-curated region-specific mock data.
    """
    if industries is None:
        industries = TARGET_INDUSTRIES

    # ── MOCK PATH ─────────────────────────────────────────────────────────────
    if not USE_TAVILY:
        raw = _mock_web_search(region)
        logger.info(
            "Mock mode: Returning %d pre-curated companies for region '%s'",
            len(raw), region,
        )
        return raw   # already structured as {"name", "website", "industry", "snippet"}

    # ── LIVE TAVILY PATH ──────────────────────────────────────────────────────
    seen_domains: set = set()
    candidates: List[Dict[str, str]] = []

    for industry in industries:
        # Use multiple query formulations to maximize region-specific hits
        queries = [
            f"{industry} company headquartered in {region} official website",
            f"top {industry} startup based in {region} site:linkedin.com/company",
            f"{industry} firm {region} India corporate website",
        ]

        for query in queries[:2]:   # Use top 2 query formulations
            raw_results = _real_web_search(query, max_results=8)

            for r in raw_results:
                title   = r.get("title", "")
                url     = r.get("url", "")
                snippet = r.get("snippet", "") or r.get("content", "")

                if not url:
                    continue

                domain = _extract_domain(url)
                if domain in seen_domains:
                    continue

                # Require homepage URL
                if not _is_homepage(url):
                    continue

                # Block aggregators and listing pages
                if _is_aggregator(title, url):
                    continue

                # Block small local businesses
                if _is_excluded(title, snippet):
                    continue

                # ── Region validation ──────────────────────────────────────
                # Check all available text for region name mention
                combined_text = f"{title} {snippet} {url}"
                if not _region_in_text(combined_text, region):
                    logger.debug(
                        "Skipped (region mismatch): '%s' — region '%s' not found in: %s",
                        title, region, combined_text[:120],
                    )
                    continue

                seen_domains.add(domain)
                candidates.append({
                    "name":    _extract_company_name(title),
                    "website": url,
                    "industry": industry,
                    "snippet": snippet,
                })

    logger.info(
        "Tavily: Found %d validated companies in region '%s'",
        len(candidates), region,
    )
    return candidates