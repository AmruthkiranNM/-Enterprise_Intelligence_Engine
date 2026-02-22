import re
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

TRIGGER_MAP = {
    "IPO": [r"\bipo\b", r"\binitial public offering\b", r"\bnasdaq\b", r"\bnyse\b"],
    "Funding Round": [r"\braises\b", r"\bseries [a-z]\b", r"\bfunding round\b", r"\bseed round\b", r"\bventure capital\b"],
    "M&A": [r"\bacquires\b", r"\bacquisition\b", r"\bmerger\b", r"\bm&a\b", r"\btakeover\b"],
    "Leadership Change": [r"\bnew cto\b", r"\bnew ceo\b", r"\bnew cfo\b", r"\bappointed\b", r"\bjoins as\b", r"\bchief executive\b"],
    "Major Partnership": [r"\bpartnership\b", r"\bcollaboration\b", r"\bstrategic alliance\b", r"\bjoint venture\b"],
    "Product Launch": [r"\bproduct launch\b", r"\bnew feature\b", r"\bunveiled\b", r"\brollout\b"],
    "Regulatory Issue": [r"\bregulatory\b", r"\bfiling\b", r"\blawsuit\b", r"\bcompliance\b", r"\bfine\b"],
    "Layoffs": [r"\blayoffs\b", r"\brestructuring\b", r"\bdownsizing\b", r"\bworkforce reduction\b"],
    "Expansion": [r"\bexpansion\b", r"\bnew office\b", r"\bentered market\b", r"\bnew region\b"],
}

class EventDetector:
    """Detects strategic events from news text."""
    
    def detect(self, headline: str, content: str) -> Optional[Dict[str, Any]]:
        text = f"{headline} {content}".lower()
        
        for event_type, patterns in TRIGGER_MAP.items():
            matches = []
            for pattern in patterns:
                if re.search(pattern, text):
                    matches.append(pattern)
            
            if matches:
                # Confidence score based on number of keyword matches and text prominence
                confidence = min(40 + (len(matches) * 20), 100)
                if headline.lower().find(matches[0].replace(r"\b", "")) != -1:
                    confidence += 10
                
                return {
                    "event_type": event_type,
                    "confidence_score": min(confidence, 100),
                    "evidence": headline,
                    "event_date": None # To be filled by ingestion if available
                }
        
        return None
