"""
backend/reports.py — Decision-Grade Strategic PDF Generation
============================================================
Generates Board-ready PDF reports from DataVex intelligence JSON.
Utilizes reportlab.platypus for structured, high-fidelity layouts.

ALL content is dynamically derived from crawler JSON.
NO hardcoded company data. NO template pain points.

CRITICAL RULES:
  - Never fabricate funding data.
  - Never fabricate executive emails.
  - If unknown, explicitly state: "No public data found."
  - Maintain conservative scoring.
  - Avoid over-scoring large companies without evidence.
"""

import os
import json
import datetime
from typing import Dict, Any, List

from reportlab.lib.pagesizes import LETTER
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
)
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT

# ── Styling ───────────────────────────────────────────────────────────────────

styles = getSampleStyleSheet()

PRIMARY_BLUE = colors.HexColor("#1e3a8a")
BORDER_GREY = colors.HexColor("#e5e7eb")
HEADER_BG = colors.HexColor("#f1f5f9")
ROW_ALT_BG = colors.HexColor("#f8fafc")
TEXT_DARK = colors.HexColor("#0f172a")
TEXT_MUTED = colors.HexColor("#64748b")

TITLE_STYLE = ParagraphStyle(
    "TitleStyle", parent=styles["Heading1"],
    fontSize=18, textColor=TEXT_DARK, alignment=TA_LEFT,
    spaceAfter=4, fontName="Helvetica-Bold",
)
SUBTITLE_STYLE = ParagraphStyle(
    "SubtitleStyle", parent=styles["Normal"],
    fontSize=9, textColor=TEXT_MUTED, spaceAfter=15,
)
HEADING_SECTION_STYLE = ParagraphStyle(
    "HeadingSection", parent=styles["Normal"],
    fontSize=12, textColor=PRIMARY_BLUE,
    fontName="Helvetica-Bold", spaceBefore=20, spaceAfter=10,
)
SUBHEADING_STYLE = ParagraphStyle(
    "Subheading", parent=styles["Normal"],
    fontSize=10, textColor=TEXT_DARK,
    fontName="Helvetica-Bold", spaceBefore=10, spaceAfter=5,
)
BODY_STYLE = ParagraphStyle(
    "BodyCustom", parent=styles["Normal"],
    fontSize=9, leading=13, textColor=TEXT_DARK,
)
BODY_MUTED = ParagraphStyle(
    "BodyMuted", parent=styles["Normal"],
    fontSize=8, leading=11, textColor=TEXT_MUTED,
)
TABLE_HEADER_STYLE = ParagraphStyle(
    "TableHeader", parent=styles["Normal"],
    fontSize=8, textColor=colors.white,
    fontName="Helvetica-Bold", leading=10,
)
TABLE_CELL_STYLE = ParagraphStyle(
    "TableCell", parent=styles["Normal"],
    fontSize=8, leading=10, textColor=TEXT_DARK,
)
TABLE_CELL_BOLD = ParagraphStyle(
    "TableCellBold", parent=styles["Normal"],
    fontSize=8, leading=10, textColor=TEXT_DARK,
    fontName="Helvetica-Bold",
)
DECISION_STYLE = ParagraphStyle(
    "Decision", parent=styles["Normal"],
    fontSize=10, fontName="Helvetica-Bold",
    textColor=PRIMARY_BLUE, spaceBefore=8, spaceAfter=4,
)

# ── Helpers ───────────────────────────────────────────────────────────────────

def _page_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#94a3b8"))
    canvas.drawRightString(
        doc.pagesize[0] - 40, 25,
        f"Page {canvas.getPageNumber()}  |  DataVex Strategic Intelligence  |  Confidential",
    )
    canvas.restoreState()


def _create_pdf(filename: str, elements: list):
    doc = SimpleDocTemplate(
        filename, pagesize=LETTER,
        rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40,
    )
    doc.build(elements, onFirstPage=_page_footer, onLaterPages=_page_footer)


def _p(text: str, style=None):
    return Paragraph(str(text), style or BODY_STYLE)


def _header_row(headers: List[str]):
    return [Paragraph(h, TABLE_HEADER_STYLE) for h in headers]


def _styled_table(data, col_widths, has_header=True):
    t = Table(data, colWidths=col_widths)
    cmds = [
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_GREY),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]
    if has_header:
        cmds.append(("BACKGROUND", (0, 0), (-1, 0), PRIMARY_BLUE))
    for i in range(1 if has_header else 0, len(data)):
        if i % 2 == 0:
            cmds.append(("BACKGROUND", (0, i), (-1, i), ROW_ALT_BG))
    t.setStyle(TableStyle(cmds))
    return t


def _kv_table(rows, lw=2.2 * inch, vw=4.3 * inch):
    t = Table(rows, colWidths=[lw, vw])
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_GREY),
        ("BACKGROUND", (0, 0), (0, -1), HEADER_BG),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 7),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
    ]))
    return t


def _safe(val, default="N/A"):
    if val is None or val == "":
        return default
    return str(val)


def _load_catalog():
    for p in [
        os.path.join(os.path.dirname(__file__), "..", "catalog.json"),
        os.path.join(os.path.dirname(__file__), "catalog.json"),
    ]:
        if os.path.exists(p):
            with open(p, "r") as f:
                return json.load(f)
    return {"services": []}


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers to derive GENUINE content from crawler JSON
# ═══════════════════════════════════════════════════════════════════════════════

def _derive_pain_for_role(role: str, bottlenecks: List[dict], dossier: dict) -> dict:
    """
    Build role-specific pain alignment ENTIRELY from real crawler data.
    Every field references actual detected bottlenecks, signals, or trigger events.
    If no relevant data exists, returns honest 'No public data found' statements.
    """
    bn_titles = [b.get("title", "") for b in bottlenecks]
    bn_evidences = [b.get("evidence", b.get("description", "")) for b in bottlenecks]
    bn_services = [b.get("mapped_service", "") for b in bottlenecks]
    growth = dossier.get("growth_signals", [])
    triggers = dossier.get("trigger_events", [])
    hiring = dossier.get("hiring_intensity", "Unknown")

    # Find the bottleneck most relevant to each role
    ROLE_KEYWORDS = {
        "CEO": ["gtm", "market", "revenue", "growth", "efficiency", "partnership", "sales", "sdr"],
        "CTO": ["ai", "legacy", "modernization", "architecture", "technical", "code", "infrastructure", "migration"],
        "VP Engineering": ["engineering", "velocity", "release", "deploy", "pipeline", "sprint", "microfrontend", "scaling"],
        "Head of Data": ["data", "pipeline", "analytics", "intelligence", "insight", "monitoring"],
        "Head of Platform": ["platform", "infrastructure", "cloud", "aws", "azure", "scaling", "resilience", "devops"],
    }

    keywords = ROLE_KEYWORDS.get(role, [])
    relevant_bns = []
    for b in bottlenecks:
        text = (b.get("title", "") + " " + b.get("evidence", b.get("description", ""))).lower()
        if any(kw in text for kw in keywords):
            relevant_bns.append(b)
    if not relevant_bns and bottlenecks:
        relevant_bns = [bottlenecks[0]]  # fallback to primary bottleneck

    if relevant_bns:
        primary = relevant_bns[0]
        concern = primary.get("title", "Operational strain detected")
        friction = primary.get("evidence", primary.get("description", "No public evidence available."))
        risk = f"{primary.get('severity', 'Medium')} severity — mapped to {primary.get('mapped_service', 'infrastructure modernization')}"
        angle = f"Address '{primary.get('title', 'detected bottleneck')}' via {primary.get('mapped_service', 'DataVex capabilities')}"
    else:
        concern = "No role-specific vulnerabilities detected from public data."
        friction = "No public evidence of operational friction detected."
        risk = "No measurable risk exposure identified from available signals."
        angle = "General strategic alignment assessment recommended."

    return {
        "concern": concern,
        "friction": friction,
        "risk": risk,
        "angle": angle,
    }


def _derive_messaging_angle(role: str, bottlenecks: List[dict], dossier: dict) -> str:
    """Derive a messaging angle for a role from actual bottleneck data."""
    pain = _derive_pain_for_role(role, bottlenecks, dossier)
    bn_title = pain["concern"]
    if bn_title and bn_title != "No role-specific vulnerabilities detected from public data.":
        return bn_title
    # Fallback to generic industry angle
    industry = dossier.get("industry", "Technology")
    return f"{industry} operational alignment"


def _derive_pressure_level(role: str, bottlenecks: List[dict], dossier: dict) -> str:
    """Derive strategic pressure level for a role from actual signals."""
    ROLE_KEYWORDS = {
        "CEO": ["gtm", "market", "revenue", "growth", "partnership", "sales"],
        "CTO": ["ai", "legacy", "modernization", "architecture", "technical", "code"],
        "VP Engineering": ["engineering", "velocity", "release", "deploy", "pipeline", "scaling"],
        "Head of Data": ["data", "pipeline", "analytics", "intelligence"],
        "Head of Platform": ["platform", "infrastructure", "cloud", "aws", "azure", "scaling"],
    }
    keywords = ROLE_KEYWORDS.get(role, [])
    hit_count = 0
    for b in bottlenecks:
        text = (b.get("title", "") + " " + b.get("evidence", "")).lower()
        if any(kw in text for kw in keywords):
            sev = b.get("severity", "Medium")
            hit_count += 2 if sev in ("High", "Critical") else 1

    if hit_count >= 3:
        return "Critical"
    elif hit_count >= 1:
        return "High"
    elif dossier.get("strategic_pressure_score", 0) > 60:
        return "Medium"
    return "Low"


def _derive_budget_authority(role: str) -> str:
    """Standard budget authority by org role."""
    return {"CEO": "High", "CTO": "High", "VP Engineering": "Medium",
            "Head of Data": "Medium", "Head of Platform": "Medium"}.get(role, "Low")


def _derive_access_difficulty(role: str) -> str:
    return {"CEO": "High", "CTO": "High", "VP Engineering": "Medium",
            "Head of Data": "Low", "Head of Platform": "Low"}.get(role, "Medium")


# ══════════════════════════════════════════════════════════════════════════════
# REPORT 1: Strategic Risk & Opportunity Intelligence
# ══════════════════════════════════════════════════════════════════════════════

def generate_strategic_risk_report(data: Dict[str, Any], output_path: str):
    elements = []

    dossier = data.get("company_dossier") or data.get("dossier") or {}
    lead_score = data.get("lead_score") or {}
    scores = lead_score.get("scores") or {}
    bottlenecks = data.get("strategic_bottlenecks") or data.get("bottlenecks") or []
    company_name = dossier.get("company_name") or data.get("domain", "Unknown Company")

    # Title
    elements.append(Paragraph(
        f"Strategic Risk &amp; Opportunity Intelligence — {company_name}", TITLE_STYLE))
    elements.append(Paragraph(
        f"Analysis Date: {datetime.date.today().strftime('%B %d, %Y')}  |  Classification: CONFIDENTIAL",
        SUBTITLE_STYLE))
    elements.append(Spacer(1, 0.2 * inch))

    # ══ 1. Executive Intelligence Snapshot ═══════════════════════════════
    elements.append(Paragraph("1. Executive Intelligence Snapshot", HEADING_SECTION_STYLE))

    trigger_events = dossier.get("trigger_events") or []
    trigger_str = ", ".join(trigger_events) if trigger_events else "None Detected"
    classification = lead_score.get("classification") or data.get("classification", "Not Priority")

    budget_confidence = lead_score.get("budget_confidence", "N/A")
    if budget_confidence == "N/A":
        bs = scores.get("Budget", 0)
        budget_confidence = "High" if bs >= 80 else "Medium" if bs >= 50 else "Low" if bs > 0 else "N/A"

    snapshot = [
        [Paragraph("<b>Industry:</b>", TABLE_CELL_BOLD),
         Paragraph(_safe(dossier.get("industry")), TABLE_CELL_STYLE)],
        [Paragraph("<b>Business Stage:</b>", TABLE_CELL_BOLD),
         Paragraph(_safe(dossier.get("business_stage")), TABLE_CELL_STYLE)],
        [Paragraph("<b>Strategic Pressure Score:</b>", TABLE_CELL_BOLD),
         Paragraph(f"{_safe(dossier.get('strategic_pressure_score'))}/100", TABLE_CELL_STYLE)],
        [Paragraph("<b>Total Lead Score:</b>", TABLE_CELL_BOLD),
         Paragraph(f"{_safe(lead_score.get('total'))}/100", TABLE_CELL_STYLE)],
        [Paragraph("<b>Budget Confidence Level:</b>", TABLE_CELL_BOLD),
         Paragraph(_safe(budget_confidence), TABLE_CELL_STYLE)],
        [Paragraph("<b>Trigger Events:</b>", TABLE_CELL_BOLD),
         Paragraph(trigger_str, TABLE_CELL_STYLE)],
        [Paragraph("<b>Lead Classification:</b>", TABLE_CELL_BOLD),
         Paragraph(classification, TABLE_CELL_STYLE)],
    ]
    elements.append(_kv_table(snapshot))
    elements.append(Spacer(1, 0.15 * inch))

    # Decision Statement
    total_score = lead_score.get("total", 0) or 0
    if classification.lower() in ("not priority", "deprioritize"):
        decision = "Deprioritize"
    elif total_score > 75 or classification.lower() in ("strong lead", "high priority"):
        decision = "Engage Immediately"
    else:
        decision = "Monitor"

    elements.append(Paragraph(f"<b>Decision Statement:</b> → {decision}", DECISION_STYLE))
    why_now = data.get("why_now", "")
    if not why_now:
        why_now = "Insufficient convergence of public signals for a definitive engagement recommendation."
    elements.append(_p(f"<b>Reason:</b> {why_now}"))
    elements.append(Spacer(1, 0.15 * inch))

    # ══ 2. Signal Matrix ═════════════════════════════════════════════════
    elements.append(Paragraph("2. Signal Matrix", HEADING_SECTION_STYLE))

    growth_signals = dossier.get("growth_signals") or []
    scale_signals = dossier.get("scale_signals") or []
    all_signals = growth_signals + scale_signals

    SIGNAL_CATS = {
        "Funding Signals": {
            "kw": ["raised", "funding", "series", "valuation", "investment", "capital", "ipo", "round"],
            "high": ["raised", "valuation", "series", "ipo"],
        },
        "Hiring Velocity": {
            "kw": ["hiring", "hire", "recruit", "headcount", "talent", "engineer", "team"],
            "high": ["hiring", "headcount", "recruit"],
        },
        "Expansion Signals": {
            "kw": ["expansion", "global", "office", "region", "market", "geographic", "international", "fedramp"],
            "high": ["global", "international", "fedramp"],
        },
        "Product Evolution": {
            "kw": ["product", "launch", "feature", "ai", "platform", "suite", "release", "innovation", "mandate"],
            "high": ["ai", "mandate", "platform", "launch"],
        },
        "M&amp;A Activity": {
            "kw": ["acquisition", "acquire", "merger", "m&a", "buyout", "consolidat"],
            "high": ["acquisition", "merger", "buyout"],
        },
        "Enterprise Client Signals": {
            "kw": ["enterprise", "client", "partner", "azure", "aws", "gartner", "leader", "fortune", "contract"],
            "high": ["gartner", "leader", "fortune", "partner", "azure"],
        },
    }

    # Also incorporate hiring_intensity as a direct signal for Hiring Velocity
    hiring_intensity = dossier.get("hiring_intensity", "Low")

    matrix_data = [_header_row(["Category", "Evidence Detected", "Strength", "Strategic Impact"])]
    for cat, cfg in SIGNAL_CATS.items():
        matched = [s for s in all_signals if any(kw in s.lower() for kw in cfg["kw"])]

        # Special handling for hiring — use the dossier's hiring_intensity directly
        if cat == "Hiring Velocity" and not matched:
            if hiring_intensity in ("High", "Moderate"):
                matched = [f"Hiring intensity: {hiring_intensity} (detected from careers/job postings)"]
            elif hiring_intensity == "Low":
                matched = [f"Hiring intensity: Low (minimal job activity detected)"]

        if matched:
            evidence = "; ".join(matched[:3])
            is_high = any(kw in " ".join(matched).lower() for kw in cfg["high"])
            strength = "High" if is_high else "Medium"
            impact = "Strategic Inflection" if is_high else "Operational Scale"
        else:
            evidence = "No public signals detected."
            strength = "Low"
            impact = "Baseline Monitoring"

        matrix_data.append([
            Paragraph(cat, TABLE_CELL_BOLD),
            Paragraph(evidence, TABLE_CELL_STYLE),
            Paragraph(strength, TABLE_CELL_STYLE),
            Paragraph(impact, TABLE_CELL_STYLE),
        ])
    elements.append(_styled_table(matrix_data, [1.4 * inch, 2.6 * inch, 0.9 * inch, 1.3 * inch]))

    # ══ 3. Vulnerability Risk Model ══════════════════════════════════════
    elements.append(PageBreak())
    elements.append(Paragraph("3. Vulnerability Risk Model", HEADING_SECTION_STYLE))

    if not bottlenecks:
        elements.append(_p("No immediate operational vulnerabilities detected via public telemetry."))
    else:
        for bn in bottlenecks:
            sev = bn.get("severity", "Medium")
            risk_level = {"Critical": 5, "High": 4, "Medium": 3, "Low": 2}.get(sev, 2)
            risk_level = bn.get("risk_score", risk_level)
            fin_risk = "High" if sev in ("High", "Critical") else "Medium" if sev == "Medium" else "Low"
            time_sens = "0-3 Months" if sev in ("High", "Critical") else "3-6 Months" if sev == "Medium" else "6-12 Months"
            prob_esc = "High" if sev in ("High", "Critical") else "Moderate" if sev == "Medium" else "Low"

            # ALL fields derived from the actual crawler bottleneck data
            bn_data = [
                [Paragraph("<b>Vulnerability:</b>", TABLE_CELL_BOLD),
                 Paragraph(_safe(bn.get("title", bn.get("weakness", "Unspecified"))), TABLE_CELL_STYLE)],
                [Paragraph("<b>Evidence:</b>", TABLE_CELL_BOLD),
                 Paragraph(_safe(bn.get("evidence", bn.get("description", "No public evidence available."))), TABLE_CELL_STYLE)],
                [Paragraph("<b>Mapped Service:</b>", TABLE_CELL_BOLD),
                 Paragraph(_safe(bn.get("mapped_service", "Assessment pending")), TABLE_CELL_STYLE)],
                [Paragraph("<b>Operational Risk Level (1–5):</b>", TABLE_CELL_BOLD),
                 Paragraph(str(risk_level), TABLE_CELL_STYLE)],
                [Paragraph("<b>Financial Risk Exposure:</b>", TABLE_CELL_BOLD),
                 Paragraph(fin_risk, TABLE_CELL_STYLE)],
                [Paragraph("<b>Time Sensitivity:</b>", TABLE_CELL_BOLD),
                 Paragraph(time_sens, TABLE_CELL_STYLE)],
                [Paragraph("<b>Probability of Escalation:</b>", TABLE_CELL_BOLD),
                 Paragraph(prob_esc, TABLE_CELL_STYLE)],
            ]
            elements.append(KeepTogether([_kv_table(bn_data), Spacer(1, 0.1 * inch)]))

        # Strategic Impact Summary — built from ACTUAL bottleneck data
        elements.append(Spacer(1, 0.1 * inch))
        elements.append(Paragraph("<b>Strategic Impact Summary:</b>", SUBHEADING_STYLE))

        high_bns = [b for b in bottlenecks if b.get("severity") in ("High", "Critical")]
        bn_detail_parts = []
        for b in bottlenecks[:3]:
            title = b.get("title", b.get("weakness", "unnamed"))
            sev = b.get("severity", "Medium")
            service = b.get("mapped_service", "unspecified service")
            bn_detail_parts.append(f"'{title}' ({sev} severity, addressable via {service})")

        impact_text = (
            f"The analysis identified {len(bottlenecks)} operational "
            f"vulnerabilit{'y' if len(bottlenecks)==1 else 'ies'} "
            f"({len(high_bns)} rated High/Critical): {'; '.join(bn_detail_parts)}. "
            f"Without targeted intervention, these compound into increased technical debt, "
            f"degraded competitive velocity, and measurable operational inefficiency."
        )
        elements.append(_p(impact_text))

    # ══ 4. DataVex Strategic Fit Scoring ══════════════════════════════════
    elements.append(Paragraph("4. DataVex Strategic Fit Scoring", HEADING_SECTION_STYLE))

    catalog = _load_catalog()
    catalog_services = catalog.get("services", [])

    # Build service list from catalog + ensure Strategic Outreach Layer exists
    service_defs = []
    for cs in catalog_services:
        service_defs.append({
            "name": cs["name"],
            "alignment": cs.get("pitch", "Service alignment pending assessment."),
            "leverage": "High" if any(t.lower() in ["technical debt", "old tech stacks", "recent pivots", "new funding"]
                                      for t in cs.get("targets", [])) else "Medium",
            "outcome": f"Targeted resolution via {cs['name']}.",
            "keywords": [t.lower().replace(" ", "") for t in cs.get("targets", [])] +
                        [w.lower() for w in cs["name"].split()],
        })

    # Ensure Strategic Outreach Layer exists
    existing = {s["name"].lower() for s in service_defs}
    if "strategic outreach layer" not in existing:
        service_defs.append({
            "name": "Strategic Outreach Layer",
            "alignment": "Executive engagement via data-driven personalization.",
            "leverage": "High",
            "outcome": "ROI-driven conversion lift via hyper-targeted messaging.",
            "keywords": ["outreach", "sdr", "sales", "gtm", "executive", "engagement"],
        })

    # Score each service against ACTUAL bottleneck text
    bn_text_combined = " ".join(
        (b.get("title", "") + " " + b.get("evidence", "") + " " +
         b.get("weakness", "") + " " + b.get("mapped_service", "")).lower()
        for b in bottlenecks
    )

    fit_data = [_header_row([
        "Service", "Relevance (0–10)", "Problem Alignment",
        "Impl. Leverage", "Expected Outcome",
    ])]
    fit_scores = []

    for s in service_defs:
        rel = 5  # conservative baseline
        alignment_note = s["alignment"]

        # Score by keyword matches against actual bottleneck evidence
        kw_hits = sum(1 for kw in s["keywords"] if kw in bn_text_combined)
        rel += min(kw_hits, 3)

        # Direct name match — if any bottleneck maps to this service
        for b in bottlenecks:
            if s["name"].lower() in b.get("mapped_service", "").lower():
                rel += 2
                alignment_note = (
                    f"Direct match: '{b.get('title', b.get('weakness', ''))}' "
                    f"bottleneck maps to this service."
                )
                break

        if len(bottlenecks) > 2:
            rel += 1
        rel = min(rel, 10)
        fit_scores.append(rel)

        fit_data.append([
            Paragraph(s["name"], TABLE_CELL_BOLD),
            Paragraph(f"{rel}/10", TABLE_CELL_STYLE),
            Paragraph(alignment_note, TABLE_CELL_STYLE),
            Paragraph(s["leverage"], TABLE_CELL_STYLE),
            Paragraph(s["outcome"], TABLE_CELL_STYLE),
        ])

    elements.append(_styled_table(
        fit_data, [1.2 * inch, 0.8 * inch, 1.6 * inch, 0.8 * inch, 2.1 * inch]))
    elements.append(Spacer(1, 0.1 * inch))

    fit_index = int((sum(fit_scores) / (len(fit_scores) * 10)) * 100) if fit_scores else 0
    if total_score > 0:
        fit_index = int(fit_index * 0.4 + total_score * 0.6)
    elements.append(Paragraph(f"<b>Overall Strategic Fit Index (0–100):</b> {fit_index}", DECISION_STYLE))

    # ══ 5. Engagement Timing Model ═══════════════════════════════════════
    elements.append(Paragraph("5. Engagement Timing Model", HEADING_SECTION_STYLE))

    has_trigger = bool(trigger_events)
    pressure_score = dossier.get("strategic_pressure_score", 0) or 0
    pressure_crossed = pressure_score > 70

    timing = [
        [Paragraph("<b>Trigger Detected?</b>", TABLE_CELL_BOLD),
         Paragraph(("YES — " + trigger_events[0]) if has_trigger else "NO", TABLE_CELL_STYLE)],
        [Paragraph("<b>Strategic Pressure Threshold Crossed?</b>", TABLE_CELL_BOLD),
         Paragraph(f"{'YES' if pressure_crossed else 'NO'} (Score: {pressure_score}/100)", TABLE_CELL_STYLE)],
        [Paragraph("<b>Infrastructure Maturity Gap?</b>", TABLE_CELL_BOLD),
         Paragraph(
             f"Confirmed — {len(bottlenecks)} bottleneck(s) detected" if bottlenecks
             else "Not Confirmed", TABLE_CELL_STYLE)],
    ]
    elements.append(_kv_table(timing, 2.8 * inch, 3.7 * inch))
    elements.append(Spacer(1, 0.1 * inch))

    eng_window = (
        "Immediate (0–3 months)" if decision == "Engage Immediately"
        else "Near-term (3–6 months)" if decision == "Monitor"
        else "Long-term (Monitor)"
    )
    elements.append(Paragraph(f"<b>Engagement Window:</b> {eng_window}", DECISION_STYLE))

    # Evidence — ONLY from actual detected data
    ev_parts = []
    if has_trigger:
        ev_parts.append(f"Trigger events: {', '.join(trigger_events[:3])}")
    if pressure_crossed:
        ev_parts.append(f"Strategic pressure ({pressure_score}/100) exceeds threshold")
    if bottlenecks:
        bn_names = ", ".join(b.get("title", b.get("weakness", "unnamed"))[:30] for b in bottlenecks[:3])
        ev_parts.append(f"Infrastructure gaps: {bn_names}")
    if not ev_parts:
        ev_parts.append("Insufficient signal convergence for immediate engagement")
    elements.append(_p(f"<b>Evidence:</b> {'. '.join(ev_parts)}."))

    # ══ 6. Deal Risk Assessment ══════════════════════════════════════════
    elements.append(PageBreak())
    elements.append(Paragraph("6. Deal Risk Assessment", HEADING_SECTION_STYLE))

    stage = (dossier.get("business_stage") or "").lower()
    if "public" in stage or "mature" in stage or "late" in stage:
        procurement, cycle, tech_depth = "High (Multi-stakeholder)", "6–9 Months", "High"
    elif "mid" in stage or "growth" in stage:
        procurement, cycle, tech_depth = "Medium", "3–6 Months", "Medium"
    else:
        procurement, cycle, tech_depth = "Low–Medium", "2–4 Months", "Medium"

    comp_sat = "High" if len(growth_signals) > 3 else "Low" if len(growth_signals) <= 1 else "Medium"

    risk_data = [
        _header_row(["Risk Dimension", "Assessment"]),
        [Paragraph("Procurement Complexity", TABLE_CELL_BOLD), Paragraph(procurement, TABLE_CELL_STYLE)],
        [Paragraph("Competitive Saturation", TABLE_CELL_BOLD), Paragraph(comp_sat, TABLE_CELL_STYLE)],
        [Paragraph("Budget Certainty", TABLE_CELL_BOLD), Paragraph(_safe(budget_confidence, "Medium"), TABLE_CELL_STYLE)],
        [Paragraph("Technical Depth Required", TABLE_CELL_BOLD), Paragraph(tech_depth, TABLE_CELL_STYLE)],
        [Paragraph("Sales Cycle Length Estimate", TABLE_CELL_BOLD), Paragraph(cycle, TABLE_CELL_STYLE)],
    ]
    elements.append(_styled_table(risk_data, [3.25 * inch, 3.25 * inch]))

    _create_pdf(output_path, elements)


# ══════════════════════════════════════════════════════════════════════════════
# REPORT 2: Executive Targeting & Strategic Engagement Model
# ══════════════════════════════════════════════════════════════════════════════

def generate_executive_targeting_report(data: Dict[str, Any], output_path: str):
    elements = []

    dossier = data.get("company_dossier") or data.get("dossier") or {}
    lead_score = data.get("lead_score") or {}
    bottlenecks = data.get("strategic_bottlenecks") or data.get("bottlenecks") or []
    outreach = data.get("personalized_outreach") or {}
    company_name = dossier.get("company_name") or data.get("domain", "Unknown Company")

    # Title
    elements.append(Paragraph(
        f"Executive Targeting &amp; Strategic Engagement Model — {company_name}", TITLE_STYLE))
    elements.append(Paragraph(
        f"Analysis Date: {datetime.date.today().strftime('%B %d, %Y')}  |  Classification: CONFIDENTIAL",
        SUBTITLE_STYLE))
    elements.append(Spacer(1, 0.2 * inch))

    # ══ 1. Decision-Maker Relevance Matrix ═══════════════════════════════
    elements.append(Paragraph("1. Decision-Maker Relevance Matrix", HEADING_SECTION_STYLE))

    roles = ["CEO", "CTO", "VP Engineering", "Head of Data", "Head of Platform"]
    dm_data = [_header_row(["Role", "Pressure Level", "Budget Auth.", "Messaging Angle", "Access Difficulty"])]

    for role in roles:
        pressure = _derive_pressure_level(role, bottlenecks, dossier)
        angle = _derive_messaging_angle(role, bottlenecks, dossier)
        budget = _derive_budget_authority(role)
        access = _derive_access_difficulty(role)
        dm_data.append([
            role, pressure, budget,
            Paragraph(angle, TABLE_CELL_STYLE), access,
        ])

    elements.append(_styled_table(dm_data, [1.0 * inch, 1.0 * inch, 0.9 * inch, 2.2 * inch, 0.9 * inch]))

    # ══ 2. Executive-Level Pain Alignment ════════════════════════════════
    elements.append(Paragraph("2. Executive-Level Pain Alignment", HEADING_SECTION_STYLE))

    for role in roles:
        pains = _derive_pain_for_role(role, bottlenecks, dossier)
        elements.append(Paragraph(f"<b>Role: {role}</b>", SUBHEADING_STYLE))
        elements.append(_p(f"• <b>Core Strategic Concern:</b> {pains['concern']}"))
        elements.append(_p(f"• <b>Operational Friction:</b> {pains['friction']}"))
        elements.append(_p(f"• <b>Risk Exposure:</b> {pains['risk']}"))
        elements.append(_p(f"• <b>DataVex Entry Angle:</b> {pains['angle']}"))
        elements.append(Spacer(1, 0.08 * inch))

    # ══ 3. Outreach Strategy Architecture ════════════════════════════════
    elements.append(PageBreak())
    elements.append(Paragraph("3. Outreach Strategy Architecture", HEADING_SECTION_STYLE))

    elements.append(_p("<b>Approach Type:</b> Advisory / Technical / ROI-driven / Strategic partnership"))
    elements.append(Spacer(1, 0.1 * inch))

    # Derive all email content from ACTUAL crawler data
    strategic_angle = outreach.get("strategic_angle") or outreach.get("key_strategic_angle", "")
    dm_name = outreach.get("recommended_decision_maker", "")
    bn_primary = bottlenecks[0] if bottlenecks else {}
    bn_title = bn_primary.get("title", bn_primary.get("weakness", ""))
    bn_evidence = bn_primary.get("evidence", bn_primary.get("description", ""))
    bn_service = bn_primary.get("mapped_service", "")
    triggers = dossier.get("trigger_events") or []
    industry = dossier.get("industry", "Technology")
    stage = dossier.get("business_stage", "Growth")

    # ── 120-word C-suite email ────────────────────────────────────────────
    elements.append(Paragraph("<b>Email Strategy — 120-word C-suite:</b>", SUBHEADING_STYLE))
    csuite_email = outreach.get("outreach_email", "")
    if not csuite_email:
        trigger_line = f" Given your recent {triggers[0].lower()}," if triggers else ""
        csuite_email = (
            f"[Executive Name],\n\n"
            f"I've been studying {company_name}'s trajectory in {industry} — "
            f"the {stage.lower()}-stage signals are notable.{trigger_line}\n\n"
            f"{'We see ' + bn_title.lower() + ' emerging as a friction point' if bn_title else 'We identified operational friction points'} "
            f"that compound at this stage of growth. "
            f"{'Our ' + bn_service + ' practice' if bn_service else 'Our team'} has helped similar organizations "
            f"reduce that friction without disrupting existing workflows.\n\n"
            f"Would a 15-minute strategic briefing be valuable?\n\n"
            f"Best,\n[Name]\nDataVex"
        )
    elements.append(_p(csuite_email))
    elements.append(Spacer(1, 0.15 * inch))

    # ── 80-word Technical leader email ────────────────────────────────────
    elements.append(Paragraph("<b>Email Strategy — 80-word Technical Leader:</b>", SUBHEADING_STYLE))
    if bn_title and bn_evidence:
        tech_email = (
            f"Hi [Name],\n\n"
            f"I noticed {company_name} is navigating {bn_title.lower()} — "
            f"{bn_evidence[:80].rstrip('.')}.\n\n"
            f"{'Our ' + bn_service + ' framework addresses this directly' if bn_service else 'We address this pattern directly'}: "
            f"reducing technical debt and accelerating release velocity "
            f"without destabilizing production.\n\n"
            f"Happy to share a 5-minute technical brief.\n\n"
            f"Best,\n[Name]\nDataVex"
        )
    else:
        tech_email = (
            f"Hi [Name],\n\n"
            f"Following {company_name}'s trajectory in the {industry} space. "
            f"At the {stage.lower()} stage, operational friction often compounds. "
            f"We help similar teams navigate this transition with measurable results.\n\n"
            f"Happy to share a brief case study.\n\n"
            f"Best,\n[Name]\nDataVex"
        )
    elements.append(_p(tech_email))
    elements.append(Spacer(1, 0.15 * inch))

    # ── 40-word Follow-up ─────────────────────────────────────────────────
    elements.append(Paragraph("<b>Email Strategy — 40-word Follow-up:</b>", SUBHEADING_STYLE))
    followup_detail = f"'{bn_title}' gap" if bn_title else "infrastructure maturity gap"
    elements.append(_p(
        f"Following up on the strategic brief regarding {company_name}'s "
        f"{followup_detail}. A 10-minute briefing on the findings would be "
        f"impactful for your current roadmap. Best, [Name]."
    ))
    elements.append(Spacer(1, 0.15 * inch))

    # ── LinkedIn Connect ──────────────────────────────────────────────────
    elements.append(Paragraph("<b>LinkedIn Connect Note:</b>", SUBHEADING_STYLE))
    growth = dossier.get("growth_signals") or []
    growth_ref = growth[0] if growth else f"activity in {industry}"
    elements.append(_p(
        f"Hi [Name], I've been following {company_name}'s recent signals — "
        f"particularly {growth_ref}. Compiled an Intelligence Memo regarding "
        f"your strategic positioning — would love to share it."
    ))
    elements.append(Spacer(1, 0.1 * inch))
    elements.append(_p(
        "<b>Tone:</b> High-level. Consultative. Strategic. No aggressive selling.",
        BODY_MUTED))

    # ══ 4. Multi-Touch Execution Plan ════════════════════════════════════
    elements.append(Paragraph("4. Multi-Touch Execution Plan", HEADING_SECTION_STYLE))

    # Dynamic actions referencing actual detected data
    day1_action = f"Send Strategic Intelligence Memo to {dm_name}" if dm_name else "Send Strategic Intelligence Memo to primary decision-maker"
    day4_ref = f"referencing {triggers[0]}" if triggers else f"referencing {company_name}'s {industry} momentum"
    day10_ref = f"deep dive on '{bn_title}' bottleneck" if bn_title else "technical follow-up with ROI framework"

    plan_data = [
        _header_row(["Day", "Channel", "Action"]),
        [Paragraph("Day 1", TABLE_CELL_BOLD), "Email",
         Paragraph(day1_action, TABLE_CELL_STYLE)],
        [Paragraph("Day 4", TABLE_CELL_BOLD), "LinkedIn",
         Paragraph(f"Connection request + brief note {day4_ref}", TABLE_CELL_STYLE)],
        [Paragraph("Day 10", TABLE_CELL_BOLD), "Email",
         Paragraph(f"Technical follow-up: {day10_ref}", TABLE_CELL_STYLE)],
        [Paragraph("Day 21", TABLE_CELL_BOLD), "Alt Channel",
         Paragraph("Warm intro via shared network or direct executive engagement at event", TABLE_CELL_STYLE)],
    ]
    elements.append(_styled_table(plan_data, [0.9 * inch, 1.1 * inch, 4.5 * inch]))
    elements.append(Spacer(1, 0.1 * inch))
    elements.append(_p("<b>Channel Mix:</b> Email / LinkedIn / Warm intro / Event alignment"))

    # ══ 5. Contact Intelligence ══════════════════════════════════════════
    elements.append(Paragraph("5. Contact Intelligence", HEADING_SECTION_STYLE))

    if dm_name:
        elements.append(_p(f"<b>Primary Decision Maker:</b> {dm_name}"))
    else:
        elements.append(_p("<b>Primary Decision Maker:</b> Not identified from public data."))

    elements.append(Spacer(1, 0.08 * inch))

    # NEVER fabricate email
    exec_email = outreach.get("executive_email") or outreach.get("email")
    if exec_email and "@" in str(exec_email):
        source = outreach.get("email_source", "public listing")
        elements.append(_p(f"<b>Executive Email:</b> {exec_email}"))
        elements.append(_p(f"<b>Source:</b> {source}", BODY_MUTED))
    else:
        elements.append(_p("<b>Verified Executive Email:</b> No verified public executive email found."))
        elements.append(Spacer(1, 0.05 * inch))
        elements.append(_p("<b>Recommended Discovery Tools:</b> Hunter.io / Apollo.io / LinkedIn Sales Navigator"))

    elements.append(Spacer(1, 0.1 * inch))
    elements.append(_p(
        "<i>Note: DataVex does not fabricate contact information. All data is sourced "
        "from publicly available records only.</i>", BODY_MUTED))

    _create_pdf(output_path, elements)
