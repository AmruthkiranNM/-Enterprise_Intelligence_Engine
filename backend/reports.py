"""
backend/reports.py — Decision-Grade Strategic PDF Generation
============================================================
Generates Board-ready PDF reports from DataVex intelligence JSON.
Utilizes reportlab.platypus for structured, high-fidelity layouts.
Tone: Analytical, investment-grade, crisp.
"""

import os
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
)
from reportlab.lib.units import inch

# ── Styling ───────────────────────────────────────────────────────────────────

styles = getSampleStyleSheet()

# Corporate Blue-Black Theme
PRIMARY_BLUE = colors.HexColor("#1e3a8a")
BORDER_GREY = colors.HexColor("#e5e7eb")
HEADER_BG = colors.HexColor("#f1f5f9")
TEXT_DARK = colors.HexColor("#0f172a")
TEXT_MUTED = colors.HexColor("#64748b")

TITLE_STYLE = ParagraphStyle(
    "TitleStyle",
    parent=styles["Heading1"],
    fontSize=18,
    textColor=TEXT_DARK,
    alignment=0,  # Left
    spaceAfter=15,
    fontName="Helvetica-Bold",
)

HEADING_SECTION_STYLE = ParagraphStyle(
    "HeadingSection",
    parent=styles["Normal"],
    fontSize=12,
    textColor=PRIMARY_BLUE,
    fontName="Helvetica-Bold",
    spaceBefore=20,
    spaceAfter=10,
    textTransform="uppercase",
)

SUBHEADING_STYLE = ParagraphStyle(
    "Subheading",
    parent=styles["Normal"],
    fontSize=10,
    textColor=TEXT_DARK,
    fontName="Helvetica-Bold",
    spaceBefore=10,
    spaceAfter=5,
)

BODY_STYLE = styles["Normal"]
BODY_STYLE.fontSize = 9
BODY_STYLE.leading = 12
BODY_STYLE.textColor = TEXT_DARK

TABLE_HEADER_STYLE = ParagraphStyle(
    "TableHeader",
    parent=styles["Normal"],
    fontSize=8,
    textColor=colors.white,
    fontName="Helvetica-Bold",
)

TABLE_CELL_STYLE = ParagraphStyle(
    "TableCell",
    parent=styles["Normal"],
    fontSize=8,
    leading=10,
)

# ── Helper ───────────────────────────────────────────────────────────────────

def create_pdf(filename: str, elements: list):
    doc = SimpleDocTemplate(
        filename,
        pagesize=LETTER,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )
    doc.build(elements)

# ── Report 1: Strategic Risk & Opportunity Intelligence ─────────────────────

def generate_strategic_risk_report(data: Dict[str, Any], output_path: str):
    elements = []

    dossier = data.get("company_dossier") or data.get("dossier") or {}
    lead_score = data.get("lead_score") or {}
    company_name = dossier.get("company_name") or data.get("domain", "Unknown Company")
    
    # Header
    elements.append(Paragraph(f"Strategic Intelligence Report — {company_name}", TITLE_STYLE))
    elements.append(Paragraph(f"Generated on {datetime.date.today().strftime('%B %d, %Y')} | DataVex Strategic Engine", BODY_STYLE))
    elements.append(Spacer(1, 0.25 * inch))

    # 1. Company Intelligence Dossier
    elements.append(Paragraph("1. Company Intelligence Dossier", HEADING_SECTION_STYLE))
    
    snapshot_data = [
        ["Industry:", dossier.get("industry", "N/A")],
        ["Business Type:", dossier.get("business_type", "N/A")],
        ["Business Stage:", dossier.get("business_stage", "N/A")],
        ["Hiring Intensity:", dossier.get("hiring_intensity", "N/A")],
        ["Strategic Pressure Score:", f"{dossier.get('strategic_pressure_score', 'N/A')}/100"],
        ["Signal Density:", f"{dossier.get('signal_count', 0)} detected signals"],
    ]
    
    t_snap = Table(snapshot_data, colWidths=[2 * inch, 4.5 * inch])
    t_snap.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_GREY),
        ('BACKGROUND', (0, 0), (0, -1), HEADER_BG),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(t_snap)
    elements.append(Spacer(1, 0.15 * inch))

    # 2. Justified Lead Verdict & Strategic Timing
    elements.append(Paragraph("2. Justified Lead Verdict & Strategic Timing", HEADING_SECTION_STYLE))
    
    classification = lead_score.get("classification") or data.get("classification", "Not Priority")
    total_score = lead_score.get("total", 0)
    
    v_color = "#10b981" if total_score >= 70 else "#f59e0b" if total_score >= 40 else "#ef4444"
    verdict_style = ParagraphStyle("Verdict", parent=BODY_STYLE, fontName="Helvetica-Bold", textColor=colors.HexColor(v_color), fontSize=11)

    elements.append(Paragraph(f"Engagement Verdict: {classification} ({total_score}/100)", verdict_style))
    elements.append(Spacer(1, 0.1 * inch))
    
    elements.append(Paragraph("<b>Strategic Justification (Why Now?):</b>", SUBHEADING_STYLE))
    reason = data.get("why_now") or dossier.get("why_now") or "Strategic validation based on converging growth signals and infrastructure maturity gaps."
    elements.append(Paragraph(reason, BODY_STYLE))
    elements.append(Spacer(1, 0.2 * inch))

    # 3. Outreach Strategy Summary
    elements.append(Paragraph("3. Outreach Strategy Summary", HEADING_SECTION_STYLE))
    outreach = data.get("personalized_outreach") or data.get("outreach") or {}
    
    if outreach:
        outreach_data = [
            ["Decision Maker:", outreach.get("recommended_decision_maker", "CTO / VP Engineering")],
            ["Strategic Angle:", Paragraph(outreach.get("key_strategic_angle", "Modernization & Infrastructure Maturity"), TABLE_CELL_STYLE)],
            ["Closing Question:", Paragraph(outreach.get("closing_question", "Would it make sense to share a brief case study?"), TABLE_CELL_STYLE)],
        ]
        t_out = Table(outreach_data, colWidths=[2 * inch, 4.5 * inch])
        t_out.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, BORDER_GREY),
            ('BACKGROUND', (0, 0), (0, -1), HEADER_BG),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('PADDING', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(t_out)
    else:
        elements.append(Paragraph("Outreach not recommended for current lead priority.", BODY_STYLE))
    elements.append(Spacer(1, 0.2 * inch))

    # 4. Agent Research Journey Trace
    elements.append(Paragraph("4. Agent Research Journey Trace", HEADING_SECTION_STYLE))
    trace = data.get("agent_research_trace") or dossier.get("research_trace") or []
    
    if trace:
        for i, step in enumerate(trace):
            elements.append(Paragraph(f"<b>Step {i+1}:</b> {step}", BODY_STYLE))
            elements.append(Spacer(1, 0.05 * inch))
    else:
        elements.append(Paragraph("No research trace available for this analysis.", BODY_STYLE))

    elements.append(PageBreak())

    # 5. Signal Matrix & Evidence
    elements.append(Paragraph("5. Signal Matrix & Evidence", HEADING_SECTION_STYLE))
    
    matrix_headers = [
        Paragraph("Category", TABLE_HEADER_STYLE),
        Paragraph("Evidence Detected", TABLE_HEADER_STYLE),
        Paragraph("Strength", TABLE_HEADER_STYLE),
        Paragraph("Strategic Impact", TABLE_HEADER_STYLE)
    ]
    
    def get_signal_row(cat, signals_list):
        evidence = "No specific signals found."
        strength = "Low"
        impact = "Monitoring"
        
        for sig in signals_list:
            if cat.lower()[:5] in sig.lower():
                evidence = sig
                strength = "High" if any(x in sig.lower() for x in ["raised", "growth", "expansion"]) else "Medium"
                break
        
        if strength == "High": impact = "Strategic Inflection"
        elif strength == "Medium": impact = "Operational Scale"
        
        return [cat, Paragraph(evidence, TABLE_CELL_STYLE), strength, impact]

    all_signals = dossier.get("growth_signals", []) + dossier.get("scale_signals", []) + dossier.get("trigger_events", [])
    matrix_data = [matrix_headers]
    categories = ["Funding", "Hiring", "Expansion", "Product", "M&A", "Enterprise"]
    for c in categories:
        matrix_data.append(get_signal_row(c, all_signals))

    t_matrix = Table(matrix_data, colWidths=[1.1 * inch, 3.0 * inch, 1.2 * inch, 1.2 * inch])
    t_matrix.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_BLUE),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_GREY),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(t_matrix)

    # 6. Technical Vulnerability Model
    elements.append(Paragraph("6. Technical Vulnerability & Bottlenecks", HEADING_SECTION_STYLE))
    bottlenecks = data.get("strategic_bottlenecks") or data.get("bottlenecks") or []
    
    if not bottlenecks:
        elements.append(Paragraph("No immediate operational vulnerabilities detected via public telemetry.", BODY_STYLE))
    else:
        for bn in bottlenecks:
            bn_data = [
                ["Vulnerability:", Paragraph(bn.get("title", "Strain"), TABLE_CELL_STYLE)],
                ["Evidence:", Paragraph(bn.get("evidence", bn.get("description", "Inferred")), TABLE_CELL_STYLE)],
                ["Mapped Service:", bn.get("mapped_service", "N/A")],
                ["Severity:", bn.get("severity", "Medium")],
            ]
            t_bn = Table(bn_data, colWidths=[2 * inch, 4.5 * inch])
            t_bn.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 0.5, BORDER_GREY),
                ('BACKGROUND', (0, 0), (0, -1), HEADER_BG),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('PADDING', (0, 0), (-1, -1), 5),
            ]))
            elements.append(t_bn)
            elements.append(Spacer(1, 0.1 * inch))

    create_pdf(output_path, elements)

# ── Report 2: Executive Targeting & Strategic Engagement Model ──────────────

def generate_executive_targeting_report(data: Dict[str, Any], output_path: str):
    elements = []

    dossier = data.get("company_dossier") or data.get("dossier") or {}
    company_name = dossier.get("company_name") or data.get("domain", "Unknown Company")
    outreach = data.get("personalized_outreach") or data.get("outreach") or {}
    
    # Title
    elements.append(Paragraph(f"Engagement Blueprint — {company_name}", TITLE_STYLE))
    elements.append(Paragraph(f"Analysis Date: {datetime.date.today().strftime('%B %d, %Y')}", BODY_STYLE))
    elements.append(Spacer(1, 0.25 * inch))

    # 1. Target Decision Maker
    elements.append(Paragraph("1. Primary Decision Maker & Target Role", HEADING_SECTION_STYLE))
    dm_role = outreach.get("recommended_decision_maker", "CTO / VP Engineering")
    elements.append(Paragraph(f"<b>Recommended Persona:</b> {dm_role}", BODY_STYLE))
    
    dm_justification = "Based on detected technical bottlenecks and infrastructure modernization requirements."
    elements.append(Paragraph(f"<b>Rationale:</b> {dm_justification}", BODY_STYLE))
    elements.append(Spacer(1, 0.1 * inch))

    # 2. Executive Outreach Strategy
    elements.append(Paragraph("2. Executive Outreach Strategy", HEADING_SECTION_STYLE))
    elements.append(Paragraph("<b>Messaging Angle:</b> Advisory / Results-Driven", BODY_STYLE))
    elements.append(Spacer(1, 0.15 * inch))

    elements.append(Paragraph("<b>Draft Executive Email (~120 words):</b>", SUBHEADING_STYLE))
    email_text = outreach.get("outreach_email") or "Strategic engagement draft pending priority qualification."
    elements.append(Paragraph(email_text, BODY_STYLE))
    elements.append(Spacer(1, 0.2 * inch))

    # 3. Decision-Maker Relevance Matrix
    elements.append(Paragraph("3. Decision-Maker Relevance Matrix", HEADING_SECTION_STYLE))
    
    matrix_headers = [Paragraph(h, TABLE_HEADER_STYLE) for h in ["Role", "Pressure Level", "Budget Authority", "Messaging Angle", "Difficulty"]]
    matrix_data = [
        matrix_headers,
        ["CEO", "High", "High", "Market Dominance", "High"],
        ["CTO", "Critical", "High", "Modernization", "High"],
        ["VP Engineering", "High", "Medium", "Velocity", "Medium"],
        ["Platform Head", "High", "Medium", "Resilience", "Low"],
    ]
    t_dm = Table(matrix_data, colWidths=[1.1 * inch, 1.2 * inch, 1.2 * inch, 1.8 * inch, 1.2 * inch])
    t_dm.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_BLUE),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_GREY),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(t_dm)

    # 4. Multi-Touch Execution Plan
    elements.append(Paragraph("4. Multi-Touch Execution Plan", HEADING_SECTION_STYLE))
    plan_data = [
        ["Day 1", "Email", "Send Strategic Intelligence Report"],
        ["Day 4", "LinkedIn", "Connection Request + Research Note"],
        ["Day 10", "Email", "Technical Follow-up on specific bottleneck"],
        ["Day 21", "Call", "Direct executive briefing attempt"],
    ]
    t_plan = Table(plan_data, colWidths=[1 * inch, 1.5 * inch, 4 * inch])
    t_plan.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_GREY),
        ('BACKGROUND', (0, 0), (0, -1), HEADER_BG),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(t_plan)
    elements.append(Spacer(1, 0.2 * inch))

    # 5. Research Journey Trace Summary
    elements.append(Paragraph("5. Research Journey Trace Summary", HEADING_SECTION_STYLE))
    trace = data.get("agent_research_trace") or dossier.get("research_trace") or []
    if trace:
        elements.append(Paragraph("The analysis was conducted through a multi-step strategic research process:", BODY_STYLE))
        elements.append(Spacer(1, 0.05 * inch))
        for step in trace[:5]: # Show top 5 steps
            elements.append(Paragraph(f"• {step}", BODY_STYLE))
    
    create_pdf(output_path, elements)
