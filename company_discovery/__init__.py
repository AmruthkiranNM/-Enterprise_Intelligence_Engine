"""
Company Discovery & Revenue Estimation Module
===============================================
Discovers companies in a given region and estimates whether they
likely meet or exceed a specified revenue threshold using public signals only.

Usage:
    from company_discovery import discover_companies
    results = discover_companies(region="Pune", revenue_threshold="1Cr+")
"""

from company_discovery.main import discover_companies

__all__ = ["discover_companies"]
