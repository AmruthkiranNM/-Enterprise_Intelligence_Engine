import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class ImpactScorer:
    """Analytical scoring engine for Strategic Impact Index (0-100)."""
    
    def calculate(self, event_type: str, confidence: float, dossier_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Calculates impact across 4 dimensions:
        - Market Visibility (0-25)
        - Financial Pressure (0-25)
        - Operational Strain (0-25)
        - Service Alignment (0-25)
        """
        # Base scores per event type
        mapping = {
            "IPO":             {"mv": 25, "fp": 20, "os": 15, "sa": 20},
            "Funding Round":   {"mv": 20, "fp": 25, "os": 10, "sa": 15},
            "M&A":             {"mv": 22, "fp": 15, "os": 25, "sa": 25},
            "Leadership Change":{"mv": 15, "fp": 10, "os": 20, "sa": 20},
            "Major Partnership":{"mv": 18, "fp": 0,  "os": 5,  "sa": 15},
            "Product Launch":  {"mv": 20, "fp": 5,  "os": 12, "sa": 22},
            "Regulatory Issue": {"mv": 10, "fp": 25, "os": 15, "sa": 10},
            "Layoffs":         {"mv": 5,  "fp": 25, "os": 25, "sa": 15},
            "Expansion":       {"mv": 20, "fp": 15, "os": 20, "sa": 15},
        }
        
        base = mapping.get(event_type, {"mv": 10, "fp": 10, "os": 10, "sa": 10})
        
        # Scaling factor based on confidence
        factor = confidence / 100.0
        
        mv = base["mv"] * factor
        fp = base["fp"] * factor
        os_score = base["os"] * factor
        sa = base["sa"] * factor
        
        total = mv + fp + os_score + sa
        
        # Severity labeling
        if total >= 76:
            severity = "Critical Executive Event"
            action = "Executive Escalation"
        elif total >= 51:
            severity = "Strategic Trigger"
            action = "Strategic Outreach"
        elif total >= 26:
            severity = "Growth Indicator"
            action = "Warm Outreach"
        else:
            severity = "Informational"
            action = "Monitor"
            
        return {
            "strategic_impact_index": round(total, 1),
            "severity_label": severity,
            "action_level": action,
            "impact_breakdown": {
                "market_visibility": round(mv, 1),
                "financial_pressure": round(fp, 1),
                "operational_strain": round(os_score, 1),
                "service_alignment": round(sa, 1)
            },
            "impact_drivers": self._get_drivers(event_type, base),
            "strategic_relevance": self._get_relevance(event_type)
        }

    def _get_drivers(self, event_type: str, base: Dict[str, float]) -> List[str]:
        drivers = []
        if base["mv"] >= 20: drivers.append("High Market Visibility")
        if base["fp"] >= 20: drivers.append("Significant Financial Impact")
        if base["os"] >= 20: drivers.append("High Operational Strain")
        if base["sa"] >= 20: drivers.append("Strong DataVex Alignment")
        return drivers

    def _get_relevance(self, event_type: str) -> str:
        relevance = {
            "IPO": "Post-IPO readiness requires automated governance and scaling infrastructure.",
            "Funding Round": "Scaling operations rapidly creates immediate demand for digital transformation.",
            "M&A": "Integration complexity requires unified data pipelines and process automation.",
            "Leadership Change": "New leadership often triggers a 90-day vendor and tech stack reassessment window.",
            "Major Partnership": "Extended ecosystem requires robust API and security integration.",
            "Product Launch": "Rapid R&D cycles demand optimized DevOps and cloud modernization.",
            "Regulatory Issue": "Compliance pressure necessitates automated risk monitoring and signal validation.",
            "Layoffs": "Workforce reduction creates an urgent need for do-more-with-less AI automation.",
            "Expansion": "Entering new regions requires scalable outreach and localized market intelligence.",
        }
        return relevance.get(event_type, "Strategic event suggesting potential operational misalignment.")
