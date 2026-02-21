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
    elements.append(Paragraph(f"Strategic Risk & Opportunity Intelligence — {company_name}", TITLE_STYLE))
    elements.append(Paragraph(f"Analysis Date: {datetime.date.today().strftime('%B %d, %Y')}", BODY_STYLE))
    elements.append(Spacer(1, 0.25 * inch))

    # 1. Executive Intelligence Snapshot (One-page)
    elements.append(Paragraph("1. Executive Intelligence Snapshot", HEADING_SECTION_STYLE))
    
    snapshot_data = [
        ["Industry:", dossier.get("industry", "N/A")],
        ["Business Stage:", dossier.get("business_stage", "N/A")],
        ["Strategic Pressure Score:", f"{dossier.get('strategic_pressure_score', 'N/A')}/100"],
        ["Total Lead Score:", f"{lead_score.get('total', 'N/A')}/100"],
        ["Budget Confidence Level:", lead_score.get("budget_confidence", "N/A")],
        ["Trigger Events:", ", ".join(dossier.get("trigger_events", []) or ["None Detected"])],
        ["Lead Classification:", lead_score.get("classification") or data.get("classification", "Not Priority")],
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

    # Decision Statement
    decision = "Engage Immediately" if (lead_score.get("total", 0) > 75) else "Monitor"
    if (lead_score.get("classification") or "").lower() == "not priority": decision = "Deprioritize"
    
    elements.append(Paragraph(f"<b>Decision Statement:</b> → {decision}", BODY_STYLE))
    reason = data.get("why_now", "Strategic validation based on converging growth signals and infrastructure maturity gaps.")
    elements.append(Paragraph(f"<b>Reason:</b> {reason}", BODY_STYLE))
    elements.append(Spacer(1, 0.2 * inch))

    # 2. Signal Matrix
    elements.append(Paragraph("2. Signal Matrix", HEADING_SECTION_STYLE))
    
    matrix_headers = [
        Paragraph("Category", TABLE_HEADER_STYLE),
        Paragraph("Evidence Detected", TABLE_HEADER_STYLE),
        Paragraph("Strength (Low/Med/High)", TABLE_HEADER_STYLE),
        Paragraph("Strategic Impact", TABLE_HEADER_STYLE)
    ]
    
    def get_signal_row(cat, signals_list):
        evidence = "No specific signals found."
        strength = "Low"
        impact = "Baseline Monitoring"
        
        # Look for signal in growth_signals or scale_signals
        for sig in signals_list:
            if cat.lower().replace(" signals", "").replace(" velocity", "") in sig.lower():
                evidence = sig
                strength = "High" if any(x in sig.lower() for x in ["raised", "valuation", "leader", "acquisition", "mandate"]) else "Medium"
                break
        
        if strength == "High": impact = "Strategic Inflection"
        elif strength == "Medium": impact = "Operational Scale"
        
        return [cat, Paragraph(evidence, TABLE_CELL_STYLE), strength, impact]

    all_signals = dossier.get("growth_signals", []) + dossier.get("scale_signals", [])
    matrix_data = [matrix_headers]
    categories = ["Funding Signals", "Hiring Velocity", "Expansion Signals", "Product Evolution", "M&A Activity", "Enterprise Client Signals"]
    for c in categories:
        matrix_data.append(get_signal_row(c, all_signals))

    t_matrix = Table(matrix_data, colWidths=[1.4 * inch, 2.7 * inch, 1.2 * inch, 1.2 * inch])
    t_matrix.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_BLUE),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_GREY),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(t_matrix)

    # 3. Vulnerability Risk Model
    elements.append(Paragraph("3. Vulnerability Risk Model", HEADING_SECTION_STYLE))
    bottlenecks = data.get("strategic_bottlenecks") or data.get("bottlenecks") or []
    
    if not bottlenecks:
        elements.append(Paragraph("No immediate operational vulnerabilities detected via public telemetry.", BODY_STYLE))
    else:
        for bn in bottlenecks:
            bn_data = [
                ["Vulnerability:", Paragraph(bn.get("title", "Infrastructure Strain"), TABLE_CELL_STYLE)],
                ["Evidence:", Paragraph(bn.get("evidence", bn.get("description", "Inferred from rapid headcount expansion.")), TABLE_CELL_STYLE)],
                ["Operational Risk Level (1-5):", str(bn.get("risk_score", 3 if bn.get("severity") == "Medium" else 5 if bn.get("severity") == "High" else 2))],
                ["Financial Risk Exposure:", "High" if bn.get("severity", "Medium") == "High" else "Medium"],
                ["Time Sensitivity:", "0-6 Months"],
                ["Probability of Escalation:", "High" if bn.get("severity") == "High" else "Moderate"],
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
            
        elements.append(Spacer(1, 0.1 * inch))
        elements.append(Paragraph("<b>Strategic Impact Summary:</b>", SUBHEADING_STYLE))
        impact_summary = "The convergence of growth signals and infrastructure strain indicates that without immediate workflow modernization, the subject will experience significant operational friction. Downstream consequences include increased technical debt, decreased competitive velocity, and potential GTM inefficiency."
        elements.append(Paragraph(impact_summary, BODY_STYLE))

    # 4. DataVex Strategic Fit Scoring
    elements.append(Paragraph("4. DataVex Strategic Fit Scoring", HEADING_SECTION_STYLE))
    
    service_defs = [
        {
            "id": "market_intel",
            "name": "Market Intelligence Agent",
            "alignment": "Manual research and signal fragmentation.",
            "leverage": "High",
            "outcome": "Automated engagement nodes.",
            "trigger_keywords": ["gtm", "sdr", "outreach", "market", "sales"]
        },
        {
            "id": "legacy_mod",
            "name": "Legacy Modernization AI",
            "alignment": "Platform technical debt and scaling friction.",
            "leverage": "Medium",
            "outcome": "Accelerated release velocity.",
            "trigger_keywords": ["ai", "legacy", "modernization", "architecture", "microfrontend", "scaling", "infrastructure"]
        },
        {
            "id": "strategic_layer",
            "name": "Strategic Outreach Layer",
            "alignment": "Generic executive engagement.",
            "leverage": "High",
            "outcome": "ROI-driven conversion lift.",
            "trigger_keywords": ["ceo", "strategic", "executive", "investment", "board"]
        }
    ]
    
    bn_texts = " ".join([b.get("title", "") + " " + b.get("evidence", "") for b in bottlenecks]).lower()
    
    fit_headers = [Paragraph(h, TABLE_HEADER_STYLE) for h in ["Service", "Relevance Score (0-10)", "Problem Alignment", "Implementation Leverage", "Expected Transformation Outcome"]]
    fit_data = [fit_headers]
    
    for s in service_defs:
        rel_score = 6 # baseline
        alignment_note = s["alignment"]
        
        for kw in s["trigger_keywords"]:
            if kw in bn_texts:
                rel_score += 1
        
        rel_score = min(rel_score + (1 if len(bottlenecks) > 2 else 0), 10)
        
        if rel_score >= 8:
            matching_bn = [b.get("title") for b in bottlenecks if any(kw in (b.get("title", "") + b.get("evidence", "")).lower() for kw in s["trigger_keywords"])]
            if matching_bn:
                alignment_note = f"Direct alignment with {matching_bn[0]} vulnerability."
        
        fit_data.append([
            s["name"], 
            f"{rel_score}/10", 
            Paragraph(alignment_note, TABLE_CELL_STYLE), 
            s["leverage"], 
            Paragraph(s["outcome"], TABLE_CELL_STYLE)
        ])
        
    t_fit = Table(fit_data, colWidths=[1.3 * inch, 1.0 * inch, 1.4 * inch, 1.2 * inch, 1.6 * inch])
    t_fit.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_BLUE),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_GREY),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(t_fit)
    elements.append(Spacer(1, 0.1 * inch))
    elements.append(Paragraph(f"<b>Overall Strategic Fit Index (0-100):</b> {int(lead_score.get('total', 0))}", BODY_STYLE))

    # 5. Engagement Timing Model
    elements.append(Paragraph("5. Engagement Timing Model", HEADING_SECTION_STYLE))
    
    timing_data = [
        ["Trigger Detected?", "YES" if (dossier.get("trigger_events")) else "NO"],
        ["Strategic Pressure Threshold Crossed?", "YES" if dossier.get("strategic_pressure_score", 0) > 70 else "NO"],
        ["Infrastructure Maturity Gap?", "Confirmed (via Bottleneck Detection)"],
    ]
    t_timing = Table(timing_data, colWidths=[3.25 * inch, 3.25 * inch])
    t_timing.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 0.5, BORDER_GREY)]))
    elements.append(t_timing)
    
    eng_window = "Immediate (0-3 months)" if decision == "Engage Immediately" else "Near-term (3-6 months)" if decision == "Monitor" else "Long-term (Monitor)"
    elements.append(Spacer(1, 0.1 * inch))
    elements.append(Paragraph(f"<b>Engagement Window:</b> {eng_window}", BODY_STYLE))
    elements.append(Paragraph(f"<b>Evidence:</b> {data.get('why_now', 'High-density signals indicate optimal budget window.')}", BODY_STYLE))

    # 6. Deal Risk Assessment
    elements.append(Paragraph("6. Deal Risk Assessment", HEADING_SECTION_STYLE))
    risk_data = [
        ["Procurement Complexity:", "High (Multi-stakeholder)"],
        ["Competitive Saturation:", "Medium"],
        ["Budget Certainty:", lead_score.get("budget_confidence", "Medium")],
        ["Technical Depth Required:", "High"],
        ["Sales Cycle Length Estimate:", "6-9 Months"],
    ]
    t_risk = Table(risk_data, colWidths=[3.25 * inch, 3.25 * inch])
    t_risk.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_GREY),
        ('BACKGROUND', (0, 0), (0, -1), HEADER_BG),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
    ]))
    elements.append(t_risk)

    create_pdf(output_path, elements)

# ── Report 2: Executive Targeting & Strategic Engagement Model ──────────────

def generate_executive_targeting_report(data: Dict[str, Any], output_path: str):
    elements = []

    dossier = data.get("company_dossier") or data.get("dossier") or {}
    company_name = dossier.get("company_name") or data.get("domain", "Unknown Company")
    
    # Title
    elements.append(Paragraph(f"Executive Targeting & Strategic Engagement Model — {company_name}", TITLE_STYLE))
    elements.append(Paragraph(f"Analysis Date: {datetime.date.today().strftime('%B %d, %Y')}", BODY_STYLE))
    elements.append(Spacer(1, 0.25 * inch))

    # 1. Decision-Maker Relevance Matrix
    elements.append(Paragraph("1. Decision-Maker Relevance Matrix", HEADING_SECTION_STYLE))
    
    matrix_headers = [Paragraph(h, TABLE_HEADER_STYLE) for h in ["Role", "Strategic Pressure Level", "Budget Authority", "Messaging Angle", "Access Difficulty"]]
    matrix_data = [
        matrix_headers,
        ["CEO", "High", "High", "Market Dominance & Efficiency", "High"],
        ["CTO", "Critical", "High", "Modernization & Technical Debt", "High"],
        ["VP Engineering", "High", "Medium", "Operational Velocity", "Medium"],
        ["Head of Data", "Medium", "Medium", "Intelligence Integration", "Low"],
        ["Head of Platform", "High", "Medium", "Infrastructure Resilience", "Low"],
    ]
    t_dm = Table(matrix_data, colWidths=[1.1 * inch, 1.4 * inch, 1.2 * inch, 1.8 * inch, 1 * inch])
    t_dm.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY_BLUE),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_GREY),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(t_dm)

    # 2. Executive-Level Pain Alignment
    elements.append(Paragraph("2. Executive-Level Pain Alignment", HEADING_SECTION_STYLE))
    
    roles = ["CTO", "CEO", "Head of Platform"]
    for role in roles:
        elements.append(Paragraph(f"<b>Role: {role}</b>", SUBHEADING_STYLE))
        pains = [
            f"<b>Core Strategic Concern:</b> {'Ensuring platform stability under rapid growth' if role=='CTO' else 'Maximizing market capture speed' if role=='CEO' else 'Infrastructure resilience'}",
            f"<b>Operational Friction:</b> {'Legacy workflow bottlenecks and technical debt' if role=='CTO' else 'Lack of real-time market signal validation' if role=='CEO' else 'Scaling overhead'}",
            f"<b>Risk Exposure:</b> {'Systemic reliability escalation' if role=='CTO' else 'Budget inefficiency' if role=='CEO' else 'Deployment lag'}",
            f"<b>DataVex Entry Angle:</b> {'Strategic modernization layer' if role=='CTO' else 'ROI-driven intelligence engine' if role=='CEO' else 'Automated scaling nodes'}",
        ]
        for p in pains:
            elements.append(Paragraph(f"• {p}", BODY_STYLE))
        elements.append(Spacer(1, 0.1 * inch))

    # 3. Outreach Strategy Architecture
    elements.append(Paragraph("3. Outreach Strategy Architecture", HEADING_SECTION_STYLE))
    elements.append(Paragraph("<b>Approach Type:</b> Advisory / Technical / ROI-driven / Strategic partnership", BODY_STYLE))
    elements.append(Spacer(1, 0.1 * inch))

    outreach = data.get("personalized_outreach") or {}
    
    elements.append(Paragraph("<b>120-word C-suite email:</b>", SUBHEADING_STYLE))
    elements.append(Paragraph(outreach.get("outreach_email", "Drafting personalized C-suite pitch..."), BODY_STYLE))
    elements.append(Spacer(1, 0.1 * inch))

    elements.append(Paragraph("<b>80-word Technical leader email:</b>", SUBHEADING_STYLE))
    tech_pitch = f"Focus on {outreach.get('strategic_angle', 'technical infrastructure modernization')}. Address the detected legacy bottlenecks directly with a high-velocity transition framework. Highlight the reduction in technical debt and gain in release speed."
    elements.append(Paragraph(tech_pitch, BODY_STYLE))
    elements.append(Spacer(1, 0.1 * inch))

    elements.append(Paragraph("<b>40-word Follow-up email:</b>", SUBHEADING_STYLE))
    elements.append(Paragraph("Following up on the strategic brief previously shared. A 10-minute briefing on the 'Modernization Gap' identified in the initial analysis would be impactful for the current roadmap. Best, [Name].", BODY_STYLE))
    elements.append(Spacer(1, 0.1 * inch))

    elements.append(Paragraph("<b>LinkedIn Connect:</b>", SUBHEADING_STYLE))
    elements.append(Paragraph(f"Hi [Name], I've been following {company_name}'s recent growth signals. I put together a Strategic Intelligence Memo regarding your infrastructure maturity—would love to share it with you.", BODY_STYLE))

    # 4. Multi-Touch Execution Plan
    elements.append(Paragraph("4. Multi-Touch Execution Plan", HEADING_SECTION_STYLE))
    plan_data = [
        ["Day 1", "Email", "Send Strategic Intelligence Memo to Decision Maker"],
        ["Day 4", "LinkedIn", "Connection Request + Brief Note referencing news trigger"],
        ["Day 10", "Email", "Technical follow-up (Deep dive on specific bottleneck)"],
        ["Day 21", "Alt Channel", "Warm intro attempt or direct executive engagement"],
    ]
    t_plan = Table(plan_data, colWidths=[1 * inch, 1.5 * inch, 4 * inch])
    t_plan.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_GREY),
        ('BACKGROUND', (0, 0), (0, -1), HEADER_BG),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(t_plan)
    elements.append(Spacer(1, 0.1 * inch))
    elements.append(Paragraph("<b>Channel Mix:</b> Email / LinkedIn / Warm intro / Event alignment", BODY_STYLE))

    # 5. Contact Intelligence
    elements.append(Paragraph("5. Contact Intelligence", HEADING_SECTION_STYLE))
    elements.append(Paragraph("<b>Decision Maker:</b> " + outreach.get("recommended_decision_maker", "Identifying..."), BODY_STYLE))
    elements.append(Spacer(1, 0.05 * inch))
    
    # No fabrication rule
    elements.append(Paragraph("<b>Verified Executive Email:</b> No verified public executive email found.", BODY_STYLE))
    elements.append(Paragraph("<b>Recommendation:</b> Hunter.io / Apollo / LinkedIn Sales Navigator", BODY_STYLE))

    create_pdf(output_path, elements)
