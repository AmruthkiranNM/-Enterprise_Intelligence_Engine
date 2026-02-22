import sys
import os

# Add the project root to sys.path
sys.path.append(os.getcwd())

from company_discovery.intelligence import (
    _classify_website_scale,
    _detect_industry,
    _detect_hiring_intensity,
    _detect_growth_signals,
    _detect_scale_signals,
    _detect_trigger_events,
    detect_bottlenecks
)
from company_discovery.scoring import score_company_domain

# Mock data for browserstack.com
browserstack_text = """
BrowserStack is the world's leading software testing platform. 
We offer a comprehensive product ecosystem including App Live, Automate, Percy, and Test Observability.
Trusted by over 50,000 customers globally, including Microsoft, Google, Amazon, and Spotify.
With global offices in San Francisco, Mumbai, and Dublin.
Our enterprise platform provides APIs and SDKs for seamless integration with your DevOps pipeline.
We are hiring aggressively across engineering, product, and sales.
Our SOC2 compliant infrastructure handles millions of tests every day.
"""

# Mock subpages
class MockSoup:
    def __init__(self, text):
        self.text = text
    def get_text(self, separator=" ", strip=True):
        return self.text
    def find_all(self, *args, **kwargs):
        return [1, 2, 3, 4, 5, 6] # Simulating many job links

mock_subpages = {
    "/careers": MockSoup("We have many open positions for engineers, product managers, and account executives.")
}

from company_discovery.intelligence import (
    _detect_product_complexity,
    _detect_enterprise_exposure,
    _detect_geographical_presence,
    _detect_technical_depth
)

def run_test():
    print("--- Running BrowserStack Classification Test ---")
    
    classification = _classify_website_scale(browserstack_text, mock_subpages)
    industry = _detect_industry(browserstack_text)
    hiring = _detect_hiring_intensity(browserstack_text, mock_subpages)
    growth = _detect_growth_signals(browserstack_text)
    scale = _detect_scale_signals(browserstack_text)
    triggers = _detect_trigger_events(browserstack_text)
    
    print(f"Classification: {classification}")
    print(f"Industry: {industry}")
    print(f"Hiring: {hiring}")
    print(f"Growth Signals: {growth}")
    print(f"Scale Signals: {scale}")
    print(f"Trigger Events: {triggers}")
    
    # ── New Strategic Pressure Index (100-point scale) ──────────
    financial_score = min(len(growth) * 5 + len(triggers) * 10, 20)
    hiring_score = 15 if hiring == "High" else 7 if hiring == "Moderate" else 0
    product_score = _detect_product_complexity(browserstack_text) * 2
    enterprise_score = _detect_enterprise_exposure(browserstack_text)
    geo_score = _detect_geographical_presence(browserstack_text)
    tech_score = _detect_technical_depth(browserstack_text)
    
    total_pressure = financial_score + hiring_score + product_score + enterprise_score + geo_score + tech_score
    total_pressure = min(total_pressure, 100)
    
    # Enterprise SaaS Guard
    if industry == "SaaS" and classification["business_type"] == "Enterprise / Global":
        total_pressure = max(total_pressure, 15)

    print(f"\nComplexity Signals: Product({product_score}), Ent({enterprise_score}), Geo({geo_score}), Tech({tech_score})")
    print(f"Strategic Pressure Score: {total_pressure}/100")

    dossier = {
        "domain": "browserstack.com",
        "industry": industry,
        "business_type": classification["business_type"],
        "business_stage": classification["business_stage"],
        "hiring_intensity": hiring,
        "growth_signals": growth,
        "scale_signals": scale,
        "trigger_events": triggers,
        "strategic_pressure_score": total_pressure,
    }
    
    bottlenecks = detect_bottlenecks(dossier)
    threshold_config = {"tier": "medium", "min_signals_region": 3}
    
    final_score = score_company_domain(dossier, bottlenecks, threshold_config)
    
    print(f"Final Lead Score: {final_score['total']}/100")
    print(f"Classification: {final_score['classification']}")
    print(f"Scores Breakdown: {final_score['scores']}")

    # Validation
    assert industry == "SaaS", f"Expected SaaS, got {industry}"
    assert total_pressure >= 25, f"Pressure too low: {total_pressure}"
    assert final_score['total'] >= 65, f"Lead Score too low: {final_score['total']}"
    print("\nSUCCESS: BrowserStack correctly classified.")

if __name__ == "__main__":
    run_test()
