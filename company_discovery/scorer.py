"""
scorer.py — Revenue Likelihood Scoring
========================================
Classifies companies by revenue likelihood based on collected signals.

Revenue Estimation Philosophy:
  We NEVER guess exact revenue. Instead, we classify using the density
  of indirect signals:

    ┌─────────────────────────┬──────────────────────────────────┐
    │  Signal Count           │  Classification                  │
    ├─────────────────────────┼──────────────────────────────────┤
    │  3+ strong indicators   │  "Likely" meets threshold        │
    │  1–2 indicators         │  "Possibly" meets threshold      │
    │  0 indicators           │  Discarded (not returned)        │
    └─────────────────────────┴──────────────────────────────────┘

  The confidence level further modulates how sure we are:
    - High:   5+ signals + hiring + funding
    - Medium: 3-4 signals
    - Low:    1-2 signals
"""

from typing import Dict, Any, List, Tuple

# ---------------------------------------------------------------------------
# Signal weights — some signals are stronger revenue indicators than others.
# A hiring page + funding is much more telling than just a press mention.
# ---------------------------------------------------------------------------
SIGNAL_WEIGHTS: Dict[str, float] = {
    "hiring_page":        1.5,  # Active hiring = active investment in growth
    "funding_mentions":   2.0,  # External capital = validated business model
    "team_size":          1.5,  # Large team = large payroll = large revenue
    "enterprise_clients": 1.8,  # Enterprise contracts are high-value
    "years_in_operation": 1.0,  # Longevity = sustainability, but not growth
    "multi_location":     1.3,  # Geo expansion = scaled operations
    "press_mentions":     0.8,  # Visibility, but not a direct revenue proxy
}

# Total number of tracked signals.
TOTAL_SIGNALS: int = len(SIGNAL_WEIGHTS)


def _count_detected_signals(
    signals: Dict[str, Dict[str, Any]]
) -> Tuple[int, float, List[str]]:
    """
    Count how many signals were detected and compute a weighted score.

    Returns:
        (raw_count, weighted_score, list_of_supporting_signal_descriptions)
    """
    raw_count = 0
    weighted_score = 0.0
    supporting: List[str] = []

    for signal_name, result in signals.items():
        if result.get("detected", False):
            raw_count += 1
            weighted_score += SIGNAL_WEIGHTS.get(signal_name, 1.0)
            supporting.append(result.get("details", signal_name))

    return raw_count, weighted_score, supporting


def classify_revenue_likelihood(signal_count: int) -> str:
    """
    Classify revenue likelihood based on the number of detected signals.

    Rules (from the requirements):
      - 3+ signals  → "Likely" meets/exceeds threshold
      - 1–2 signals → "Possibly" meets threshold
      - 0 signals   → "Discard" (caller should filter these out)
    """
    if signal_count >= 3:
        return "Likely"
    elif signal_count >= 1:
        return "Possibly"
    else:
        return "Discard"


def determine_confidence(
    signal_count: int,
    weighted_score: float,
    signals: Dict[str, Dict[str, Any]],
) -> str:
    """
    Determine a confidence level for the revenue estimate.

    High confidence requires:
      - 5+ signals detected, OR
      - Both hiring and funding signals present with 3+ total signals.

    Medium confidence:
      - 3–4 signals detected.

    Low confidence:
      - 1–2 signals detected.

    This layered approach avoids over-stating confidence when we have
    only weak or few signals.
    """
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
    """
    Infer the company's business stage from signal combinations.

    Heuristic mapping:
      - Established: 5+ years + enterprise clients + multi-location
      - Scale-up:    Funding + hiring + team size
      - Growth:      Hiring OR funding present
      - Early:       Few or weak signals

    This is deliberately conservative — we'd rather under-classify
    than over-classify.
    """
    has_hiring = signals.get("hiring_page", {}).get("detected", False)
    has_funding = signals.get("funding_mentions", {}).get("detected", False)
    has_team = signals.get("team_size", {}).get("detected", False)
    has_enterprise = signals.get("enterprise_clients", {}).get("detected", False)
    has_years = signals.get("years_in_operation", {}).get("detected", False)
    has_multi_loc = signals.get("multi_location", {}).get("detected", False)

    # Established: long-running company with enterprise reach.
    if has_years and has_enterprise and has_multi_loc:
        return "Established"

    # Scale-up: has funding runway, is hiring, and has a sizable team.
    if has_funding and has_hiring and has_team:
        return "Scale-up"

    # Growth: actively expanding (hiring or funded but not yet at scale).
    if has_hiring or has_funding:
        return "Growth"

    # Default: early-stage or insufficient data to classify further.
    return "Early"


def score_company(
    signals: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Score a single company based on its extracted signals.

    Args:
        signals: Output of scraper.scrape_signals().

    Returns:
        {
            "revenue_likelihood":  "Likely" | "Possibly" | "Discard",
            "confidence_level":    "High" | "Medium" | "Low",
            "business_stage":      "Established" | "Scale-up" | "Growth" | "Early",
            "supporting_signals":  [str, ...],
            "signal_count":        int,
            "weighted_score":      float,
        }
    """
    count, weighted, supporting = _count_detected_signals(signals)

    return {
        "revenue_likelihood": classify_revenue_likelihood(count),
        "confidence_level":   determine_confidence(count, weighted, signals),
        "business_stage":     determine_business_stage(signals),
        "supporting_signals": supporting,
        "signal_count":       count,
        "weighted_score":     weighted,
    }
