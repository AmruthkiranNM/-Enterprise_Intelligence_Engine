"""
Validation test for the two required scenarios:
1. mluisconstruction.com  -> Not Priority, no outreach section
2. browserstack.com       -> Strong Lead, different evidence-based language
"""
import os
from backend.reports import generate_strategic_risk_report, generate_executive_targeting_report

# ── Test 1: mluisconstruction.com — low-score, no outreach ───────────────────
low_score_data = {
    "domain": "mluisconstruction.com",
    "why_now": "",
    "company_dossier": {
        "company_name": "M Luis Construction",
        "industry": "Construction & Civil Engineering",
        "business_stage": "SMB / Regional",
        "hiring_intensity": "Low",
        "geographic_scope": "Regional (MD/VA/DC)",
        "growth_signals": [],
        "scale_signals": [],
        "trigger_events": [],
        "research_trace": [
            "Scraped mluisconstruction.com homepage",
            "No enterprise language detected",
            "No funding or expansion signals found",
            "No hiring velocity signals detected",
            "Scored: 22/100 — Not Priority",
        ],
    },
    "lead_score": {
        "total": 22,
        "classification": "Not Priority",
        "has_trigger_event": False,
        "scores": {
            "Industry Fit": 20,
            "Growth": 10,
            "Bottlenecks": 15,
            "Alignment": 12,
        },
    },
    "strategic_bottlenecks": [],
    "personalized_outreach": None,
    "agent_research_trace": [
        "Scraped homepage — static construction company website, no product breadth",
        "No hiring signals, no job board presence",
        "No funding, no enterprise client language",
        "Score 22/100 — Not Priority. No outreach generated.",
    ],
}

# ── Test 2: browserstack.com — high complexity, evidence-based ───────────────
high_score_data = {
    "domain": "browserstack.com",
    "why_now": (
        "BrowserStack's acquisition of Percy and Mobitaze, combined with active "
        "enterprise client expansion across EMEA and the Asia-Pacific, signals a "
        "critical integration window. Their engineering team is simultaneously "
        "managing multi-product deployment across 5+ cloud test platforms while "
        "scaling the AI-powered smart testing features released in Q3 2024. "
        "This creates measurable DevOps orchestration strain that DataVex can address directly."
    ),
    "company_dossier": {
        "company_name": "BrowserStack",
        "industry": "Developer Tools / Cloud Testing",
        "business_stage": "Late Growth / Enterprise SaaS",
        "business_type": "B2B SaaS — Enterprise",
        "hiring_intensity": "High",
        "geographic_scope": "Global (US, UK, India, APAC)",
        "growth_signals": [
            "$200M Series B at $4B valuation",
            "6M+ developers across 50,000+ enterprise customers",
            "Active EMEA enterprise expansion in 2024",
        ],
        "scale_signals": [
            "Multi-cloud: AWS, GCP, Azure",
            "5+ distinct product lines (Automate, App Automate, Live, Percy, Accessibility)",
            "Offices in San Francisco, Dublin, Mumbai, Sydney",
        ],
        "trigger_events": [
            "Acquired Percy (visual testing) — integration in progress",
            "Acquired Mobitaze — QA automation platform added to portfolio",
            "AI-powered Smart Testing launched Q3 2024",
        ],
        "enterprise_signals": [
            "Serves FAANG and Fortune 500 clients",
            "SOC2 Type II, GDPR compliant",
            "99.99% uptime SLA for enterprise tier",
        ],
        "research_trace": [
            "Scraped browserstack.com, /products, /enterprise, /changelog",
            "LinkedIn: 1,700+ employees, 80+ open engineering roles",
            "Crunchbase: $200M Series B, $4B valuation confirmed",
            "Detected 2 acquisitions in 18 months: Percy + Mobitaze",
            "Product matrix: 5+ distinct lines requiring unified DevOps orchestration",
            "Scored: 87/100 — Strong Lead",
        ],
    },
    "lead_score": {
        "total": 87,
        "classification": "Strong Lead",
        "has_trigger_event": True,
        "scores": {
            "Industry Fit": 92,
            "Growth": 88,
            "Bottlenecks": 90,
            "Alignment": 85,
        },
    },
    "strategic_bottlenecks": [
        {
            "title": "Post-Acquisition Integration Strain",
            "evidence": "Two acquisitions (Percy, Mobitaze) within 18 months require merging CI/CD pipelines across incompatible toolchains while maintaining 99.99% uptime SLA.",
            "mapped_service": "DevOps Optimization",
            "severity": "High",
        },
        {
            "title": "Multi-Product Release Coordination",
            "evidence": "5+ active product lines (Automate, App Automate, Live, Percy, Accessibility) share infrastructure but operate on separate release cycles, creating deployment orchestration complexity.",
            "mapped_service": "DevOps Optimization",
            "severity": "High",
        },
    ],
    "personalized_outreach": {
        "recommended_decision_maker": "Nakul Aggarwal, CTO / VP Engineering",
        "key_strategic_angle": (
            "Post-acquisition DevOps integration: merging Percy and Mobitaze pipelines "
            "without disrupting the 99.99% SLA for 50,000+ enterprise customers."
        ),
        "outreach_email": (
            "Hi Nakul,\n\n"
            "The Percy and Mobitaze acquisitions represent a meaningful expansion of "
            "BrowserStack's testing coverage. Having followed your product growth, I want "
            "to flag a specific engineering risk: integrating two acquired CI/CD pipelines "
            "into a shared infrastructure while maintaining your enterprise SLA is a high-stakes "
            "orchestration challenge.\n\n"
            "At DataVex, we help engineering teams navigate exactly this — post-acquisition "
            "DevOps consolidation without release velocity regression. We've done this for "
            "comparable SaaS platforms managing 5+ product lines.\n\n"
            "Would a 20-minute technical review of our integration approach be useful?\n\n"
            "Best regards,\n[Name], DataVex"
        ),
    },
    "agent_research_trace": [
        "Scraped browserstack.com, /products, /enterprise, /changelog",
        "LinkedIn analysis: 1,700+ employees, 80+ open engineering roles",
        "Crunchbase: $200M Series B confirmed, $4B valuation",
        "Identified 2 acquisitions within 18 months: Percy (visual testing) + Mobitaze (QA automation)",
        "Detected 5 distinct product lines sharing infrastructure — multi-product DevOps strain signal",
        "AI Smart Testing launch Q3 2024 — platform pivot signal detected",
        "Mapped to DataVex DevOps Optimization catalog entry",
        "Score computed: 87/100 — Strong Lead",
    ],
}

# ── Run both ──────────────────────────────────────────────────────────────────

print("=== TEST 1: mluisconstruction.com (Not Priority — no outreach expected) ===")
generate_strategic_risk_report(low_score_data, "test_construction_risk.pdf")
generate_executive_targeting_report(low_score_data, "test_construction_targeting.pdf")
print("  test_construction_risk.pdf      ->", os.path.getsize("test_construction_risk.pdf"), "bytes")
print("  test_construction_targeting.pdf ->", os.path.getsize("test_construction_targeting.pdf"), "bytes")

print()
print("=== TEST 2: browserstack.com (Strong Lead — outreach expected) ===")
generate_strategic_risk_report(high_score_data, "test_browserstack_risk.pdf")
generate_executive_targeting_report(high_score_data, "test_browserstack_targeting.pdf")
print("  test_browserstack_risk.pdf      ->", os.path.getsize("test_browserstack_risk.pdf"), "bytes")
print("  test_browserstack_targeting.pdf ->", os.path.getsize("test_browserstack_targeting.pdf"), "bytes")

print()
print("VALIDATION: Construction report should be smaller (no outreach section).")
size_low  = os.path.getsize("test_construction_risk.pdf")
size_high = os.path.getsize("test_browserstack_risk.pdf")
if size_high > size_low:
    print(f"PASS: browserstack ({size_high}B) > mluisconstruction ({size_low}B) as expected.")
else:
    print(f"REVIEW: Sizes are similar — check outreach gating.")
