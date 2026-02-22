"""
scoring.py — Threshold-Aware Scoring Engine (Calibrated)
==========================================================
Replaces the original scorer.py with threshold-sensitive logic.

Two scoring modes:

REGION MODE (score_company_region):
    - Uses signal density to classify revenue likelihood.
    - Threshold tier controls minimum signal count for inclusion.

DOMAIN MODE (score_company_domain):
    - 5-category scoring on a 0-100 scale.
    - Uses strategic_pressure_score from dossier.
    - Threshold tier controls budget/scale strictness.
    - Trigger events from growth + scale + trigger lists.
    - Service alignment calibrated for enterprise SaaS.
    - Target range for strong enterprise companies: 70–90.
"""

import logging
from typing import Dict, Any, List, Tuple

logger = logging.getLogger(__name__)

# ────────────────────────────────────────────────────────────────
# Signal weights for region mode — carried over from scorer.py
# ────────────────────────────────────────────────────────────────
SIGNAL_WEIGHTS: Dict[str, float] = {
    "hiring_page":        1.5,
    "funding_mentions":   2.0,
    "team_size":          1.5,
    "enterprise_clients": 1.8,
    "years_in_operation": 1.0,
    "multi_location":     1.3,
    "press_mentions":     0.8,
}

# Enterprise industry tiers for service alignment calibration
ENTERPRISE_INDUSTRIES = {
    "saas", "fintech", "healthtech", "enterprise", "enterprise tech",
    "cloud", "cloud / devops", "ai", "ai / ml", "data",
}


# ════════════════════════════════════════════════════════════════
# Region Mode Scoring (unchanged core logic + threshold awareness)
# ════════════════════════════════════════════════════════════════

def _count_detected_signals(
    signals: Dict[str, Dict[str, Any]]
) -> Tuple[int, float, List[str]]:
    """Count signals, compute weighted score, collect descriptions."""
    raw_count = 0
    weighted_score = 0.0
    supporting: List[str] = []

    for signal_name, result in signals.items():
        if result.get("detected", False):
            raw_count += 1
            weighted_score += SIGNAL_WEIGHTS.get(signal_name, 1.0)
            supporting.append(result.get("details", signal_name))

    return raw_count, weighted_score, supporting


def classify_revenue_likelihood(signal_count: int, min_signals: int = 3) -> str:
    """
    Threshold-aware classification.
    min_signals is derived from the threshold tier:
        low  → 2 (accept "Possibly" at 2+)
        medium → 3
        high → 4
    """
    if signal_count >= min_signals:
        return "Likely"
    elif signal_count >= 1:
        return "Possibly"
    else:
        return "Discard"


def determine_confidence(
    signal_count: int,
    signals: Dict[str, Dict[str, Any]],
) -> str:
    """Determine confidence level: High / Medium / Low."""
    has_hiring = signals.get("hiring_page", {}).get("detected", False)
    has_funding = signals.get("funding_mentions", {}).get("detected", False)

    if signal_count >= 5:
        return "High"
    if signal_count >= 3 and has_hiring and has_funding:
        return "High"
    if signal_count >= 3:
        return "Medium"
    return "Low"


def determine_business_stage(signals: Dict[str, Dict[str, Any]]) -> str:
    """Infer business stage from signal combinations."""
    has_hiring = signals.get("hiring_page", {}).get("detected", False)
    has_funding = signals.get("funding_mentions", {}).get("detected", False)
    has_team = signals.get("team_size", {}).get("detected", False)
    has_enterprise = signals.get("enterprise_clients", {}).get("detected", False)
    has_years = signals.get("years_in_operation", {}).get("detected", False)
    has_multi_loc = signals.get("multi_location", {}).get("detected", False)

    if has_years and has_enterprise and has_multi_loc:
        return "Established"
    if has_funding and has_hiring and has_team:
        return "Scale-up"
    if has_hiring or has_funding:
        return "Growth"
    return "Early"


def score_company_region(
    signals: Dict[str, Dict[str, Any]],
    threshold_config: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Score a company for Region Mode.
    Uses threshold_config['min_signals_region'] to control strictness.
    """
    min_signals = threshold_config.get("min_signals_region", 3)
    count, weighted, supporting = _count_detected_signals(signals)

    return {
        "revenue_likelihood": classify_revenue_likelihood(count, min_signals),
        "confidence_level":   determine_confidence(count, signals),
        "business_stage":     determine_business_stage(signals),
        "supporting_signals": supporting,
        "signal_count":       count,
        "weighted_score":     weighted,
    }


# ════════════════════════════════════════════════════════════════
# Domain Mode Scoring (Calibrated, Pressure-Aware)
# ════════════════════════════════════════════════════════════════

def score_company_domain(
    dossier: Dict[str, Any],
    bottlenecks: List[Dict[str, Any]],
    threshold_config: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Score a domain-mode target on 5 dimensions (0-20 each = 0-100 total).

    Categories:
        1. Industry Fit          (0–20)
        2. Budget & Scale        (0–20)  ← threshold-sensitive
        3. Growth & Triggers     (0–20)  ← includes complexity detection
        4. Bottleneck Severity   (0–20)
        5. Service Alignment     (0–20)  ← calibrated for enterprise SaaS

    Calibration targets:
        Enterprise growth SaaS → 70–90
        Guard Condition: Min 60 floor for qualified Enterprise SaaS targets.
    """
    scores: Dict[str, int] = {}

    industry = dossier.get("industry", "").lower()
    pressure = dossier.get("strategic_pressure_score", 0)
    tier = threshold_config.get("tier", "medium")
    business_type = dossier.get("business_type", "Unknown")

    # ── 1. Industry Fit ──────────────────────────────────────
    if any(t in industry for t in ENTERPRISE_INDUSTRIES):
        scores["industry_fit"] = 20
    elif industry and industry != "technology":
        scores["industry_fit"] = 12
    else:
        scores["industry_fit"] = 8

    # ── 2. Budget & Scale (Complexity-Aware) ─────────────────
    scale_signals = dossier.get("scale_signals", [])
    has_enterprise = business_type == "Enterprise / Global"
    
    # Scale score from dossier signals + business stage
    scale_score = min(len(scale_signals) * 4, 12)
    if has_enterprise:
        scale_score = max(scale_score, 15)
    
    # Multi-product / Geography / Tech depth boost
    complexity_boost = 0
    if pressure > 30: complexity_boost += 5
    elif pressure > 15: complexity_boost += 3
    
    scores["budget_signals"] = min(scale_score + complexity_boost, 20)

    # ── 3. Growth & Triggers (Complexity-Centric) ────────────
    triggers = dossier.get("trigger_events", [])
    growth_signals = dossier.get("growth_signals", [])
    
    unique_events = set()
    for s in triggers + growth_signals:
        key = s.split(" — ")[0].split(":")[0].strip().lower()
        unique_events.add(key)
    
    unique_count = len(unique_events)
    
    # Base trigger score
    trigger_score = min(unique_count * 5, 15)
    
    # Growth floor based on pressure (Complexity as growth signal)
    if pressure >= 25:
        trigger_score = max(trigger_score, 16)
    elif pressure >= 15:
        trigger_score = max(trigger_score, 12)
        
    scores["growth_triggers"] = min(trigger_score, 20)
    has_trigger = unique_count > 0

    # ── 4. Bottleneck Severity ──────────────────────────────
    severity_map = {"high": 8, "medium": 5, "low": 2}
    bottleneck_raw = sum(
        severity_map.get(b.get("severity", "").lower(), 0)
        for b in bottlenecks
    )

    # Complexity indicates hidden bottlenecks even if not explicit
    if pressure >= 30:
        bottleneck_raw = max(bottleneck_raw, 15)
    elif pressure >= 15:
        bottleneck_raw = max(bottleneck_raw, 10)

    scores["bottleneck_severity"] = min(bottleneck_raw, 20)

    # ── 5. Service Alignment ─────────────────────────────────
    aligned_services = {b.get("mapped_service", "") for b in bottlenecks if b.get("mapped_service") != "N/A"}
    alignment_count = len(aligned_services)
    
    alignment_score = min(alignment_count * 5, 15)
    
    # Enterprise Industry boost
    if any(t in industry for t in ENTERPRISE_INDUSTRIES):
        alignment_score = max(alignment_score, 16)
        if has_enterprise:
            alignment_score = 20

    scores["service_alignment"] = alignment_score

    # ── Total Calculation ────────────────────────────────────
    total = sum(scores.values())

    # ── Guard Condition: Prevents False Negatives ────────────
    # Minimum floor of 60 for qualified Enterprise SaaS targets
    if industry == "saas" and has_enterprise and pressure >= 20:
        if total < 60:
            logger.info("Enterprise SaaS Guard: lifting score from %d to 60", total)
            total = 60

    # Normalization (prevent artificial inflation)
    if not has_trigger and total > 85:
        total = 85

    # Classification
    if total >= 80:
        classification = "Strong Lead"
    elif total >= 65:
        classification = "Medium Priority"
    else:
        classification = "Not Priority"

    logger.info(
        "Final score: %d/100 -> %s | Pressure: %d | Triggers: %d",
        total, classification, pressure, unique_count,
    )

    return {
        "scores": scores,
        "total": total,
        "classification": classification,
        "has_trigger_event": has_trigger,
        "strategic_pressure": pressure,
    }
