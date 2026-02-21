"""
intelligence.py — Domain Research & Bottleneck Analysis
========================================================
Runs the Strategic Intelligence Engine for a single company domain.

Pipeline:
    1. Scrape homepage, about, blog, careers for signals
    2. Build structured company dossier
    3. Compute strategic_pressure_score
    4. Detect strategic bottlenecks via pressure inference
    5. Return dossier + bottlenecks for scoring

This module uses only public signals. It does NOT fabricate
financial data. If a signal is missing, it says so explicitly.
"""

import logging
import re
import os
import json
from typing import Dict, Any, List, Optional

import requests
from bs4 import BeautifulSoup

from company_discovery.scraper import _fetch_page
from company_discovery.signals import extract_signals, count_positive_signals

logger = logging.getLogger(__name__)

# ────────────────────────────────────────────────────────────────
# DataVex Service Catalog for bottleneck-to-service mapping
# ────────────────────────────────────────────────────────────────
def _load_catalog_services() -> List[str]:
    """Load service names from catalog.json if available."""
    cat_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "catalog.json")
    if os.path.exists(cat_path):
        try:
            with open(cat_path, "r") as f:
                data = json.load(f)
                return [s["name"] for s in data.get("services", [])]
        except Exception as e:
            logger.warning("Failed to load catalog.json: %s", e)
    
    # Fallback to defaults if catalog.json is missing or invalid
    return [
        "AI Automation",
        "Data Engineering & Pipelines",
        "Cloud Modernization",
        "DevOps Optimization",
        "Digital Transformation & Process Automation",
    ]

DATAVEX_SERVICES = _load_catalog_services()

# ────────────────────────────────────────────────────────────────
# Sub-page paths to check beyond the homepage
# ────────────────────────────────────────────────────────────────
SUB_PAGES = ["/about", "/careers", "/blog", "/company", "/services", "/products"]


def _scrape_subpages(base_url: str) -> Dict[str, Optional[BeautifulSoup]]:
    """Attempt to fetch common sub-pages. Returns map of path → soup."""
    pages: Dict[str, Optional[BeautifulSoup]] = {}
    base = base_url.rstrip("/")

    for path in SUB_PAGES:
        url = f"{base}{path}"
        soup = _fetch_page(url)
        if soup:
            pages[path] = soup
            logger.info("  Fetched: %s", url)
        else:
            logger.debug("  Not found: %s", url)

    return pages


def _extract_text_from_pages(
    homepage_soup: Optional[BeautifulSoup],
    subpages: Dict[str, Optional[BeautifulSoup]],
) -> str:
    """Combine all visible text from all fetched pages."""
    texts: List[str] = []

    if homepage_soup:
        texts.append(homepage_soup.get_text(separator=" ", strip=True))

    for soup in subpages.values():
        if soup:
            texts.append(soup.get_text(separator=" ", strip=True))

    return " ".join(texts)


# ════════════════════════════════════════════════════════════════
# Dossier Builder
# ════════════════════════════════════════════════════════════════

def _detect_industry(full_text: str) -> str:
    """Best-effort industry detection from page text."""
    industry_keywords = {
        "SaaS": ["saas", "software as a service", "cloud platform", "subscription"],
        "FinTech": ["fintech", "payment", "banking", "financial technology", "lending"],
        "HealthTech": ["healthtech", "health tech", "diagnostic", "medical", "healthcare"],
        "EdTech": ["edtech", "education technology", "learning platform", "e-learning"],
        "IT Services": ["it services", "consulting", "technology services", "outsourcing"],
        "E-commerce": ["e-commerce", "ecommerce", "marketplace", "online store"],
        "Enterprise Tech": ["enterprise", "b2b", "platform", "infrastructure"],
        "AI / ML": ["artificial intelligence", "machine learning", "deep learning", "ai-powered"],
        "Cloud / DevOps": ["cloud", "devops", "kubernetes", "containerization", "ci/cd"],
        "Data": ["data engineering", "data pipeline", "analytics", "data platform", "big data"],
        "Logistics Tech": ["logistics", "supply chain", "delivery", "fulfillment"],
    }

    text_lower = full_text.lower()
    best_match = "Technology"
    best_count = 0

    for industry, keywords in industry_keywords.items():
        count = sum(1 for kw in keywords if kw in text_lower)
        if count > best_count:
            best_count = count
            best_match = industry

    return best_match


def _detect_hiring_intensity(full_text: str, subpages: Dict) -> str:
    """Estimate hiring intensity: Low / Moderate / High."""
    text_lower = full_text.lower()
    careers_page = subpages.get("/careers")

    if careers_page:
        careers_text = careers_page.get_text(separator=" ").lower()
        job_patterns = re.findall(
            r"(?:apply now|open position|we.re hiring|join us|view role"
            r"|job opening|current opening|work with us|career)",
            careers_text
        )
        if len(job_patterns) >= 5:
            return "High"
        elif len(job_patterns) >= 1:
            return "Moderate"

    if any(kw in text_lower for kw in [
        "we're hiring", "join our team", "open roles",
        "careers", "job opening", "work with us",
    ]):
        return "Moderate"

    return "Low"


def _detect_growth_signals(full_text: str) -> List[str]:
    """Identify growth signals from page text."""
    signals = []
    text_lower = full_text.lower()

    growth_indicators = [
        ("expansion", "Geographic or market expansion mentioned"),
        ("new office", "New office opening signal"),
        ("partnership", "Strategic partnership detected"),
        ("product launch", "New product/feature launch"),
        ("acquisition", "M&A activity detected"),
        ("ipo", "IPO or public listing signal"),
        ("series", "Funding round reference"),
        ("raised", "Fundraising activity"),
        ("revenue growth", "Revenue growth mentioned"),
        ("yoy growth", "Year-over-year growth signal"),
        ("doubled", "Scale doubling signal"),
        ("tripled", "3x growth signal"),
        ("new product", "New product launch detected"),
        ("launched", "Product/feature launch detected"),
    ]

    for keyword, description in growth_indicators:
        if keyword in text_lower:
            signals.append(description)

    return signals


def _detect_scale_signals(full_text: str) -> List[str]:
    """Identify scale indicators (budget/size proxy). Strict validation."""
    signals = []
    text_lower = full_text.lower()

    # Standard scale patterns
    standard_patterns = [
        (r"\d{3,}\+?\s*(?:employees|team members|people)", "Large team size"),
        (r"fortune\s*(?:500|100)", "Fortune 500/100 client base"),
        (r"(?:global|worldwide|international)\s*(?:presence|operations)", "Global presence"),
        (r"\$\d+[mb]\b", "Dollar-denominated funding/revenue"),
        (r"(?:enterprise|global)\s*(?:clients?|customers?)", "Enterprise client base"),
        (r"(?:\d+)\s*(?:countries|regions|offices)", "Multi-geography operations"),
        (r"(?:billion|million)\s*(?:dollar|usd|\$)", "Large-scale revenue reference"),
    ]

    for pattern, description in standard_patterns:
        if re.search(pattern, text_lower, re.IGNORECASE):
            signals.append(description)

    # ── Fix 1: Strict public listing validation ──────────────
    # Only include "Publicly listed" if explicit exchange/IPO evidence
    public_listing_patterns = [
        r"\bipo\b",
        r"\bnasdaq\b",
        r"\bnyse\b",
        r"\bbse\b",
        r"\bnse\b",
        r"stock\s*exchange",
        r"ticker\s*(?:symbol)?\s*[:=]?\s*[A-Z]{2,5}",
        r"publicly\s*(?:listed|traded)",
        r"listed\s*on\s*(?:nasdaq|nyse|bse|nse)",
    ]
    if any(re.search(p, text_lower, re.IGNORECASE) for p in public_listing_patterns):
        signals.append("Publicly listed")

    return signals


def _detect_trigger_events(full_text: str) -> List[str]:
    """
    Identify trigger events that create strategic urgency.

    Fix 5: Trigger validation — events must reference concrete activity.
    Generic "raised" alone excluded unless tied to a funding round context.
    """
    triggers = []
    text_lower = full_text.lower()

    # ── Concrete trigger patterns (validated) ────────────────
    trigger_patterns = [
        ("new cto", "New CTO appointment — technology direction change"),
        ("new cfo", "New CFO — fiscal restructuring signal"),
        ("new ceo", "New CEO — strategic direction change"),
        ("digital transformation", "Active digital transformation initiative"),
        ("cloud migration", "Cloud migration underway"),
        ("cost optimization", "Cost optimization pressure"),
        ("budget cut", "Fiscal pressure — budget restructuring"),
        ("downsizing", "Fiscal pressure — operational restructuring"),
        ("layoff", "Fiscal pressure — workforce reduction"),
        ("restructuring", "Organizational restructuring"),
        ("pivot", "Business model pivot — strategic shift"),
        ("rebranding", "Brand/market pivot detected"),
        ("new direction", "Strategic direction shift"),
        ("recently funded", "Recent funding — growth investment incoming"),
        ("series a", "Series A funding — growth investment"),
        ("series b", "Series B funding — scale-up investment"),
        ("series c", "Series C funding — expansion stage"),
        ("series d", "Series D funding — late-stage growth"),
        ("series e", "Series E+ funding — pre-IPO stage"),
        ("acquisition", "M&A activity — integration complexity"),
        ("acquired", "Company acquired — strategic integration"),
        ("merger", "Corporate merger — complex system consolidation"),
        ("new office", "New office expansion — operational scaling"),
        ("expansion", "Market/geographic expansion initiative"),
        ("ipo", "IPO — public markets entry"),
        ("product launch", "Major product launch — platform growth"),
    ]

    seen_descriptions = set()
    for keyword, description in trigger_patterns:
        if keyword in text_lower and description not in seen_descriptions:
            triggers.append(description)
            seen_descriptions.add(description)

    # ── Fix 5: "raised" only valid with funding-round context ─
    if "raised" in text_lower:
        funding_context = re.search(
            r"raised\s+\$?\d+|raised.*(?:series|round|seed|funding|million|billion|venture)",
            text_lower,
        )
        if funding_context:
            desc = "Fundraising activity — capital infusion"
            if desc not in seen_descriptions:
                triggers.append(desc)
                seen_descriptions.add(desc)

    # "launched" only valid with product/feature/platform context
    if "launched" in text_lower:
        launch_context = re.search(
            r"launched\s+(?:a\s+)?(?:new\s+)?(?:product|platform|feature|service|tool|solution)",
            text_lower,
        )
        if launch_context:
            desc = "Feature/product launch event"
            if desc not in seen_descriptions:
                triggers.append(desc)
                seen_descriptions.add(desc)

    # "ai initiative" only if genuine AI context present
    if "ai initiative" in text_lower or "ai strategy" in text_lower:
        desc = "AI adoption initiative"
        if desc not in seen_descriptions:
            triggers.append(desc)
            seen_descriptions.add(desc)

    return triggers


def build_dossier(domain: str) -> Dict[str, Any]:
    """
    Build a comprehensive company dossier from public sources.

    Scrapes homepage + sub-pages, then extracts structured intelligence.
    Does NOT fabricate any financial data.
    """
    base_url = f"https://{domain}" if not domain.startswith("http") else domain
    logger.info("Building dossier for: %s", base_url)

    # ── Fetch pages ──────────────────────────────────────────
    homepage_soup = _fetch_page(base_url)
    subpages = _scrape_subpages(base_url)
    full_text = _extract_text_from_pages(homepage_soup, subpages)

    if not full_text:
        logger.warning("Could not fetch any content from %s", domain)
        return {
            "domain": domain,
            "error": "Could not fetch website content",
            "industry": "Unknown",
            "hiring_intensity": "Unknown",
            "growth_signals": [],
            "scale_signals": [],
            "trigger_events": [],
            "signals": {},
            "strategic_pressure_score": 0,
            "research_trace": ["Attempted homepage fetch — failed"],
        }

    # ── Extract structured intelligence ──────────────────────
    signals = extract_signals(base_url)
    signal_count = count_positive_signals(signals)

    industry = _detect_industry(full_text)
    hiring_intensity = _detect_hiring_intensity(full_text, subpages)
    growth_signals = _detect_growth_signals(full_text)
    scale_signals = _detect_scale_signals(full_text)
    trigger_events = _detect_trigger_events(full_text)

    # ── Strategic Pressure Score ────────────────────────────
    pressure = compute_strategic_pressure(
        growth_signals, scale_signals, hiring_intensity,
        signals, trigger_events,
    )

    # ── Business stage inference ─────────────────────────────
    if signal_count >= 5 or pressure >= 6:
        stage = "Mature"
    elif signal_count >= 3 or pressure >= 4:
        stage = "Growth"
    else:
        stage = "Early"

    # ── Research trace ───────────────────────────────────────
    trace = [
        f"Scraped homepage: {base_url}",
    ]
    for path in subpages:
        trace.append(f"Fetched sub-page: {path}")
    trace.append(f"Detected industry: {industry}")
    trace.append(f"Detected {signal_count}/7 revenue-proxy signals")
    trace.append(f"Hiring intensity: {hiring_intensity}")
    trace.append(f"Found {len(growth_signals)} growth signal(s)")
    trace.append(f"Found {len(scale_signals)} scale signal(s)")
    trace.append(f"Found {len(trigger_events)} trigger event(s)")
    trace.append(f"Strategic pressure score: {pressure}")

    dossier = {
        "domain": domain,
        "industry": industry,
        "business_stage": stage,
        "hiring_intensity": hiring_intensity,
        "growth_signals": growth_signals,
        "scale_signals": scale_signals,
        "trigger_events": trigger_events,
        "signal_count": signal_count,
        "signals": signals,
        "strategic_pressure_score": pressure,
        "research_trace": trace,
        "_full_text": full_text,  # internal: used by AI gating in detect_bottlenecks
    }

    logger.info("Dossier built: %s (%s, %s stage, %d signals, pressure=%d)",
                domain, industry, stage, signal_count, pressure)

    return dossier


# ════════════════════════════════════════════════════════════════
# Strategic Pressure Score
# ════════════════════════════════════════════════════════════════

def compute_strategic_pressure(
    growth_signals: List[str],
    scale_signals: List[str],
    hiring_intensity: str,
    signals: Dict[str, Dict[str, Any]],
    trigger_events: List[str],
) -> int:
    """
    Derived metric: strategic_pressure_score.

    Calculation:
        +1 per growth signal
        +1 per scale signal
        +1 if hiring intensity = Moderate
        +2 if hiring intensity = High
        +1 if M&A detected
        +1 if new office expansion detected
        +1 if enterprise client references detected
    """
    score = 0

    # +1 per growth signal
    score += len(growth_signals)

    # +1 per scale signal
    score += len(scale_signals)

    # Hiring intensity
    if hiring_intensity == "High":
        score += 2
    elif hiring_intensity == "Moderate":
        score += 1

    # M&A detection (from trigger events or growth signals)
    ma_keywords = ["m&a", "acquisition", "acquired", "merger"]
    if any(any(kw in s.lower() for kw in ma_keywords) for s in trigger_events + growth_signals):
        score += 1

    # New office expansion
    office_keywords = ["new office", "expansion"]
    if any(any(kw in s.lower() for kw in office_keywords) for s in trigger_events + growth_signals):
        score += 1

    # Enterprise client references
    has_enterprise = signals.get("enterprise_clients", {}).get("detected", False)
    if has_enterprise:
        score += 1

    logger.info("Strategic pressure score: %d", score)
    return score


# ════════════════════════════════════════════════════════════════
# Bottleneck Detection (Pressure-Inferred)
# ════════════════════════════════════════════════════════════════

def _pressure_severity(
    pressure: int,
    growth_signals: List[str],
    scale_signals: List[str],
) -> str:
    """
    Map pressure score to severity label.

    Fix 3: Severity normalization — High requires pressure ≥ 6
    AND ≥ 2 distinct growth signal types AND ≥ 2 scale signal types.
    Prevents automatic inflation from pressure alone.
    """
    if pressure >= 6 and len(growth_signals) >= 2 and len(scale_signals) >= 2:
        return "High"
    elif pressure >= 4:
        return "Medium"
    return "Low"


def detect_bottlenecks(dossier: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Identify strategic/operational bottlenecks from dossier signals.

    Uses strategic_pressure_score for inference — does NOT require
    explicit weakness language on the company website.

    Each bottleneck maps to a DataVex service.
    Only returns "No major bottlenecks" if pressure ≤ 2.
    """
    bottlenecks: List[Dict[str, Any]] = []
    signals = dossier.get("signals", {})
    growth_signals = dossier.get("growth_signals", [])
    scale_signals = dossier.get("scale_signals", [])
    trigger_events = dossier.get("trigger_events", [])
    hiring_intensity = dossier.get("hiring_intensity", "Low")
    industry = dossier.get("industry", "").lower()
    pressure = dossier.get("strategic_pressure_score", 0)
    full_text = dossier.get("_full_text", "")
    severity = _pressure_severity(pressure, growth_signals, scale_signals)

    has_enterprise = signals.get("enterprise_clients", {}).get("detected", False)
    has_funding = signals.get("funding_mentions", {}).get("detected", False)
    has_multi_loc = signals.get("multi_location", {}).get("detected", False)

    # ── 0. Technical Debt & Legacy Modernization ─────────────
    tech_debt_keywords = [
        "legacy system", "on-premise", "mainframe", "monolith", 
        "cobol", "java 8", "old versions", "manual process",
        "outdated infrastructure", "technical debt", "migration from",
    ]
    has_tech_debt = any(kw in full_text.lower() for kw in tech_debt_keywords)
    
    if has_tech_debt:
        bottlenecks.append({
            "title": "Technical debt detected — legacy infrastructure inhibiting agentic scale",
            "evidence": f"Legacy keywords found in site content, Pressure: {pressure}",
            "severity": "High" if pressure >= 4 else "Medium",
            "mapped_service": "Legacy Modernization AI",
        })

    # ── 1. Infrastructure scaling risk ───────────────────────
    # Inferred when: funding + expansion + enterprise clients
    funding_evidence = [s for s in trigger_events + growth_signals
                        if any(kw in s.lower() for kw in
                               ["funding", "raised", "series", "fundrais"])]
    expansion_evidence = [s for s in trigger_events + growth_signals
                          if any(kw in s.lower() for kw in
                                 ["expansion", "new office", "geographic"])]

    if (funding_evidence or has_funding) and (expansion_evidence or has_multi_loc or has_enterprise):
        bottlenecks.append({
            "title": "Infrastructure scaling risk — rapid growth demands exceed current capacity signals",
            "evidence": (
                f"Funding signals: {funding_evidence or ['funding_mentions detected']}, "
                f"Expansion: {expansion_evidence or ['multi-location/enterprise presence']}, "
                f"Pressure: {pressure}"
            ),
            "severity": severity,
            "mapped_service": "Cloud Modernization",
        })

    # ── 2. M&A integration complexity ────────────────────────
    ma_evidence = [s for s in trigger_events + growth_signals
                   if any(kw in s.lower() for kw in
                          ["acquisition", "acquired", "m&a", "merger"])]
    if ma_evidence:
        bottlenecks.append({
            "title": "M&A integration complexity — post-acquisition system consolidation needed",
            "evidence": f"M&A signals: {ma_evidence}, Pressure: {pressure}",
            "severity": severity,
            "mapped_service": "Data Engineering & Pipelines",
        })

    # ── 3. Multi-product DevOps orchestration ────────────────
    product_evidence = [s for s in growth_signals
                        if any(kw in s.lower() for kw in
                               ["product", "launch", "platform", "feature"])]
    if product_evidence or (has_enterprise and len(growth_signals) >= 2):
        bottlenecks.append({
            "title": "Multi-product ecosystem complexity — DevOps orchestration at scale",
            "evidence": (
                f"Product signals: {product_evidence or ['enterprise + growth signals']}, "
                f"Enterprise clients: {has_enterprise}, Pressure: {pressure}"
            ),
            "severity": severity,
            "mapped_service": "DevOps Optimization",
        })

    # ── 4. AI governance / automation scaling ────────────────
    # Fix 2: AI bottleneck gating — only generate if explicit AI evidence
    # Uses word-boundary matching to avoid false positives from substrings
    ai_gate_keywords = [
        "ai product", "ai platform", "ai-powered", "ai solution",
        "machine learning", "ml engineer", "ml platform", "ml pipeline",
        "deep learning", "ai roadmap", "ai expansion",
        "artificial intelligence",
    ]

    # Check 1: AI references in trigger/growth signal descriptions
    ai_in_signals = any(
        any(kw in s.lower() for kw in ai_gate_keywords)
        for s in trigger_events + growth_signals
    )

    # Check 2: Industry is AI/ML
    ai_in_industry = any(kw in industry for kw in ["ai", "ml"])

    # Check 3: Explicit AI phrases in page text (word-boundary regex)
    ai_page_patterns = [
        r"\bai\s+product", r"\bai\s+platform", r"\bai[- ]powered",
        r"\bai\s+solution", r"\bmachine\s+learning", r"\bml\s+engineer",
        r"\bml\s+platform", r"\bml\s+pipeline", r"\bdeep\s+learning",
        r"\bartificial\s+intelligence", r"\bai\s+roadmap",
        r"\bai\s+expansion", r"\bai\s+strategy",
    ]
    ai_in_text = any(
        re.search(p, full_text.lower()) for p in ai_page_patterns
    ) if full_text else False

    # Require at least 2 distinct evidence sources to avoid weak signals
    ai_evidence_count = sum([ai_in_signals, ai_in_industry, ai_in_text])
    has_ai_evidence = ai_evidence_count >= 2

    if has_ai_evidence:
        bottlenecks.append({
            "title": "AI governance risk — automation scaling without visible ML pipeline governance",
            "evidence": (
                f"AI evidence sources: {ai_evidence_count} "
                f"(signals={ai_in_signals}, industry={ai_in_industry}, page={ai_in_text}), "
                f"Pressure: {pressure}"
            ),
            "severity": severity,
            "mapped_service": "AI Automation",
        })
    # If insufficient AI evidence → no AI bottleneck generated (Fix 2)

    # ── 5. Strategic pressure-inferred scaling complexity ────
    # Fix 6: Conservative inference — use hedged language
    if pressure >= 4 and not bottlenecks:
        bottlenecks.append({
            "title": "Possible scaling complexity inferred from converging growth and scale signals",
            "evidence": (
                f"Strategic pressure: {pressure}, "
                f"Growth signals: {len(growth_signals)}, "
                f"Scale signals: {len(scale_signals)}, "
                f"Hiring: {hiring_intensity}"
            ),
            "severity": severity,
            "mapped_service": "Cloud Modernization",
        })

    if pressure >= 6 and len(bottlenecks) < 3:
        bottlenecks.append({
            "title": "Possible operational strain — growth velocity may exceed infrastructure maturity",
            "evidence": (
                f"Strategic pressure: {pressure} (≥6 threshold), "
                f"Hiring: {hiring_intensity}, "
                f"Triggers: {len(trigger_events)}"
            ),
            "severity": severity,  # Fix 3: use normalized severity, not forced "High"
            "mapped_service": "Digital Transformation & Process Automation",
        })

    # ── 6. Expansion without process automation ──────────────
    if expansion_evidence and has_multi_loc and hiring_intensity != "Low":
        bottlenecks.append({
            "title": "Geographic expansion without visible process automation",
            "evidence": (
                f"Expansion: {expansion_evidence}, "
                f"Multi-location: True, Hiring: {hiring_intensity}"
            ),
            "severity": severity,
            "mapped_service": "Digital Transformation & Process Automation",
        })

    # ── 7. Cost optimization pressure ────────────────────────
    cost_evidence = [s for s in trigger_events
                     if any(kw in s.lower() for kw in ["cost", "restructur"])]
    if cost_evidence:
        bottlenecks.append({
            "title": "Cost optimization pressure — operational efficiency gap",
            "evidence": f"Cost triggers: {cost_evidence}",
            "severity": "High",
            "mapped_service": "Data Engineering & Pipelines",
        })

    # ── Fallback: only if pressure ≤ 2 ──────────────────────
    if not bottlenecks:
        if pressure <= 2:
            bottlenecks.append({
                "title": "No major bottlenecks — insufficient strategic pressure signals",
                "evidence": f"Strategic pressure: {pressure} (≤2 threshold)",
                "severity": "Low",
                "mapped_service": "N/A",
            })
        else:
            # Pressure 3 = moderate; still infer something
            bottlenecks.append({
                "title": "Possible moderate scaling complexity — growth signals present but limited evidence",
                "evidence": (
                    f"Strategic pressure: {pressure}, "
                    f"Growth: {len(growth_signals)}, Scale: {len(scale_signals)}"
                ),
                "severity": "Medium",
                "mapped_service": "Cloud Modernization",
            })

    dossier["research_trace"].append(
        f"Strategic pressure: {pressure} → "
        f"Detected {len(bottlenecks)} bottleneck(s) (severity: {severity})"
    )

    return bottlenecks
