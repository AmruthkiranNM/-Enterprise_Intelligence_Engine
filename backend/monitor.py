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


# ── Signal detection ──────────────────────────────────────────────────────────

def _search_company_news(domain: str, company_name: str) -> List[Dict[str, Any]]:
    """
    Search Google News / Bing for recent news about the company.
    Returns a list of {title, snippet, url} items.
    Falls back gracefully if the network call fails.
    """
    try:
        import sys, os
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
        from company_discovery.search import search_web as _search_web  # type: ignore

        query = f"{company_name} site:{domain} OR \"{company_name}\" funding OR acquisition OR IPO OR hiring 2025 2026"
        results = _search_web(query)
        return results if isinstance(results, list) else []
    except Exception as e:
        logger.warning("[monitor] news search failed for %s: %s", domain, e)
        # Fallback: return empty (no false positives)
        return []


def _detect_triggers(news_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Scan news titles and snippets for trigger keywords.
    Returns list of {event_type, event_summary, severity, impact_score, confidence, keyword}.
    """
    detected = []
    seen_types: set = set()

    for item in news_items:
        text = (
            f"{item.get('title', '')} {item.get('snippet', '')} {item.get('body', '')}"
        ).lower()

        for event_type, keywords in TRIGGER_KEYWORDS.items():
            if event_type in seen_types:
                continue
            for kw in keywords:
                if kw in text:
                    severity = SEVERITY_WEIGHTS[event_type]
                    confidence = "High" if kw in text and len(text) > 100 else "Medium"
                    detected.append({
                        "event_type": event_type,
                        "event_summary": (
                            f"{item.get('title', 'Signal detected').strip()} — "
                            f"Keyword: \"{kw}\" detected in recent news."
                        ),
                        "severity": severity,
                        "impact_score": IMPACT_SCORES[severity],
                        "confidence": confidence,
                        "source_url": item.get("url", item.get("link", "")),
                    })
                    seen_types.add(event_type)
                    break

    return detected


def _build_suggested_action(event_type: str, company_name: str) -> str:
    templates = {
        "Funding": (
            f"Reach out immediately — {company_name} has fresh capital to deploy on tooling and infrastructure. "
            "Lead with ROI framing and reference their expansion mandate."
        ),
        "Acquisition": (
            f"{company_name} is in integration mode — a prime window for workflow modernization tools. "
            "Pitch DataVex as the integration intelligence layer."
        ),
        "IPO": (
            f"Post-IPO, {company_name} faces intense investor scrutiny on operational efficiency. "
            "DataVex's Market Intelligence Agent directly addresses GTM efficiency at scale."
        ),
        "Leadership": (
            f"New leadership at {company_name} means a 90-day window where new executives make vendor decisions. "
            "Request introductory meeting before their agenda is set."
        ),
        "Hiring": (
            f"{company_name} is scaling fast — their ops and data workflows will strain under growth. "
            "Suggest DataVex as the automation layer for talent intelligence."
        ),
        "Layoffs": (
            f"{company_name} is restructuring. This is an internal pivot signal — they need efficiency. "
            "Pitch DataVex as a way to do more with less through AI automation."
        ),
        "Legal": (
            f"{company_name} faces new regulatory/legal pressure. Compliance efficiency is key. "
            "Focus on DataVex signal validation for risk monitoring."
        ),
        "Expansion": (
            f"{company_name} is entering new markets — outreach intelligence at scale is critical. "
            "DataVex's Market Intelligence Agent is the top-of-funnel engine they need."
        ),
        "Product": (
            f"A product launch signals R&D velocity at {company_name}. "
            "DataVex can accelerate their next release cycle with legacy modernization tooling."
        ),
    }
    return templates.get(event_type, f"Engage {company_name} on strategic priorities driven by this event.")


# ── Core scan logic ───────────────────────────────────────────────────────────

def scan_company(entry, db) -> int:
    """
    Scan a single WatchlistEntry for new trigger events.
    Creates Alert records. Returns count of new alerts created.
    """
    from database.models import Alert

    company_name = entry.company_name
    domain = entry.domain
    logger.info("[monitor] scanning — %s (%s)", company_name, domain)

    # Load last snapshot
    try:
        last_snapshot: List[str] = json.loads(entry.last_trigger_snapshot or "[]")
    except (ValueError, TypeError):
        last_snapshot = []

    # Fetch news
    news_items = _search_company_news(domain, company_name)
    new_triggers = _detect_triggers(news_items)

    created = 0
    new_snapshot = list(last_snapshot)

    for trigger in new_triggers:
        # De-duplicate against snapshot
        snapshot_key = f"{trigger['event_type']}:{trigger['event_summary'][:60]}"
        if snapshot_key in last_snapshot:
            continue

        alert = Alert(
            company_name=company_name,
            domain=domain,
            event_type=trigger["event_type"],
            event_summary=trigger["event_summary"],
            severity=trigger["severity"],
            impact_score=trigger["impact_score"],
            confidence=trigger["confidence"],
            suggested_action=_build_suggested_action(trigger["event_type"], company_name),
            is_read=False,
            email_sent=False,
        )
        db.add(alert)
        new_snapshot.append(snapshot_key)
        created += 1

        # Fire email for High severity
        if trigger["severity"] == "High":
            try:
                from alerter import send_alert_email
                db.flush()  # get alert.id
                send_alert_email(alert)
                alert.email_sent = True
            except Exception as e:
                logger.warning("[monitor] email for %s failed: %s", company_name, e)

    # Update entry metadata
    entry.last_scan_at = datetime.datetime.utcnow()
    entry.last_trigger_snapshot = json.dumps(new_snapshot[-100:])  # keep last 100
    db.commit()

    if created:
        logger.info("[monitor] %d new alert(s) for %s", created, company_name)
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
