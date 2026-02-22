"""
outreach.py — Personalized Outreach Generation
================================================
Generates SDR outreach content for qualified leads (Strong or Medium).

Rules:
    - Professional advisory tone
    - No aggressive selling
    - Low-friction closing question
    - 120-word executive-level email
    - Only generated for Strong or Medium classification
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


def _infer_decision_maker(dossier: Dict[str, Any]) -> str:
    """
    Recommend the best decision maker to target.
    Based on detected bottleneck types.
    """
    industry = dossier.get("industry", "").lower()

    if any(kw in industry for kw in ["ai", "data", "cloud", "saas"]):
        return "CTO / VP Engineering"
    elif any(kw in industry for kw in ["fintech", "enterprise"]):
        return "CTO / Head of Digital Transformation"
    else:
        return "CTO / VP Technology"


def _build_strategic_angle(
    dossier: Dict[str, Any],
    bottlenecks: List[Dict[str, Any]],
) -> str:
    """Determine the most compelling strategic angle for outreach."""
    # Prioritize substantive bottlenecks
    valid_bottlenecks = [b for b in bottlenecks if "No Strategic Bottlenecks" not in b.get("title")]
    
    if valid_bottlenecks:
        # Sort by severity
        sorted_b = sorted(valid_bottlenecks, key=lambda x: {"High": 0, "Medium": 1, "Low": 2}.get(x.get("severity"), 3))
        return (
            f"Optimize {sorted_b[0]['title'].lower()} via {sorted_b[0]['mapped_service']}"
        )

    return "Optimize operational velocity and scaling efficiency"


def _build_outreach_email(
    domain: str,
    dossier: Dict[str, Any],
    bottlenecks: List[Dict[str, Any]],
    score_result: Dict[str, Any],
) -> str:
    """
    Generate a ~120-word executive-level outreach email.
    Professional advisory tone. No aggressive selling.
    """
    industry = dossier.get("industry", "Technology")
    stage = dossier.get("business_stage", "Growth")
    
    # Pick the most relevant bottleneck
    valid_bottlenecks = [b for b in bottlenecks if b.get("mapped_service") != "Monitoring Only"]
    primary_bottleneck = valid_bottlenecks[0] if valid_bottlenecks else bottlenecks[0]

    bottleneck_desc = primary_bottleneck["title"].lower()
    mapped_service = primary_bottleneck.get("mapped_service", "platforms")

    trigger_text = ""
    triggers = dossier.get("trigger_events", [])
    if triggers:
        trigger_text = f" Given your recent {triggers[0].split('—')[0].split(':')[0].strip().lower()},"
    elif stage in ("Growth", "Mature"):
        trigger_text = f" Given {domain}'s position as a {stage.lower()}-stage player in {industry},"

    email = (
        f"Subject: Thought on {domain}'s {bottleneck_desc}\n"
        f"\n"
        f"Hi,\n"
        f"\n"
        f"I've been following {domain}'s trajectory in the {industry} space — "
        f"the {stage.lower()}-stage momentum is impressive.{trigger_text}\n"
        f"\n"
        f"One pattern we see with companies at your scale: {bottleneck_desc} "
        f"often creates friction that compounds as you grow. "
        f"Our {mapped_service} practice has helped similar teams "
        f"reduce that friction without disrupting existing workflows.\n"
        f"\n"
        f"Would it make sense to share a brief case study that's "
        f"relevant to your current trajectory? No commitment — just "
        f"seeing if there's alignment.\n"
        f"\n"
        f"Best regards"
    )

    return email


def generate_outreach(
    domain: str,
    dossier: Dict[str, Any],
    bottlenecks: List[Dict[str, Any]],
    score_result: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """
    Generate personalized outreach strategy.
    Only produces output for Strong Lead or Medium Priority classifications.

    Returns None if the lead is Not Priority.
    """
    classification = score_result.get("classification", "Not Priority")

    if classification == "Not Priority":
        logger.info("Lead classified as Not Priority — skipping outreach generation")
        return None

    decision_maker = _infer_decision_maker(dossier)
    strategic_angle = _build_strategic_angle(dossier, bottlenecks)
    email = _build_outreach_email(domain, dossier, bottlenecks, score_result)

    outreach = {
        "recommended_decision_maker": decision_maker,
        "key_strategic_angle": strategic_angle,
        "outreach_email": email,
        "closing_question": (
            "Would it make sense to share a brief case study "
            "relevant to your current trajectory?"
        ),
        "tone": "Professional advisory — no aggressive selling",
    }

    # Add to research trace
    dossier.setdefault("research_trace", []).append(
        f"Generated outreach targeting {decision_maker}"
    )

    return outreach
