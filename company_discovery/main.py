"""
main.py — Dual-Mode Enterprise Intelligence Engine
=====================================================
Routes between two mutually exclusive pipelines:

REGION MODE  (--region):  Market Discovery Engine
    search → scrape → score → rank → JSON output

DOMAIN MODE  (--domain):  Strategic Intelligence Engine
    research → dossier → bottlenecks → score → outreach → JSON output

Usage:
    python -m company_discovery.main --region "Mumbai" --threshold "1Cr+"
    python -m company_discovery.main --domain "druva.com" --threshold "10Cr+"
"""

import argparse
import json
import logging
import sys
from typing import List, Dict, Any, Optional

from company_discovery.utils import interpret_threshold, validate_inputs
from company_discovery.search import search_companies
from company_discovery.signals import extract_signals
from company_discovery.scoring import score_company_region, score_company_domain
from company_discovery.intelligence import (
    build_dossier, detect_bottlenecks, compute_strategic_pressure,
    get_pressure_metadata
)
from company_discovery.outreach import generate_outreach

# ────────────────────────────────────────────────────────────────
# Logging
# ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-28s | %(levelname)-5s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

MAX_RESULTS: int = 5


# ════════════════════════════════════════════════════════════════
# REGION PIPELINE — Market Discovery
# ════════════════════════════════════════════════════════════════

def run_region_pipeline(
    region: str,
    threshold: str,
    max_results: int = MAX_RESULTS,
) -> List[Dict[str, Any]]:
    """
    Discover companies in a region, scrape public signals,
    score them against the threshold, and return the top N.
    """
    threshold_config = interpret_threshold(threshold)

    logger.info("=" * 60)
    logger.info("REGION MODE — Market Discovery Engine")
    logger.info("  Region:    %s", region)
    logger.info("  Threshold: %s (tier: %s)", threshold, threshold_config["tier"])
    logger.info("=" * 60)

    # Step 1: Search
    logger.info("[1/4] Searching for companies in %s...", region)
    candidates = search_companies(region)

    if not candidates:
        logger.warning("No candidates found for region: %s", region)
        return []

    logger.info("  → %d candidates found", len(candidates))

    # Step 2: Extract signals
    logger.info("[2/4] Scraping signals from candidate homepages...")
    enriched: List[Dict[str, Any]] = []

    for i, candidate in enumerate(candidates, 1):
        logger.info("  [%d/%d] %s (%s)",
                     i, len(candidates), candidate["name"], candidate["website"])

        signals = extract_signals(candidate["website"])
        enriched.append({**candidate, "signals": signals})

    # Step 3: Score with threshold awareness
    logger.info("[3/4] Scoring candidates (threshold tier: %s)...",
                threshold_config["tier"])
    scored: List[Dict[str, Any]] = []

    for candidate in enriched:
        score_result = score_company_region(candidate["signals"], threshold_config)

        if score_result["revenue_likelihood"] == "Discard":
            logger.info("  ✗ Discarded: %s (no signals)", candidate["name"])
            continue

        scored.append({
            "company_name":       candidate["name"],
            "website":            candidate["website"],
            "industry":           candidate["industry"],
            "business_stage":     score_result["business_stage"],
            "revenue_likelihood": (
                f"{score_result['revenue_likelihood']} meets {threshold}"
            ),
            "supporting_signals": score_result["supporting_signals"],
            "confidence_level":   score_result["confidence_level"],
            "_weighted_score":    score_result["weighted_score"],
            "_signal_count":      score_result["signal_count"],
        })

    # Step 4: Rank and return top N
    logger.info("[4/4] Ranking and selecting top %d candidates...", max_results)
    scored.sort(key=lambda x: (x["_weighted_score"], x["_signal_count"]),
                reverse=True)

    top = scored[:max_results]

    # Strip internal fields
    for c in top:
        c.pop("_weighted_score", None)
        c.pop("_signal_count", None)

    logger.info("=" * 60)
    logger.info("Region pipeline complete — returning %d candidates", len(top))
    logger.info("=" * 60)

    return top


# ════════════════════════════════════════════════════════════════
# DOMAIN PIPELINE — Strategic Intelligence
# ════════════════════════════════════════════════════════════════

def run_domain_pipeline(
    domain: str,
    threshold: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Deep-research a single company domain, detect bottlenecks,
    score as a lead, and generate outreach if qualified.

    Threshold is optional for domain mode — defaults to medium tier.
    """
    threshold = threshold or "10Cr+"
    threshold_config = interpret_threshold(threshold)

    logger.info("=" * 60)
    logger.info("DOMAIN MODE — Strategic Intelligence Engine")
    logger.info("  Domain:    %s", domain)
    logger.info("  Threshold: %s (tier: %s)", threshold, threshold_config["tier"])
    logger.info("=" * 60)

    # Step 1: Build dossier
    logger.info("[1/5] Researching %s...", domain)
    dossier = build_dossier(domain)

    if dossier.get("error"):
        logger.error("Research failed: %s", dossier["error"])
        return {"domain": domain, "error": dossier["error"]}

    # Step 2: Detect bottlenecks
    logger.info("[2/5] Detecting strategic bottlenecks...")
    bottlenecks = detect_bottlenecks(dossier)
    logger.info("  → %d bottleneck(s) detected", len(bottlenecks))

    # Step 3: Score lead
    logger.info("[3/5] Scoring lead (threshold tier: %s)...", threshold_config["tier"])
    score_result = score_company_domain(dossier, bottlenecks, threshold_config)
    logger.info("  → Score: %d/100 — %s",
                score_result["total"], score_result["classification"])

    # Build why-now explanation
    why_now = _build_why_now(dossier, score_result)

    # Step 4: Generate outreach (only if qualified)
    logger.info("[4/5] Generating outreach strategy...")
    outreach = generate_outreach(domain, dossier, bottlenecks, score_result)

    if outreach:
        logger.info("  → Outreach generated for %s", outreach["recommended_decision_maker"])
    else:
        logger.info("  → Lead not qualified for outreach")

    # Step 5: Assemble final output
    logger.info("[5/5] Assembling final intelligence report...")

    output = {
        "mode": "DOMAIN",
        "domain": domain,
        "threshold": threshold,
        "company_dossier": {
            "industry": dossier["industry"],
            "business_stage": dossier["business_stage"],
            "hiring_intensity": dossier["hiring_intensity"],
            "signal_count": dossier["signal_count"],
            "growth_signals": dossier["growth_signals"],
            "scale_signals": dossier["scale_signals"],
            "trigger_events": dossier["trigger_events"],
            "strategic_pressure_score": dossier.get("strategic_pressure_score", 0),
        },
        "strategic_bottlenecks": bottlenecks,
        "lead_score": {
            "scores": score_result["scores"],
            "total": score_result["total"],
            "classification": score_result["classification"],
            "has_trigger_event": score_result["has_trigger_event"],
            "strategic_pressure_index": score_result.get("strategic_pressure", 0),
            **get_pressure_metadata(score_result.get("strategic_pressure", 0))
        },
        "why_now": why_now,
        "personalized_outreach": outreach,
        "agent_research_trace": dossier.get("research_trace", []),
    }

    logger.info("=" * 60)
    logger.info("Domain pipeline complete — %s: %s (%d/100)",
                domain, score_result["classification"], score_result["total"])
    logger.info("=" * 60)

    return output


def _build_why_now(dossier: Dict[str, Any], score_result: Dict[str, Any]) -> str:
    """Build a why-now explanation from trigger events and growth signals."""
    triggers = dossier.get("trigger_events", [])
    growth = dossier.get("growth_signals", [])
    classification = score_result.get("classification", "Not Priority")

    if not triggers and not growth:
        return (
            f"Classification: {classification}. "
            "No strong trigger events detected from public sources. "
            "Recommend monitoring for future signals."
        )

    parts = []
    if triggers:
        parts.append(f"Trigger events detected: {'; '.join(triggers[:3])}")
    if growth:
        parts.append(f"Growth signals: {'; '.join(growth[:3])}")

    return (
        f"Classification: {classification}. "
        + " | ".join(parts)
        + " — These converging signals create a strategic window for engagement."
    )


# ════════════════════════════════════════════════════════════════
# Backward-compatible wrapper
# ════════════════════════════════════════════════════════════════

def discover_companies(
    region: str,
    revenue_threshold: str,
    max_results: int = MAX_RESULTS,
) -> List[Dict[str, Any]]:
    """
    Backward-compatible entry point.
    Wraps run_region_pipeline() so old imports still work:
        from company_discovery import discover_companies
    """
    return run_region_pipeline(region, revenue_threshold, max_results)


# ════════════════════════════════════════════════════════════════
# CLI
# ════════════════════════════════════════════════════════════════

def main() -> None:
    """Dual-mode CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Enterprise Intelligence Engine — Dual-mode company analysis.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Region mode:
    python -m company_discovery.main --region "Mumbai" --threshold "1Cr+"

  Domain mode:
    python -m company_discovery.main --domain "druva.com"
    python -m company_discovery.main --domain "druva.com" --threshold "10Cr+"
        """,
    )

    # Mutually exclusive: --region XOR --domain
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        "--region", "-r",
        help='Region mode: discover companies in a city (e.g. "Pune")',
    )
    mode_group.add_argument(
        "--domain", "-d",
        help='Domain mode: deep-research a company (e.g. "druva.com")',
    )

    parser.add_argument(
        "--threshold", "-t",
        default=None,
        help='Revenue threshold (e.g. "1Cr+", "10Cr+", "100Cr+"). Required for region mode, optional for domain mode.',
    )
    parser.add_argument(
        "--top", "-n",
        type=int,
        default=MAX_RESULTS,
        help=f"(Region mode only) Max results to return (default: {MAX_RESULTS})",
    )

    args = parser.parse_args()

    # ── Validate: region mode requires threshold ───────────
    if args.region and not args.threshold:
        parser.error("--threshold is required for region mode")

    # ── Route to the correct pipeline ──────────────────────
    if args.region:
        results = run_region_pipeline(
            region=args.region,
            threshold=args.threshold,
            max_results=args.top,
        )
    else:
        results = run_domain_pipeline(
            domain=args.domain,
            threshold=args.threshold,
        )

    # Output clean JSON to stdout
    print(json.dumps(results, indent=2, ensure_ascii=False))

    # Exit code: 0 = success, 1 = no results / not qualified
    if isinstance(results, list):
        sys.exit(0 if results else 1)
    else:
        has_error = results.get("error")
        sys.exit(1 if has_error else 0)


if __name__ == "__main__":
    main()
