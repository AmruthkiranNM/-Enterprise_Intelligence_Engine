"""
report_agent.py — Assembles final JSON & generates outreach
"""

def generate_report(prospect_profile, context_signals, gap_analysis, verdict_data, service_catalog) -> dict:
    
    verdict = verdict_data.get("lead_verdict", "Unknown")
    company_name = service_catalog.get("company_name", "Our Team")
    
    outreach_email = ""
    if verdict in ["Strong Lead", "Medium Lead"] and gap_analysis:
        primary_gap = gap_analysis[0]
        gap_desc = primary_gap.get('gap', 'operational workflows').lower()
        service = primary_gap.get('matched_service', 'digital solutions')
        
        trigger_mention = "been following your recent momentum. Growing companies "
        for c in context_signals:
            if "expanding" in c.lower() or "expansion" in c.lower():
                trigger_mention = "noticed your company's expansion. Companies scaling operations "
                break
            elif "funding" in c.lower() or "raised" in c.lower():
                trigger_mention = "congratulations on the recent funding. Scaling companies "
                break
                
        outreach_email = (
            f"Hi,\n\n"
            f"We've {trigger_mention}often face challenges managing {gap_desc}.\n\n"
            f"Our platform helps automate and streamline this exact process through our {service}. "
            f"Would it make sense to connect and share how we've helped similar teams?\n\n"
            f"Best,\n{company_name}"
        )
    else:
        outreach_email = "Not generated (Weak Lead)"
        
    agent_trace = [
        "Discovery: Located targeted prospect",
        "Auditing: Scraped company website for profile metrics",
        "Context: Collected external intelligence signals",
        "Gap Analysis: Analyzed prospect profile against user's Service Catalog",
        f"Verdict: Classified as {verdict} based on {len(gap_analysis)} gaps"
    ]
        
    return {
        "prospect_profile": {
            "domain": prospect_profile.get("domain", ""),
            "industry": prospect_profile.get("industry", ""),
            "business_stage": prospect_profile.get("business_stage", ""),
            "services_offered": prospect_profile.get("services_offered", []),
            "technology_mentions": prospect_profile.get("technology_mentions", [])
        },
        "context_signals": context_signals,
        "gap_analysis": gap_analysis,
        "lead_verdict": verdict,
        "outreach_email": outreach_email,
        "agent_trace": agent_trace
    }
