"""
auditor_agent.py — Auditor Agent
Scrapes prospect website and builds Prospect Company Profile.
Wraps `build_dossier()`.
"""

from company_discovery.intelligence import build_dossier

def run_auditor(domain: str) -> dict:
    dossier = build_dossier(domain)
    
    # Heuristics to extract tools and services from raw text
    raw_text = dossier.get("_full_text", "").lower()
    
    tech_tools = ["aws", "azure", "jira", "salesforce", "hubspot", "oracle", "sap"]
    services_keywords = ["platform", "api", "mobile app", "web app", "consulting", "managed services"]
    
    detected_tools = [t for t in tech_tools if t in raw_text]
    detected_services = [s for s in services_keywords if s in raw_text]
    
    return {
        "domain": domain,
        "industry": dossier.get("industry", "Unknown"),
        "business_stage": dossier.get("business_stage", "Unknown"),
        "business_type": dossier.get("business_type", "Unknown"),
        "hiring_intensity": dossier.get("hiring_intensity", "Unknown"),
        "services_offered": detected_services if detected_services else ["Core Business Operations"],
        "technology_mentions": detected_tools,
        "scale_signals": dossier.get("scale_signals", []),
        "raw_text": raw_text
    }
