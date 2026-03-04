"""
gap_analysis_agent.py — Gap Analyst Agent
Compares Service Catalog vs Prospect Profile + Context.
Identifies operational gaps.
"""

def identify_gaps(service_catalog: dict, prospect_profile: dict, context_signals: list) -> list:
    gaps = []
    catalog_services = service_catalog.get("services", [])
    prospect_industry = prospect_profile.get("industry", "").lower()
    context_text = " ".join(context_signals).lower()
    
    has_expansion = "expansion" in context_text or "expand" in context_text
    has_funding = "funding" in context_text or "raised" in context_text
    has_hiring = prospect_profile.get("hiring_intensity") == "High"
    
    for service in catalog_services:
        service_lower = service.lower()
        # Evaluate context for gap creation
        if (has_expansion or has_hiring) and any(kw in service_lower for kw in ["software", "automation", "cloud", "digital"]):
            gaps.append({
                "gap": f"Operational scaling gap during expansion",
                "evidence": f"Prospect is scaling quickly, typically requiring {service}",
                "matched_service": service
            })
            continue # Don't double add the same service
            
        if has_funding and any(kw in service_lower for kw in ["security", "data", "engineering", "devops"]):
            gaps.append({
                "gap": f"Enterprise readiness gap post-funding",
                "evidence": f"Recent capital injection requires enterprise-grade {service}",
                "matched_service": service
            })
            continue
            
    # Fallback gap
    if not gaps and catalog_services:
        gaps.append({
            "gap": f"Modernization opportunity in {prospect_industry}",
            "evidence": "General operational friction typical for the industry",
            "matched_service": catalog_services[0]
        })
        
    return gaps
