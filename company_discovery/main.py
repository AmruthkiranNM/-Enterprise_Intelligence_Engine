"""
main.py — Company Discovery Orchestrator
==========================================
Ties together search → scrape → score into a single pipeline.
Can be used as a library or as a CLI tool.

Pipeline:
  1. search_companies()  — find candidates in the target region
  2. scrape_signals()    — extract revenue-proxy signals from each homepage
  3. score_company()     — classify revenue likelihood
  4. Filter & rank       — discard weak candidates, return top 3–5

Usage (CLI):
    python -m company_discovery.main --region "Pune" --threshold "1Cr+"

Usage (Library):
    from company_discovery import discover_companies
    results = discover_companies("Pune", "1Cr+")
"""

import argparse
import json
import logging
import sys
from typing import List, Dict, Any

from company_discovery.search import search_companies
from company_discovery.scraper import scrape_signals
from company_discovery.scorer import score_company

# ---------------------------------------------------------------------------
# Logging configuration — INFO level gives progress visibility without
# flooding the console.
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-28s | %(levelname)-5s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# Maximum number of candidates to return in the final output.
MAX_RESULTS: int = 5
MIN_RESULTS: int = 3


def discover_companies(
    region: str,
    revenue_threshold: str,
    max_results: int = MAX_RESULTS,
) -> List[Dict[str, Any]]:
    """
    Main entry point — discover companies in a region and estimate
    whether they meet the given revenue threshold.

    Args:
        region:             Target geographic region (e.g. "Pune").
        revenue_threshold:  Human-readable threshold (e.g. "1Cr+", "10Cr+").
                            Used only for labeling, not for numeric comparison,
                            because we rely on signal-based estimation, not
                            exact revenue data.
        max_results:        Maximum number of candidates to return (3–5).

    Returns:
        List of structured dicts — see output contract in implementation_plan.md.
    """
    logger.info("=" * 60)
    logger.info("Company Discovery Pipeline")
    logger.info("  Region:    %s", region)
    logger.info("  Threshold: %s", revenue_threshold)
    logger.info("=" * 60)

    # ── Step 1: Search ─────────────────────────────────────────────────
    logger.info("[1/4] Searching for companies in %s...", region)
    candidates = search_companies(region)

    if not candidates:
        logger.warning("No candidates found for region: %s", region)
        return []

    logger.info("  → %d candidates found", len(candidates))

    # ── Step 2: Scrape signals from each candidate's homepage ──────────
    logger.info("[2/4] Scraping signals from candidate homepages...")
    enriched_candidates: List[Dict[str, Any]] = []

    for i, candidate in enumerate(candidates, 1):
        logger.info("  [%d/%d] %s (%s)",
                     i, len(candidates), candidate["name"], candidate["website"])

        signals = scrape_signals(candidate["website"])

        enriched_candidates.append({
            **candidate,
            "signals": signals,
        })

    # ── Step 3: Score each candidate ──────────────────────────────────
    logger.info("[3/4] Scoring candidates...")
    scored: List[Dict[str, Any]] = []

    for candidate in enriched_candidates:
        score_result = score_company(candidate["signals"])

        # Discard companies with 0 detected signals.
        if score_result["revenue_likelihood"] == "Discard":
            logger.info("  ✗ Discarded: %s (no signals)", candidate["name"])
            continue

        scored.append({
            "company_name":       candidate["name"],
            "website":            candidate["website"],
            "industry":           candidate["industry"],
            "business_stage":     score_result["business_stage"],
            "revenue_likelihood": (
                f"{score_result['revenue_likelihood']} meets {revenue_threshold}"
            ),
            "supporting_signals": score_result["supporting_signals"],
            "confidence_level":   score_result["confidence_level"],
            # Internal fields for sorting (not in final output).
            "_signal_count":      score_result["signal_count"],
            "_weighted_score":    score_result["weighted_score"],
        })

    # ── Step 4: Rank and return top N ─────────────────────────────────
    logger.info("[4/4] Ranking and selecting top %d candidates...", max_results)

    # Sort by weighted score descending, then by signal count as tiebreaker.
    scored.sort(key=lambda x: (x["_weighted_score"], x["_signal_count"]),
                reverse=True)

    # Take top N.
    top_candidates = scored[:max_results]

    # Strip internal fields before returning.
    for candidate in top_candidates:
        candidate.pop("_signal_count", None)
        candidate.pop("_weighted_score", None)

    logger.info("=" * 60)
    logger.info("Pipeline complete — returning %d candidates", len(top_candidates))
    logger.info("=" * 60)

    return top_candidates


def main() -> None:
    """CLI entry point with argparse."""
    parser = argparse.ArgumentParser(
        description="Discover companies in a region and estimate revenue likelihood.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m company_discovery.main --region "Pune" --threshold "1Cr+"
  python -m company_discovery.main --region "Bengaluru" --threshold "10Cr+" --top 3
        """,
    )
    parser.add_argument(
        "--region", "-r",
        required=True,
        help='Target region (e.g. "Pune", "Bengaluru", "Hyderabad")',
    )
    parser.add_argument(
        "--threshold", "-t",
        default="1Cr+",
        help='Revenue threshold label (e.g. "1Cr+", "10Cr+"). Default: "1Cr+"',
    )
    parser.add_argument(
        "--top", "-n",
        type=int,
        default=MAX_RESULTS,
        help=f"Maximum number of results to return (default: {MAX_RESULTS})",
    )

    args = parser.parse_args()

    results = discover_companies(
        region=args.region,
        revenue_threshold=args.threshold,
        max_results=args.top,
    )

    # Output clean JSON to stdout.
    print(json.dumps(results, indent=2, ensure_ascii=False))

    # Exit with non-zero if no results found.
    sys.exit(0 if results else 1)


if __name__ == "__main__":
    main()
