"""
backend/reports.py — DataVex Evidence-Based PDF Report Generator
================================================================
Generates clean, company-specific PDF reports using ONLY data
present in the analysis payload. No boilerplate. No fabrication.
No templated fallbacks. No outreach if score < 70.
"""

import datetime
from typing import Any, Dict, List

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# ── Color tokens ──────────────────────────────────────────────────────────────

NAVY       = colors.HexColor("#0f172a")
BLUE_DARK  = colors.HexColor("#1e3a8a")
BLUE_MID   = colors.HexColor("#3b82f6")
GREY_LIGHT = colors.HexColor("#f1f5f9")
GREY_LINE  = colors.HexColor("#cbd5e1")
TEXT_DARK  = colors.HexColor("#1e293b")
TEXT_MID   = colors.HexColor("#475569")
WHITE      = colors.white

GREEN      = colors.HexColor("#059669")
AMBER      = colors.HexColor("#d97706")
RED        = colors.HexColor("#dc2626")

# ── Paragraph styles ──────────────────────────────────────────────────────────

_base = getSampleStyleSheet()

TITLE = ParagraphStyle(
    "Title", parent=_base["Normal"],
    fontSize=16, fontName="Helvetica-Bold",
    textColor=NAVY, spaceAfter=4, leading=22,
)
SUBTITLE = ParagraphStyle(
    "Subtitle", parent=_base["Normal"],
    fontSize=9, fontName="Helvetica",
    textColor=TEXT_MID, spaceAfter=14,
)
SECTION = ParagraphStyle(
    "Section", parent=_base["Normal"],
    fontSize=10, fontName="Helvetica-Bold",
    textColor=BLUE_DARK, spaceBefore=16, spaceAfter=6,
    borderPad=0,
)
BODY = ParagraphStyle(
    "Body", parent=_base["Normal"],
    fontSize=9, fontName="Helvetica",
    textColor=TEXT_DARK, leading=13, spaceAfter=4,
)
BODY_ITALIC = ParagraphStyle(
    "BodyItalic", parent=BODY,
    fontName="Helvetica-Oblique", textColor=TEXT_MID,
)
LABEL = ParagraphStyle(
    "Label", parent=_base["Normal"],
    fontSize=8, fontName="Helvetica-Bold", textColor=TEXT_DARK,
)
CELL = ParagraphStyle(
    "Cell", parent=_base["Normal"],
    fontSize=8, fontName="Helvetica", textColor=TEXT_DARK, leading=11,
)
TH = ParagraphStyle(
    "TH", parent=_base["Normal"],
    fontSize=8, fontName="Helvetica-Bold", textColor=WHITE,
)

# ── Helpers ───────────────────────────────────────────────────────────────────

def _doc(path: str):
    return SimpleDocTemplate(
        path, pagesize=LETTER,
        leftMargin=0.55 * inch, rightMargin=0.55 * inch,
        topMargin=0.5 * inch, bottomMargin=0.5 * inch,
    )

def _rule():
    """Thin horizontal rule via a 1-row table."""
    t = Table([[""]], colWidths=[7.4 * inch])
    t.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), 0.5, GREY_LINE),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return t

def _kv_table(rows: List[List], col_w=(1.8 * inch, 5.6 * inch)):
    """Two-column key-value fact table."""
    t = Table(rows, colWidths=list(col_w))
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), GREY_LIGHT),
        ("FONTNAME",   (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE",   (0, 0), (-1, -1), 8),
        ("GRID",       (0, 0), (-1, -1), 0.4, GREY_LINE),
        ("VALIGN",     (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",  (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
    ]))
    return t

def _score_color(score: int):
    if score >= 70: return GREEN
    if score >= 40: return AMBER
    return RED

def _classification_label(score: int, classification: str) -> str:
    if classification:
        return classification
    if score >= 70: return "Strong Lead"
    if score >= 40: return "Medium Lead"
    return "Not Priority"

def _bullets(items: List[str], elements: list):
    """Render a list of strings as bullet points."""
    for item in items:
        elements.append(Paragraph(f"  \u2022  {item}", BODY))

def _section(title: str, elements: list):
    elements.append(Spacer(1, 0.06 * inch))
    elements.append(_rule())
    elements.append(Paragraph(title, SECTION))

# ── Report: Lead Intelligence Report (single unified PDF) ─────────────────────

def _report_header(data: dict, elements: list):
    dossier = data.get("company_dossier") or data.get("dossier") or {}
    company = dossier.get("company_name") or data.get("domain", "Unknown")
    domain  = data.get("domain", "")
    date    = datetime.date.today().strftime("%B %d, %Y")

    elements.append(Paragraph(f"Lead Intelligence Report: {company}", TITLE))
    elements.append(Paragraph(
        f"Domain: {domain}  |  Generated: {date}  |  DataVex Strategic Engine",
        SUBTITLE,
    ))


def _section_overview(dossier: dict, elements: list):
    _section("1. Company Overview", elements)

    industry = dossier.get("industry") or None
    stage    = dossier.get("business_stage") or None
    offering = dossier.get("primary_offering") or dossier.get("business_type") or None
    geo      = dossier.get("geographic_scope") or dossier.get("geography") or None
    summary  = dossier.get("summary") or dossier.get("company_summary") or None

    rows = []
    if industry: rows.append(["Industry:", industry])
    if stage   : rows.append(["Business Stage:", stage])
    if offering: rows.append(["Primary Offering:", offering])
    if geo     : rows.append(["Geographic Scope:", geo])

    if rows:
        elements.append(_kv_table(rows))
    else:
        elements.append(Paragraph("Company profile data not available from public sources.", BODY_ITALIC))

    if summary:
        elements.append(Spacer(1, 0.08 * inch))
        elements.append(Paragraph(summary, BODY))


def _section_signals(dossier: dict, elements: list):
    _section("2. Verified Public Signals", elements)

    signal_items = []

    hiring = dossier.get("hiring_intensity")
    if hiring and hiring.lower() not in ("unknown", "none", "n/a", ""):
        signal_items.append(f"Hiring Intensity: {hiring}")

    for sig in dossier.get("growth_signals") or []:
        signal_items.append(sig)

    for sig in dossier.get("scale_signals") or []:
        signal_items.append(sig)

    for evt in dossier.get("trigger_events") or []:
        signal_items.append(f"Trigger Event: {evt}")

    for sig in dossier.get("product_signals") or []:
        signal_items.append(f"Product: {sig}")

    for sig in dossier.get("enterprise_signals") or []:
        signal_items.append(f"Enterprise: {sig}")

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for s in signal_items:
        if s not in seen:
            seen.add(s)
            unique.append(s)

    if unique:
        _bullets(unique, elements)
    else:
        elements.append(Paragraph(
            "No major growth or trigger signals detected from available public data.",
            BODY_ITALIC,
        ))


def _section_evaluation(dossier: dict, lead_score: dict, elements: list):
    _section("3. Lead Evaluation", elements)

    scores = lead_score.get("scores") or {}
    total  = lead_score.get("total") or 0
    cls    = _classification_label(total, lead_score.get("classification", ""))

    rows = []
    if scores.get("Industry Fit"): rows.append(["Industry Fit:", str(scores["Industry Fit"])])
    if scores.get("Growth"):       rows.append(["Growth Indicators:", str(scores["Growth"])])
    if scores.get("Bottlenecks"):  rows.append(["Operational Complexity:", str(scores["Bottlenecks"])])
    if scores.get("Alignment"):    rows.append(["Service Alignment:", str(scores["Alignment"])])

    if rows and lead_score.get("has_trigger_event"):
        rows.append(["Trigger Event:", "Yes — strategic window open"])

    if rows:
        elements.append(_kv_table(rows))
        elements.append(Spacer(1, 0.08 * inch))

    score_color = _score_color(total)
    score_style = ParagraphStyle(
        "ScoreStyle", parent=BODY,
        fontName="Helvetica-Bold", fontSize=11,
        textColor=score_color,
    )
    elements.append(Paragraph(
        f"Lead Score: {total}/100  |  Classification: {cls}",
        score_style,
    ))


def _section_verdict(data: dict, lead_score: dict, elements: list):
    _section("4. Verdict", elements)

    why_now = data.get("why_now") or ""
    total   = lead_score.get("total") or 0
    cls     = _classification_label(total, lead_score.get("classification", ""))

    # Build verdict from actual data — never from template strings
    if why_now and len(why_now.strip()) > 20:
        elements.append(Paragraph(why_now.strip(), BODY))
    elif total < 40:
        elements.append(Paragraph(
            f"{data.get('domain', 'This company')} does not meet the qualification threshold "
            f"(score {total}/100). No engagement is recommended at this time based on available signals.",
            BODY,
        ))
    elif total < 70:
        elements.append(Paragraph(
            f"{data.get('domain', 'This company')} shows limited signals warranting engagement "
            f"(score {total}/100, classification: {cls}). Monitor for future trigger events before outreach.",
            BODY,
        ))
    else:
        elements.append(Paragraph(
            f"{data.get('domain', 'This company')} qualifies for active engagement "
            f"(score {total}/100, classification: {cls}). Proceed with outreach as detailed below.",
            BODY,
        ))


def _section_outreach(data: dict, elements: list):
    """Only called when score >= 70."""
    _section("5. Outreach Strategy", elements)

    outreach = data.get("personalized_outreach") or data.get("outreach") or {}

    dm      = outreach.get("recommended_decision_maker") or ""
    angle   = outreach.get("key_strategic_angle") or outreach.get("strategic_angle") or ""
    email   = outreach.get("outreach_email") or ""

    rows = []
    if dm   : rows.append(["Decision Maker:", dm])
    if angle: rows.append(["Strategic Angle:", Paragraph(angle, CELL)])
    if rows:
        elements.append(_kv_table(rows))
        elements.append(Spacer(1, 0.08 * inch))

    if email:
        elements.append(Paragraph("Executive Outreach Draft:", LABEL))
        elements.append(Spacer(1, 0.04 * inch))
        # Render each line of the email as a separate paragraph
        for line in email.strip().split("\n"):
            line = line.strip()
            if line:
                elements.append(Paragraph(line, BODY))
            else:
                elements.append(Spacer(1, 0.04 * inch))
    else:
        elements.append(Paragraph("No outreach draft available in analysis data.", BODY_ITALIC))


def _section_bottlenecks(data: dict, elements: list):
    _section("5b. Strategic Bottlenecks", elements)

    bottlenecks = data.get("strategic_bottlenecks") or data.get("bottlenecks") or []

    if not bottlenecks:
        elements.append(Paragraph(
            "No strategic bottlenecks detected from available public data.", BODY_ITALIC,
        ))
        return

    for bn in bottlenecks:
        title    = bn.get("title") or "Bottleneck"
        evidence = bn.get("evidence") or bn.get("description") or ""
        service  = bn.get("mapped_service") or ""
        severity = bn.get("severity") or ""

        rows = [["Bottleneck:", title]]
        if evidence: rows.append(["Evidence:", Paragraph(evidence, CELL)])
        if service : rows.append(["Mapped Service:", service])
        if severity: rows.append(["Severity:", severity])

        elements.append(_kv_table(rows))
        elements.append(Spacer(1, 0.06 * inch))


def _section_trace(data: dict, dossier: dict, elements: list):
    _section("6. Agent Research Trace", elements)

    trace = data.get("agent_research_trace") or dossier.get("research_trace") or []

    if not trace:
        elements.append(Paragraph(
            "No research trace recorded for this analysis.", BODY_ITALIC,
        ))
        return

    for step in trace:
        if isinstance(step, dict):
            detail = step.get("detail") or step.get("step") or str(step)
            step_n = step.get("step", "")
            tag    = step.get("type", "")
            line   = f"Step {step_n}: [{tag}] {detail}" if step_n else f"[{tag}] {detail}" if tag else detail
        else:
            line = str(step)
        elements.append(Paragraph(f"  \u2022  {line}", BODY))


# ── Public API ────────────────────────────────────────────────────────────────

def generate_strategic_risk_report(data: Dict[str, Any], output_path: str):
    """
    Strategic Risk & Opportunity Intelligence Report.
    Evidence-based. No boilerplate. No fabrication.
    """
    elements: list = []

    dossier    = data.get("company_dossier") or data.get("dossier") or {}
    lead_score = data.get("lead_score") or {}
    total      = lead_score.get("total") or 0

    _report_header(data, elements)
    _section_overview(dossier, elements)
    _section_signals(dossier, elements)
    _section_evaluation(dossier, lead_score, elements)
    _section_verdict(data, lead_score, elements)

    # Outreach only if score >= 70
    if total >= 70:
        _section_outreach(data, elements)

    _section_bottlenecks(data, elements)
    _section_trace(data, dossier, elements)

    _doc(output_path).build(elements)


def generate_executive_targeting_report(data: Dict[str, Any], output_path: str):
    """
    Executive Targeting & Engagement Blueprint.
    Only generated when score >= 70. Contains outreach, trace, and context.
    If score < 70: produces a minimal disqualification summary.
    """
    elements: list = []

    dossier    = data.get("company_dossier") or data.get("dossier") or {}
    lead_score = data.get("lead_score") or {}
    total      = lead_score.get("total") or 0

    _report_header(data, elements)

    if total < 70:
        _section("Engagement Status", elements)
        cls = _classification_label(total, lead_score.get("classification", ""))
        elements.append(Paragraph(
            f"Lead Score: {total}/100  |  Classification: {cls}", BODY,
        ))
        elements.append(Spacer(1, 0.08 * inch))
        elements.append(Paragraph(
            "This company does not meet the minimum qualification threshold (70/100) "
            "for executive outreach. No outreach strategy has been generated. "
            "Re-evaluate if new trigger events are detected.",
            BODY,
        ))
        elements.append(Spacer(1, 0.12 * inch))
        _section_signals(dossier, elements)
        _section_trace(data, dossier, elements)
    else:
        _section_overview(dossier, elements)
        _section_signals(dossier, elements)
        _section_evaluation(dossier, lead_score, elements)
        _section_verdict(data, lead_score, elements)
        _section_outreach(data, elements)
        _section_trace(data, dossier, elements)

    _doc(output_path).build(elements)
