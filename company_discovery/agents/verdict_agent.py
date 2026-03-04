"""
verdict_agent.py — Final Verdict Agent
Classifies prospect as Strong/Medium/Weak Lead based on gap relevance, context, service match.
"""

def generate_verdict(gaps: list, context_signals: list) -> dict:
    gap_count = len(gaps)
    context_count = sum(1 for c in context_signals if "funding" in c.lower() or "expansion" in c.lower() or "trigger" in c.lower())
    
    score = (gap_count * 2) + (context_count * 3)
    
    if score >= 5:
        verdict = "Strong Lead"
        justification = "Compelling operational gaps combined with acute strategic context (e.g. expansion/funding)."
    elif score >= 2:
        verdict = "Medium Lead"
        justification = "Identified operational gaps present an opportunity, but lacks acute strategic urgency."
    else:
        verdict = "Weak Lead"
        justification = "Stable operations with no clear gaps or growth triggers detected."
        
    return {
        "lead_verdict": verdict,
        "score": score,
        "justification": justification
    }
