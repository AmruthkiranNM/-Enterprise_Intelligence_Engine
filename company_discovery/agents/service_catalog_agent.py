"""
service_catalog_agent.py — Self-Awareness Onboarding Agent
Crawls the user company website. Extracts:
- Services offered
- Industry focus
- Core expertise
- Products
- Technologies mentioned
"""

import re
from urllib.parse import urlparse
from company_discovery.scraper import _fetch_page
from company_discovery.intelligence import _scrape_subpages, _extract_text_from_pages, _detect_industry

def build_service_catalog(company_url: str) -> dict:
    if not company_url.startswith("http"):
        company_url = f"https://{company_url}"
    
    domain = urlparse(company_url).netloc.lower()
    
    # Scrape
    homepage_soup = _fetch_page(company_url)
    subpages = _scrape_subpages(company_url)
    full_text = _extract_text_from_pages(homepage_soup, subpages).lower()
    
    # Detect Industry
    industry = _detect_industry(full_text)
    
    # Extract common services / keywords using heuristics
    service_keywords = [
        "consulting", "software development", "cloud migration", "data science", 
        "machine learning", "digital marketing", "cybersecurity", "managed services",
        "devops", "automation", "ui/ux design", "waste management", "logistics"
    ]
    
    tech_keywords = [
        "python", "react", "aws", "azure", "gcp", "docker", "kubernetes", 
        "node.js", "java", "sql", "nosql", "artificial intelligence", "ai", "blockchain"
    ]
    
    target_industries = [
        "healthcare", "finance", "retail", "manufacturing", "education", "real estate", "logistics"
    ]
    
    services = [s for s in service_keywords if s in full_text]
    expertise = [t for t in tech_keywords if t in full_text]
    targets = [ti for ti in target_industries if ti in full_text]
    
    # Default fallbacks if empty
    if not services:
        services = ["General Business Services", "Digital Solutions", "Strategy Consulting"]
    if not expertise:
        expertise = ["Enterprise Software", "Cloud Platforms"]
    if not targets:
        targets = ["B2B Enterprises", "SMEs"]
        
    company_name = domain.split('.')[0].capitalize()
    if company_name in ["Www", "App"]:
        company_name = domain.replace('www.', '').split('.')[0].capitalize()
    
    return {
        "company_name": company_name,
        "company_url": company_url,
        "industry": industry,
        "services": services,
        "tech_expertise": expertise,
        "target_industries": targets,
    }
