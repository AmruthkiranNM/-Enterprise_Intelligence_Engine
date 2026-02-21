"""Verification of Refined Strategic Pressure Index (SPI) Interpretation Metadata."""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from company_discovery.intelligence import compute_strategic_pressure, get_pressure_metadata

def test_spi_refinement():
    print("Running Refined Strategic Pressure Index (SPI) Tests...\n")

    # Case 1: Stable (0-3)
    # Expected: Stable Operational Velocity | Passive Monitoring
    stable_score = 3
    stable_meta = get_pressure_metadata(stable_score)
    print(f"Stable (Score: {stable_score}/20):")
    print(f"  Tier: {stable_meta['tier']}")
    print(f"  Engagement Mode: {stable_meta['engagement_mode']}")
    print(f"  Operational Meaning: {stable_meta['operational_meaning']}")
    print(f"  Explanation: {stable_meta['explanation']}\n")

    # Case 2: Emerging (4-7)
    # Expected: Emerging Operational Velocity | Warm Observation
    emerging_score = 5
    emerging_meta = get_pressure_metadata(emerging_score)
    print(f"Emerging (Score: {emerging_score}/20):")
    print(f"  Tier: {emerging_meta['tier']}")
    print(f"  Engagement Mode: {emerging_meta['engagement_mode']}")
    print(f"  Explanation: {emerging_meta['explanation']}\n")

    # Case 3: High Strain (13-16)
    # Expected: High Operational Strain | Immediate Outreach
    high_score = 15
    high_meta = get_pressure_metadata(high_score)
    print(f"High-Strain (Score: {high_score}/20):")
    print(f"  Tier: {high_meta['tier']}")
    print(f"  Engagement Mode: {high_meta['engagement_mode']}")
    print(f"  Explanation: {high_meta['explanation']}\n")

    # Case 4: Critical (17-20)
    # Expected: Critical Transformation Window | Executive Escalation
    crit_score = 20
    crit_meta = get_pressure_metadata(crit_score)
    print(f"Critical (Score: {crit_score}/20):")
    print(f"  Tier: {crit_meta['tier']}")
    print(f"  Engagement Mode: {crit_meta['engagement_mode']}")
    print(f"  Operational Meaning: {crit_meta['operational_meaning']}")
    print(f"  Explanation: {crit_meta['explanation']}\n")

    # Verify field presence in metadata
    required_fields = ["tier", "operational_meaning", "engagement_mode", "color", "explanation"]
    for field in required_fields:
        assert field in crit_meta, f"Missing field: {field}"

    print("All SPI refinement tests complete.")

if __name__ == "__main__":
    test_spi_refinement()
