"""
Company Discovery & Intelligence Engine
=========================================
Dual-mode enterprise system for B2B sales intelligence.

Modes:
    REGION MODE:  discover_companies(region, threshold)
    DOMAIN MODE:  research_domain(domain, threshold)

Usage:
    from company_discovery import discover_companies, research_domain

    # Region mode
    results = discover_companies("Pune", "1Cr+")

    # Domain mode
    report = research_domain("druva.com", "10Cr+")
"""

from company_discovery.main import (
    run_region_pipeline as discover_companies,
    run_domain_pipeline as research_domain,
)

__all__ = ["discover_companies", "research_domain"]
