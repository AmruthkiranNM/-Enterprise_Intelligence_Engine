import os
import json
from backend.reports import generate_strategic_risk_report, generate_executive_targeting_report

def test_generate_refined_reports():
    # Sample data mimicking the backend result structure
    sample_data = {
        "domain": "acme-corp.com",
        "why_now": "Converging growth signals in SaaS and Enterprise sectors combined with recent Series C funding creates an optimal window for infrastructure modernization.",
        "company_dossier": {
            "company_name": "Acme Corp",
            "industry": "SaaS",
            "business_type": "Enterprise / Global",
            "business_stage": "Mature",
            "hiring_intensity": "High",
            "strategic_pressure_score": 85,
            "signal_count": 12,
            "growth_signals": ["Verified large-scale funding", "Market expansion confirmed"],
            "scale_signals": ["Enterprise-scale workforce", "Global footprint"],
            "trigger_events": ["Executive leadership transition", "Series C funding round"],
            "research_trace": [
                "Scraped homepage and /careers",
                "Detected 12 strategic signals",
                "Identified infrastructure bottlenecks",
                "Calculated strategic pressure: 85/100"
            ]
        },
        "lead_score": {
            "total": 88,
            "classification": "Strong Lead",
            "budget_confidence": "High"
        },
        "strategic_bottlenecks": [
            {
                "title": "Scaling Infrastructure Strain",
                "evidence": "Rapid hiring in engineering (50+ roles) and global expansion.",
                "mapped_service": "Cloud Modernization",
                "severity": "High"
            }
        ],
        "personalized_outreach": {
            "recommended_decision_maker": "CTO",
            "key_strategic_angle": "Technical debt reduction for global expansion",
            "closing_question": "Are you seeing deployment lag as you scale to these new regions?",
            "outreach_email": "Hi [Name], Acme Corp's expansion is impressive. I noticed the infrastructure strain..."
        },
        "agent_research_trace": [
            "Analyzed acme-corp.com",
            "Detected funding and hiring velocity",
            "Calculated pressure score 85",
            "Generated outreach for CTO"
        ]
    }

    report1_path = "test_risk_report.pdf"
    report2_path = "test_targeting_report.pdf"

    print("Generating refined Strategic Risk Report...")
    generate_strategic_risk_report(sample_data, report1_path)
    print(f"Created: {os.path.abspath(report1_path)}")

    print("\nGenerating refined Executive Targeting Report...")
    generate_executive_targeting_report(sample_data, report2_path)
    print(f"Created: {os.path.abspath(report2_path)}")

    # Check if files exist and are not empty
    if os.path.exists(report1_path) and os.path.getsize(report1_path) > 0:
        print("\nSUCCESS: Report 1 generated successfully.")
    else:
        print("\nFAILURE: Report 1 missing or empty.")

    if os.path.exists(report2_path) and os.path.getsize(report2_path) > 0:
        print("SUCCESS: Report 2 generated successfully.")
    else:
        print("FAILURE: Report 2 missing or empty.")

if __name__ == "__main__":
    test_generate_refined_reports()
