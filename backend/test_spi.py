"""Verification of Strategic Pressure Index (SPI) logic."""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from company_discovery.intelligence import compute_strategic_pressure, get_pressure_metadata

def test_spi():
    print("Running Strategic Pressure Index (SPI) Tests...\n")

    # Case 1: Razorpay Example (5/20)
    # Expected: 5/20 -> Emerging (Blue) -> Early Engagement
    # Signals: Hiring High (+2), Product Launch (+2), Enterprise (+1) = 5
    razor_signals = {"enterprise_clients": {"detected": True}}
    razor_growth = ["New product launched", "Launched platform"]
    razor_score = compute_strategic_pressure(
        growth_signals=razor_growth,
        scale_signals=[],
        hiring_intensity="High",
        signals=razor_signals,
        trigger_events=[]
    )
    razor_meta = get_pressure_metadata(razor_score)
    print(f"Razorpay (Score: {razor_score}/20):")
    print(f"  Tier: {razor_meta['tier']} (Expected: Emerging)")
    print(f"  Color: {razor_meta['color']} (Expected: #3B82F6)")
    print(f"  Guidance: {razor_meta['guidance']} (Expected: Early Engagement)\n")

    # Case 2: Post-IPO High Pressure (15/20)
    # Funding (+3), M&A (+3), Hiring (+2), Expansion (+2), Leadership (+2)
    # We'll use specific keywords that hit the new weights.
    high_signals = {"enterprise_clients": {"detected": True}}
    high_growth = [
        "Raised funding round", # +3
        "Acquired competitor", # +3
        "Launched platform", # +2
        "Expanding to US", # +2
        "New CEO joined" # +2
    ]
    # Hiring High: +2
    # Enterprise Detected: +1
    # Total: 3+3+2+2+2+2+1 = 15
    high_score = compute_strategic_pressure(
        growth_signals=high_growth,
        scale_signals=[],
        hiring_intensity="High",
        signals=high_signals,
        trigger_events=[]
    )
    high_meta = get_pressure_metadata(high_score)
    print(f"High-Pressure (Score: {high_score}/20):")
    print(f"  Tier: {high_meta['tier']} (Expected: High Pressure)")
    print(f"  Color: {high_meta['color']} (Expected: #F97316)")
    print(f"  Guidance: {high_meta['guidance']}\n")

    # Case 3: Critical Window (Cap at 20)
    crit_signals = {"enterprise_clients": {"detected": True}}
    crit_growth = [
        "Series D funding", # +3
        "Merger with X", # +3
        "Product launch", # +2
        "Global expansion", # +2
        "New CTO appointed", # +2
        "Acquisition of Y", # +3
        "IPO announcement", # +3 (if keyword matches)
        "Series E funding", # +3
    ]
    # Total: 3+3+2+2+2+3+3+3 = 21 -> cap at 20
    crit_score = compute_strategic_pressure(
        growth_signals=crit_growth,
        scale_signals=[],
        hiring_intensity="High",
        signals=crit_signals,
        trigger_events=[]
    )
    crit_meta = get_pressure_metadata(crit_score)
    print(f"Critical Window (Score: {crit_score}/20):")
    print(f"  Tier: {crit_meta['tier']} (Expected: Critical Window)")
    print(f"  Color: {crit_meta['color']} (Expected: #EF4444)")
    print(f"  Guidance: {crit_meta['guidance']}\n")

    print("All SPI logic tests complete.")

if __name__ == "__main__":
    test_spi()
