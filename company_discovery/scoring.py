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
        3. Growth & Triggers     (0–20)
        4. Bottleneck Severity   (0–20)
        5. Service Alignment     (0–20)  ← calibrated for enterprise SaaS

    Calibration targets:
        Enterprise growth SaaS → 70–90
        Not below 60 unless evidence genuinely weak
    """
    scores: Dict[str, int] = {}

    industry = dossier.get("industry", "").lower()
    pressure = dossier.get("strategic_pressure_score", 0)
    tier = threshold_config.get("tier", "medium")

    # ── 1. Industry Fit ──────────────────────────────────────
    if any(t in industry for t in ENTERPRISE_INDUSTRIES):
        scores["industry_fit"] = 18
    elif industry and industry != "technology":
        scores["industry_fit"] = 12
    else:
        scores["industry_fit"] = 8

    # ── 2. Budget & Scale Signals (threshold-sensitive) ──────
    scale_signals = dossier.get("scale_signals", [])
    has_enterprise = dossier.get("signals", {}).get(
        "enterprise_clients", {}).get("detected", False)
    has_funding = dossier.get("signals", {}).get(
        "funding_mentions", {}).get("detected", False)

    scale_count = len(scale_signals)
    raw_budget = min(scale_count * 5, 20)

    # Threshold-aware adjustments
    if tier == "high":
        # 100Cr+: require strong scale signals
        if scale_count < 3 and not has_enterprise:
            raw_budget = min(raw_budget, 8)
            logger.info("100Cr+ threshold: capping budget to 8 (weak scale)")
    elif tier == "medium":
        # 10Cr+: require ≥2 scale signals OR enterprise OR funding
        if scale_count >= 2 or has_enterprise or has_funding:
            raw_budget = max(raw_budget, 12)
        else:
            raw_budget = max(raw_budget, 6)

    # Enterprise clients + funding boost
    if has_enterprise:
        raw_budget = max(raw_budget, 14)
    if has_funding:
        raw_budget = min(raw_budget + 3, 20)

    scores["budget_signals"] = min(raw_budget, 20)

    # ── 3. Growth & Trigger Events (deduplicated) ────────────
    triggers = dossier.get("trigger_events", [])
    growth_signals = dossier.get("growth_signals", [])
    # Deduplicate: count unique semantic events, not raw list sizes
    unique_events = set()
    for s in triggers + growth_signals:
        # Normalize to avoid double-counting overlapping descriptions
        key = s.split(" — ")[0].strip().lower()
        unique_events.add(key)
    unique_count = len(unique_events)

    # Diminishing returns curve
    if unique_count >= 6:
        growth_score = 17
    elif unique_count >= 4:
        growth_score = 15
    elif unique_count >= 3:
        growth_score = 13
    elif unique_count >= 2:
        growth_score = 10
    elif unique_count >= 1:
        growth_score = 6
    else:
        growth_score = 0

    # Pressure provides a floor for growth score
    if pressure >= 4:
        growth_score = max(growth_score, 10)

    scores["growth_triggers"] = min(growth_score, 20)
    has_trigger = unique_count > 0

    # ── 4. Bottleneck Severity ──────────────────────────────
    severity_map = {"high": 6, "medium": 4, "low": 2}
    bottleneck_raw = sum(
        severity_map.get(b.get("severity", "").lower(), 0)
        for b in bottlenecks
    )

    # Pressure-based floor (moderate)
    if pressure >= 6:
        bottleneck_raw = max(bottleneck_raw, 12)
    elif pressure >= 4:
        bottleneck_raw = max(bottleneck_raw, 8)

    scores["bottleneck_severity"] = min(bottleneck_raw, 18)

    # ── 5. Service Alignment (calibrated) ────────────────────
    aligned_services = set()
    for b in bottlenecks:
        svc = b.get("mapped_service", "")
        if svc and svc != "N/A":
            aligned_services.add(svc)

    alignment_count = len(aligned_services)

    # Base: 4 per aligned service (avoids ceiling saturation)
    alignment_score = min(alignment_count * 4, 18)

    # Enterprise SaaS / FinTech / HealthTech floor: ≥ 12
    if any(t in industry for t in ENTERPRISE_INDUSTRIES):
        alignment_score = max(alignment_score, 12)

        # Boost for multi-product + cloud-native + enterprise + growth
        enterprise_boost_signals = 0
        if has_enterprise:
            enterprise_boost_signals += 1
        if len(growth_signals) >= 2:
            enterprise_boost_signals += 1
        if scale_count >= 2:
            enterprise_boost_signals += 1
        if any("cloud" in s.lower() or "platform" in s.lower() for s in growth_signals + scale_signals):
            enterprise_boost_signals += 1

        alignment_score = min(alignment_score + enterprise_boost_signals * 2, 20)

    # Service alignment floor of 10 for any enterprise industry
    if any(t in industry for t in ENTERPRISE_INDUSTRIES):
        alignment_score = max(alignment_score, 10)

    scores["service_alignment"] = alignment_score

    # ── Total & Classification ────────────────────────────────
    total = sum(scores.values())

    # Threshold cap for 100Cr+: without strong scale, cap at 70
    if tier == "high" and scale_count < 3 and not has_enterprise:
        if total > 70:
            logger.info("100Cr+ without strong scale: capping %d to 70", total)
            total = 70

    # Trigger cap: if no trigger event → cap at 80
    if not has_trigger and total > 80:
        logger.info("No trigger events — capping score from %d to 80", total)
        total = 80

    # ── Fix 4: Scoring normalization — prevent inflation ─────
    # Allow 90+ ONLY if: funding evidence + multiple trigger types + multiple high-severity bottlenecks
    if total > 88:
        has_funding_trigger = any(
            any(kw in t.lower() for kw in ["funding", "series", "raised", "capital"])
            for t in triggers
        )
        high_severity_count = sum(
            1 for b in bottlenecks if b.get("severity", "").lower() == "high"
        )
        distinct_trigger_types = len(unique_events)

        if has_funding_trigger and distinct_trigger_types >= 3 and high_severity_count >= 2:
            total = min(total, 92)  # Hard ceiling even for strongest profiles
            logger.info("Exceptional profile — capping at %d", total)
        else:
            logger.info("Score normalization: capping %d to 88 (insufficient 90+ criteria)", total)
            total = 88

    # Classification
    if total >= 80:
        classification = "Strong Lead"
    elif total >= 65:
        classification = "Medium Priority"
    else:
        classification = "Not Priority"

    logger.info(
        "Domain score: %d/100 → %s | Pressure: %d | Triggers: %d",
        total, classification, pressure, unique_count,
    )

    return {
        "scores": scores,
        "total": total,
        "classification": classification,
        "has_trigger_event": has_trigger,
        "strategic_pressure": pressure,
    }
