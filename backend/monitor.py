"""
monitor.py — LeadMonitoringAgent
=================================
Autonomous background agent that periodically scans watched companies
for new strategic trigger events, creates alerts, and fires email notifications.

Schedule: every 6 hours (configurable via MONITOR_INTERVAL_HOURS env var).
"""

import json
import logging
import os
import datetime
from typing import List, Dict, Any

from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)

# ── Trigger Keyword Taxonomy ──────────────────────────────────────────────────
TRIGGER_KEYWORDS: Dict[str, List[str]] = {
    "Funding": [
        "raised", "series a", "series b", "series c", "series d",
        "funding round", "seed round", "investment", "venture capital",
        "vc backed", "unicorn", "valuation",
    ],
    "Acquisition": [
        "acquired", "acquisition", "merger", "m&a", "takeover",
        "bought by", "acqui-hire",
    ],
    "IPO": [
        "ipo", "initial public offering", "went public", "nasdaq", "nyse",
        "s-1 filing", "direct listing",
    ],
    "Leadership": [
        "new cto", "new ceo", "new cfo", "new vp", "new svp",
        "appointed", "joins as", "chief technology", "chief executive",
        "chief financial", "co-founder leaves",
    ],
    "Leadership": ["new ceo", "new cfo", "chief executive", "appointed", "leadership change", "new head of"],
    "Hiring": [
        "hiring aggressively", "mass hiring", "headcount",
        "100 engineers", "200 engineers", "scaling team", "rapid growth",
        "expanding team",
    ],
    "Product": ["product launch", "new feature", "beta", "rollout", "unveiled", "new product"],
    "Expansion": [
        "expansion", "new office", "global expansion", "entered market",
        "new region", "new geography", "international", "new branch",
    ],
    "Layoffs": ["layoffs", "restructuring", "downsizing", "workforce reduction", "internal pivot"],
    "Legal": ["regulatory", "filing", "lawsuit", "compliance", "antitrust", "data privacy"],
}

SEVERITY_WEIGHTS = {
    "Funding": "High",
    "Acquisition": "High",
    "IPO": "High",
    "Leadership": "Medium",
    "Hiring": "Medium",
    "Product": "Medium",
    "Expansion": "Low",
    "Layoffs": "High",
    "Legal": "Medium",
}

IMPACT_SCORES = {
    "High": 90.0,
    "Medium": 65.0,
    "Low": 40.0,
}


# ── Live Pipeline Components ──────────────────────────────────────────────────
from ingestion import NewsIngestor
from detection import EventDetector
from scoring import ImpactScorer

ingestor = NewsIngestor()
detector = EventDetector()
scorer = ImpactScorer()

# ── Core scan logic ───────────────────────────────────────────────────────────

def scan_company(entry, db) -> int:
    """
    Scan a WatchlistEntry using the real Strategic Alert Pipeline.
    1. Ingest real news (Tavily + RSS)
    2. Detect strategic triggers
    3. Score impact analytically
    4. Persist structured alerts
    """
    from database.models import Alert
    import json

    company_name = entry.company_name
    domain = entry.domain
    logger.info("[monitor] live scan initiated — %s (%s)", company_name, domain)

    # Load last snapshot to avoid duplicates
    try:
        last_snapshot: List[str] = json.loads(entry.last_trigger_snapshot or "[]")
    except (ValueError, TypeError):
        last_snapshot = []

    # Step 1: Ingest News
    articles = ingestor.fetch_company_news(company_name, domain)
    
    # We also check RSS for any mention (less precise but good for high-visibility)
    rss_articles = ingestor.fetch_rss_news()
    for art in rss_articles:
        if company_name.lower() in art["headline"].lower():
            art["company"] = company_name
            articles.append(art)

    created = 0
    new_snapshot_keys = list(last_snapshot)

    for art in articles:
        # Step 2: Detect Triggers
        event = detector.detect(art["headline"], art["raw_content"])
        if not event:
            continue
            
        # Filter by confidence
        if event["confidence_score"] < 60:
            continue

        # De-duplicate
        snapshot_key = f"{event['event_type']}:{art['headline'][:60]}"
        if snapshot_key in last_snapshot:
            continue

        # Step 3: Score Impact
        impact = scorer.calculate(event["event_type"], event["confidence_score"])

        # Step 4: Persist Alert
        alert = Alert(
            company_name=company_name,
            domain=domain,
            event_type=event["event_type"],
            headline=art["headline"],
            source=art["source"],
            url=art["url"],
            event_date=art["published_at"],
            impact_index=impact["strategic_impact_index"],
            market_visibility=impact["impact_breakdown"]["market_visibility"],
            financial_pressure=impact["impact_breakdown"]["financial_pressure"],
            operational_strain=impact["impact_breakdown"]["operational_strain"],
            service_alignment=impact["impact_breakdown"]["service_alignment"],
            severity_label=impact["severity_label"],
            action_level=impact["action_level"],
            impact_drivers=json.dumps(impact["impact_drivers"]),
            strategic_relevance=impact["strategic_relevance"],
            confidence_score=event["confidence_score"]
        )
        
        db.add(alert)
        new_snapshot_keys.append(snapshot_key)
        created += 1

        # Email for Critical events
        if impact["severity_label"] == "Critical Executive Event":
            try:
                from alerter import send_alert_email
                db.flush()
                # Basic backward compat for email builder
                alert.severity = "High" 
                alert.event_summary = art["headline"]
                alert.impact_score = impact["strategic_impact_index"]
                alert.confidence = str(event["confidence_score"])
                alert.suggested_action = impact["strategic_relevance"]
                send_alert_email(alert)
                alert.email_sent = True
            except Exception as e:
                logger.warning("[monitor] email failed: %s", e)

    # Update entry
    entry.last_scan_at = datetime.datetime.utcnow()
    entry.last_trigger_snapshot = json.dumps(new_snapshot_keys[-100:])
    db.commit()

    if created:
        logger.info("[monitor] generated %d real strategic alerts for %s", created, company_name)
    return created


# ── Scheduler ────────────────────────────────────────────────────────────────

class LeadMonitoringAgent:
    """
    Autonomous background agent.
    Schedules scan_all_watchlist() every N hours.
    """

    def __init__(self):
        self.scheduler = BackgroundScheduler(timezone="UTC")
        interval_hours = int(os.environ.get("MONITOR_INTERVAL_HOURS", "6"))
        self.scheduler.add_job(
            self._run_scan,
            trigger="interval",
            hours=interval_hours,
            id="lead_monitor",
            name="Lead Monitor Full Scan",
            replace_existing=True,
            next_run_time=datetime.datetime.utcnow(),  # run immediately on start
        )

    def start(self):
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("[monitor] LeadMonitoringAgent started — interval: %sh",
                        os.environ.get("MONITOR_INTERVAL_HOURS", "6"))

    def stop(self):
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)

    def _run_scan(self):
        """Called by APScheduler on each tick."""
        from database.db import SessionLocal
        from database.models import WatchlistEntry

        db = SessionLocal()
        try:
            entries = db.query(WatchlistEntry).filter(WatchlistEntry.is_active == True).all()  # noqa: E712
            logger.info("[monitor] scanning %d watched companies…", len(entries))
            total = 0
            for entry in entries:
                try:
                    total += scan_company(entry, db)
                except Exception as e:
                    logger.error("[monitor] scan error for %s: %s", entry.domain, e)
            logger.info("[monitor] scan complete — %d new alerts", total)
        finally:
            db.close()

    def scan_one_now(self, domain: str):
        """Trigger an immediate single-company scan (for 'Scan Now' button)."""
        from database.db import SessionLocal
        from database.models import WatchlistEntry

        db = SessionLocal()
        try:
            entry = db.query(WatchlistEntry).filter(WatchlistEntry.domain == domain).first()
            if entry:
                scan_company(entry, db)
        finally:
            db.close()


# Singleton used by main.py
monitoring_agent = LeadMonitoringAgent()
