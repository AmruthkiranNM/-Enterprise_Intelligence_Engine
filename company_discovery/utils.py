"""
utils.py — Shared Utilities
============================
Threshold interpretation, input validation, and common helpers
used across both Region and Domain pipelines.
"""

import logging
import sys
from typing import Dict, Any

logger = logging.getLogger(__name__)


# ────────────────────────────────────────────────────────────────
# Threshold Interpretation
# ────────────────────────────────────────────────────────────────
# We map human-readable thresholds to scale tiers that influence
# scoring strictness. We NEVER fabricate revenue numbers.
# ────────────────────────────────────────────────────────────────

THRESHOLD_TIERS: Dict[str, Dict[str, Any]] = {
    "low": {
        "label": "Low scale requirement",
        "min_signals_region": 2,       # Region: accept "Possibly" (2+ signals)
        "budget_score_floor": 5,       # Domain: minimum budget sub-score
        "scale_penalty": 0,            # Domain: no penalty for small signals
    },
    "medium": {
        "label": "Medium scale requirement",
        "min_signals_region": 3,       # Region: require "Likely" (3+ signals)
        "budget_score_floor": 10,      # Domain: moderate budget expectation
        "scale_penalty": 5,            # Domain: penalize if no scale evidence
    },
    "high": {
        "label": "High scale requirement",
        "min_signals_region": 4,       # Region: require strong "Likely" (4+ signals)
        "budget_score_floor": 14,      # Domain: high budget expectation
        "scale_penalty": 10,           # Domain: heavy penalty if no scale evidence
    },
}


def interpret_threshold(threshold_str: str) -> Dict[str, Any]:
    """
    Convert a human-readable threshold string into a scale tier config.

    Mapping:
        '1Cr+'          → low
        '10Cr+'         → medium
        '50Cr+', '100Cr+' → high
        Anything else   → low (conservative default)
    """
    t = threshold_str.strip().lower().replace(" ", "")

    if t in ("100cr+", "500cr+", "1000cr+", "50cr+"):
        tier = "high"
    elif t in ("10cr+", "25cr+", "20cr+"):
        tier = "medium"
    else:
        tier = "low"

    config = THRESHOLD_TIERS[tier]
    logger.info(
        "Threshold '%s' → tier '%s' (%s)",
        threshold_str, tier, config["label"]
    )
    return {"tier": tier, **config}


def validate_inputs(region: str = None, domain: str = None) -> None:
    """
    Validate that exactly one of region or domain is provided.
    Exits with a clear error message if validation fails.
    """
    if region and domain:
        logger.error("Cannot provide both --region and --domain. Pick one.")
        sys.exit(2)

    if not region and not domain:
        logger.error("Must provide either --region or --domain.")
        sys.exit(2)
