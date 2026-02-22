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

# ════════════════════════════════════════════════════════════════
# Website Classification & Scale
# ════════════════════════════════════════════════════════════════

def _classify_website_scale(full_text: str, subpages: Dict) -> Dict[str, str]:
    """
    Determine the type and scale of the business.
    Outputs: Business Type, Business Stage
    """
    text_lower = full_text.lower()
    
    # Scale Indicators
    enterprise_indicators = [
        "global offices", "worldwide presence", "fortune 500", "enterprise solutions",
        "nasdaq", "nyse", "publicly traded", "billion dollar", "subsidiaries in",
        "trusted by", "our clients", "global presence", "international", "global leader"
    ]
    regional_indicators = [
        "serving the tri-state", "midwest leader", "across the region", "metropolitan area",
        "multiple locations in", "state-wide", "regional leader"
    ]
    
    # Structural Complexity Indicators
    complexity_keywords = [
        "api", "sdk", "integrations", "developer", "platform", "multi-product",
        "ecosystem", "solutions for", "products", "documentation", "docs"
    ]

    has_enterprise = any(kw in text_lower for kw in enterprise_indicators)
    has_regional = any(kw in text_lower for kw in regional_indicators)
    has_complexity = sum(1 for kw in complexity_keywords if kw in text_lower) >= 3
    
    # Default to Local/Stable
    business_type = "Local / Small Business"
    business_stage = "Stable"
    
    if has_enterprise or has_complexity:
        business_type = "Enterprise / Global"
        business_stage = "Mature" if has_enterprise else "Growth"
    elif has_regional or len(subpages) > 4:
        business_type = "Regional / Scaling"
        business_stage = "Growth"

    return {
        "business_type": business_type,
        "business_stage": business_stage
    }

def _detect_industry(full_text: str) -> str:
    """Best-effort industry detection from page text."""
    industry_keywords = {
        "Construction": ["construction", "builder", "contractor", "roofing", "renovation", "residential", "commercial building"],
        "SaaS": ["saas", "software as a service", "cloud platform", "subscription", "software testing", "developer tool", "platform", "api", "sdk"],
        "FinTech": ["fintech", "payment", "banking", "financial technology", "lending"],
        "HealthTech": ["healthtech", "health tech", "healthcare"],
        "Professional Services": ["consulting", "legal", "accounting", "advisory"],
        "E-commerce": ["e-commerce", "ecommerce", "online store", "shop"],
        "Manufacturing": ["manufacturing", "factory", "production line", "industrial"],
    }
    text_lower = full_text.lower()
    best_match = "Regional Services" if len(text_lower) > 0 else "Unknown"
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
        job_links = len(careers_page.find_all('a', text=re.compile(r'apply|view|open|role|position', re.I)))
        if job_links >= 5: return "High"
        if job_links >= 1: return "Moderate"
    
    if any(kw in text_lower for kw in ["we're hiring", "careers", "job opening"]):
        return "Moderate"
    return "Low"

def _detect_growth_signals(full_text: str) -> List[str]:
    """Identify growth signals ONLY if explicitly visible."""
    signals = []
    text_lower = full_text.lower()
    
    # Stricter patterns
    indicators = [
        (r"raised \$?\d+ [mb]illion", "Verified large-scale funding"),
        (r"expanding to.*new (market|region|geography)", "Market expansion confirmed"),
        (r"opening.*new office", "Physical expansion signal"),
        (r"acquired\s+[a-z0-9 ]+(inc|corp|ltd)", "Specific M&A activity detected"),
        (r"\d+%\s+(yoy|year-over-year) growth", "Financial growth reported"),
    ]
    for pattern, desc in indicators:
        if re.search(pattern, text_lower):
            signals.append(desc)
    return signals

def _detect_scale_signals(full_text: str) -> List[str]:
    """Identify scale indicators. No assumptions."""
    signals = []
    text_lower = full_text.lower()
    patterns = [
        (r"\b\d{5,}\+?\s+employees\b", "Enterprise-scale workforce"),
        (r"(nasdaq|nyse|stock exchange)\b", "Publicly listed entity"),
        (r"offices in \d+ (countries|cities)", "Global/Regional footprint"),
    ]
    for pattern, desc in patterns:
        if re.search(pattern, text_lower):
            signals.append(desc)
    return signals

def _detect_trigger_events(full_text: str) -> List[str]:
    """Identify concrete trigger events. No generic urgency."""
    triggers = []
    text_lower = full_text.lower()
    events = [
        (r"new (ceo|cto|cfo) [a-z]+ [a-z]+ joined", "Executive leadership transition"),
        (r"ipo process", "Active IPO window"),
        (r"announces merger with", "Strategic merger"),
        (r"series [a-z] (funding|round) of \$", "Growth stage funding round"),
    ]
    for pattern, desc in events:
        if re.search(pattern, text_lower):
            triggers.append(desc)
    return triggers

# ── New Structural Complexity Extraction ────────────────────────

def _detect_product_complexity(full_text: str) -> int:
    """Detect breadth of product ecosystem."""
    text_lower = full_text.lower()
    product_keywords = ["product", "platform", "solution", "suite", "module", "service"]
    # Look for bulleted lists or distinct mentions
    intensity = 0
    if "products" in text_lower or "solutions" in text_lower:
        intensity += 2
    # Count distinct service-like names (manual check for SaaS commonality)
    intensity += len(re.findall(r" (app|api|cloud|automated|managed) ", text_lower)) // 5
    return min(intensity, 10)

def _detect_enterprise_exposure(full_text: str) -> int:
    """Detect enterprise-grade indicators."""
    text_lower = full_text.lower()
    enterprise_keywords = ["fortune 500", "global clients", "trusted by", "soc2", "compliance", "iso 27001", "enterprise-grade"]
    count = sum(1 for kw in enterprise_keywords if kw in text_lower)
    return min(count * 3, 15)

def _detect_geographical_presence(full_text: str) -> int:
    """Detect global/regional footprint."""
    text_lower = full_text.lower()
    geo_keywords = ["global offices", "offices in", "worldwide", "international", "subsidiaries", "across the globe"]
    count = sum(1 for kw in geo_keywords if kw in text_lower)
    return min(count * 5, 15)

def _detect_technical_depth(full_text: str) -> int:
    """Detect technical surface area (APIs, SDKs, Docs)."""
    text_lower = full_text.lower()
    tech_keywords = ["api docs", "developer", "sdk", "documentation", "integrations", "webhooks", "uptime", "latency"]
    count = sum(1 for kw in tech_keywords if kw in text_lower)
    return min(count * 3, 15)

def build_dossier(domain: str) -> Dict[str, Any]:
    """Build a factual dossier with zero-hallucination discipline."""
    base_url = f"https://{domain}" if not domain.startswith("http") else domain
    logger.info("Factual analysis of: %s", domain)
    
    homepage_soup = _fetch_page(base_url)
    subpages = _scrape_subpages(base_url)
    full_text = _extract_text_from_pages(homepage_soup, subpages)
    
    if not full_text:
        return {
            "domain": domain,
            "industry": "Insufficient public evidence available",
            "business_type": "Unknown",
            "business_stage": "Unknown",
            "hiring_intensity": "Unknown",
            "growth_signals": [],
            "scale_signals": [],
            "trigger_events": [],
            "signal_count": 0,
            "strategic_pressure_score": 0,
            "research_trace": ["Website content fetch failed."]
        }

    industry = _detect_industry(full_text)
    hiring = _detect_hiring_intensity(full_text, subpages)
    growth = _detect_growth_signals(full_text)
    scale = _detect_scale_signals(full_text)
    triggers = _detect_trigger_events(full_text)
    classification = _classify_website_scale(full_text, subpages)

    # ── New Strategic Pressure Index (100-point scale) ──────────
    # 1. Financial Triggers (0-20)
    financial_score = min(len(growth) * 5 + len(triggers) * 10, 20)
    
    # 2. Hiring Intensity (0-15)
    hiring_score = 0
    if hiring == "High": hiring_score = 15
    elif hiring == "Moderate": hiring_score = 7
    
    # 3. Product Ecosystem Complexity (0-20)
    product_score = _detect_product_complexity(full_text) * 2
    
    # 4. Enterprise Exposure (0-15)
    enterprise_score = _detect_enterprise_exposure(full_text)
    
    # 5. Multi-Geography Operations (0-15)
    geo_score = _detect_geographical_presence(full_text)
    
    # 6. Technical Infrastructure Depth (0-15)
    tech_score = _detect_technical_depth(full_text)
    
    total_pressure_score = financial_score + hiring_score + product_score + enterprise_score + geo_score + tech_score
    total_pressure_score = min(total_pressure_score, 100)

    # Enterprise SaaS Guard: Minimum floor for baseline complexity
    if industry == "SaaS" and classification["business_type"] == "Enterprise / Global":
        total_pressure_score = max(total_pressure_score, 15)

    trace = [
        f"Analyzed {domain}",
        f"Classification: {classification['business_type']} ({classification['business_stage']})",
        f"Detected {len(growth) + len(triggers)} strategic events",
        f"Complexity Signals: Product({product_score}), Ent({enterprise_score}), Geo({geo_score}), Tech({tech_score})",
        f"Pressure Score: {total_pressure_score}/100"
    ]

    return {
        "domain": domain,
        "industry": industry,
        "business_type": classification["business_type"],
        "business_stage": classification["business_stage"],
        "hiring_intensity": hiring,
        "growth_signals": growth,
        "scale_signals": scale,
        "trigger_events": triggers,
        "signal_count": len(growth) + len(scale) + len(triggers),
        "strategic_pressure_score": total_pressure_score,
        "research_trace": trace,
        "_full_text": full_text
    }

def detect_bottlenecks(dossier: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Strict bottleneck detection — only if evidence converges."""
    bottlenecks = []
    growth = dossier.get("growth_signals", [])
    scale = dossier.get("scale_signals", [])
    triggers = dossier.get("trigger_events", [])
    pressure = dossier.get("strategic_pressure_score", 0)
    
    # Rules for convergence
    has_funding = any("funding" in s.lower() for s in growth + triggers)
    has_expansion = any("expansion" in s.lower() or "office" in s.lower() for s in growth + scale)
    has_hiring = dossier.get("hiring_intensity") == "High"
    
    # 1. Operational Scaling Risk
    if has_funding and (has_expansion or has_hiring):
        bottlenecks.append({
            "title": "Scaling overhead resulting from rapid capital injection and team growth",
            "evidence": "Converging funding and expansion/hiring signals",
            "severity": "High" if pressure > 70 else "Medium",
            "mapped_service": "Digital Transformation & Process Automation"
        })
        
    # 2. Tech Debt / Legacy risk (ONLY if explicit)
    tech_keywords = ["legacy", "monolith", "on-premise", "technical debt", "migration from"]
    if any(kw in dossier.get("_full_text", "").lower() for kw in tech_keywords):
        bottlenecks.append({
            "title": "Legacy technical debt limiting modernization velocity",
            "evidence": "Specific legacy infrastructure keywords found in site content",
            "severity": "Medium",
            "mapped_service": "Legacy Modernization AI"
        })

    # If no bottlenecks
    if not bottlenecks:
        bottlenecks.append({
            "title": "No Strategic Bottlenecks Detected from Public Data",
            "evidence": "Insufficient evidence of operational strain from current trajectory",
            "severity": "Low",
            "mapped_service": "N/A"
        })
        
    return bottlenecks
