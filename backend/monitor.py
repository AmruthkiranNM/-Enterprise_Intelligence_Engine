"""
monitor.py — Precision Lead Monitoring Agent
=============================================
Autonomous background agent that scans watched companies for genuine,
corroborated strategic trigger events. Designed for ZERO false positives.

Key precision mechanisms:
  1. Website content diffing (SHA-256 hash comparison between scans)
  2. Multi-source news fetch (2 targeted queries)
  3. 2+ keyword corroboration per category (single match = ignored)
  4. Mock-data guard (no alerts when Tavily unavailable)
  5. Confidence threshold gating (must reach "Medium" to fire)
  6. Source URL required (no URL = no alert)

Schedule: weekly by default (MONITOR_INTERVAL_HOURS env, default 168).
"""

import hashlib
import json
import logging
import os
import datetime
from typing import List, Dict, Any, Tuple, Optional

from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)

# ── Trigger Keyword Taxonomy ──────────────────────────────────────────────────
# Each category requires 2+ keyword hits to fire (corroboration rule).
TRIGGER_KEYWORDS: Dict[str, List[str]] = {
    "Funding": [
        "raised", "series a", "series b", "series c", "series d",
        "funding round", "seed round", "investment round", "venture capital",
        "vc backed", "unicorn", "valuation", "capital raise", "fundraise",
    ],
    "Acquisition": [
        "acquired", "acquisition", "merger", "m&a", "takeover",
        "bought by", "acqui-hire", "merged with", "strategic acquisition",
    ],
    "IPO": [
        "ipo", "initial public offering", "went public", "nasdaq", "nyse",
        "s-1 filing", "direct listing", "public listing",
    ],
    "Leadership": [
        "new ceo", "new cto", "new cfo", "new vp", "new svp",
        "appointed", "joins as", "chief technology officer",
        "chief executive officer", "chief financial officer",
        "leadership change", "new head of", "co-founder leaves",
    ],
    "Hiring": [
        "hiring aggressively", "mass hiring", "headcount increase",
        "100+ engineers", "200+ engineers", "scaling team", "rapid hiring",
        "expanding team", "talent acquisition drive",
    ],
    "Product": [
        "product launch", "new product", "new feature", "beta launch",
        "product rollout", "unveiled", "launched platform",
        "new service", "product release",
    ],
    "Expansion": [
        "expansion", "new office", "global expansion", "entered market",
        "new region", "new geography", "international expansion",
        "new branch", "opened operations",
    ],
    "Layoffs": [
        "layoffs", "restructuring", "downsizing", "workforce reduction",
        "internal pivot", "cost cutting", "rif ", "reduction in force",
    ],
    "Legal": [
        "regulatory action", "sec filing", "lawsuit filed",
        "compliance issue", "antitrust", "data breach",
        "regulatory investigation", "penalty",
    ],
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

# Minimum thresholds to create an alert
MIN_KEYWORDS_PER_CATEGORY = 2    # Must match 2+ keywords from same category
MIN_CONFIDENCE_TO_ALERT = 2      # Confidence score must be >= 2 (out of ~5)
MIN_SEVERITY_TO_ALERT = "Medium" # Low-severity events are suppressed

SEVERITY_RANK = {"High": 3, "Medium": 2, "Low": 1}


# ── Website Content Diffing ──────────────────────────────────────────────────

def _scrape_website_content(domain: str) -> Tuple[str, str]:
    """
    Scrape company website (homepage + key sub-pages) and return
    (full_text, sha256_hash). Returns ("", "") if unreachable.
    """
    try:
        import sys
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
        from company_discovery.scraper import _fetch_page  # type: ignore
    except ImportError:
        logger.warning("[monitor] scraper import failed — skipping website diff")
        return "", ""

    base_url = f"https://{domain}"
    sub_paths = ["/", "/about", "/blog", "/news", "/careers", "/company"]
    all_text_parts: List[str] = []

    for path in sub_paths:
        url = base_url.rstrip("/") + path
        try:
            soup = _fetch_page(url)
            if soup:
                text = soup.get_text(separator=" ", strip=True)
                # Only keep meaningful chunks (>50 chars)
                if len(text) > 50:
                    all_text_parts.append(text[:5000])  # cap per page
        except Exception:
            continue

    full_text = "\n".join(all_text_parts)
    if not full_text:
        return "", ""

    content_hash = hashlib.sha256(full_text.encode("utf-8")).hexdigest()
    return full_text, content_hash


def _detect_website_changes(
    domain: str, last_hash: str
) -> Tuple[bool, str, List[str]]:
    """
    Scrape the website and compare against the last known content hash.
    Returns (has_changed, new_hash, major_change_keywords_found).
    """
    full_text, new_hash = _scrape_website_content(domain)

    if not new_hash:
        return False, last_hash or "", []

    if new_hash == last_hash:
        return False, new_hash, []

    # Content changed — look for MAJOR change keywords in the new text
    text_lower = full_text.lower()
    MAJOR_CHANGE_KEYWORDS = [
        "raised", "funding", "series", "acquired", "acquisition", "merger",
        "ipo", "public offering", "new ceo", "new cto", "appointed",
        "layoffs", "restructuring", "product launch", "expansion",
        "new office", "regulatory", "lawsuit",
    ]
    found = [kw for kw in MAJOR_CHANGE_KEYWORDS if kw in text_lower]

    return True, new_hash, found


# ── Multi-Source News Search ─────────────────────────────────────────────────

def _is_tavily_available() -> bool:
    """Check if live Tavily search is available (not mock mode)."""
    try:
        import sys
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
        from company_discovery.search import USE_TAVILY  # type: ignore
        return USE_TAVILY
    except (ImportError, AttributeError):
        return False


def _search_company_news(domain: str, company_name: str) -> List[Dict[str, Any]]:
    """
    Search for recent company news using 2 targeted queries.
    Returns ONLY live Tavily results — never mock data.
    Each result must have a valid source URL.
    """
    if not _is_tavily_available():
        logger.info("[monitor] Tavily unavailable — skipping news search (no mock alerts)")
        return []

    try:
        import sys
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
        from company_discovery.search import _real_web_search  # type: ignore
    except ImportError:
        logger.warning("[monitor] search import failed")
        return []

    all_results: List[Dict[str, Any]] = []

    # Query 1: Funding, M&A, IPO, legal
    queries = [
        f'"{company_name}" funding OR acquisition OR IPO OR merger OR regulatory 2025 2026',
        f'"{company_name}" product launch OR expansion OR hiring OR layoffs OR leadership 2025 2026',
    ]

    for query in queries:
        try:
            results = _real_web_search(query, max_results=5)
            if isinstance(results, list):
                all_results.extend(results)
        except Exception as e:
            logger.warning("[monitor] news query failed: %s", e)

    # Filter: must have a valid source URL
    validated = []
    seen_urls: set = set()
    for item in all_results:
        url = item.get("url") or item.get("link", "")
        if not url or url in seen_urls:
            continue
        # Must be an actual URL, not a placeholder
        if not url.startswith("http"):
            continue
        seen_urls.add(url)
        validated.append(item)

    logger.info("[monitor] %d validated news items for %s", len(validated), company_name)
    return validated


# ── Precision Trigger Detection ──────────────────────────────────────────────

def _detect_triggers(news_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Scan news for trigger events with STRICT corroboration:
      - 2+ keyword matches required per category
      - Source URL must be present
      - Confidence computed from keyword density + source quality

    Returns list of {event_type, event_summary, severity, impact_score,
                     confidence, confidence_score, source_url}.
    """
    # Aggregate all text from all news items per-category
    category_hits: Dict[str, List[Dict[str, Any]]] = {}

    for item in news_items:
        text = (
            f"{item.get('title', '')} {item.get('snippet', '')} "
            f"{item.get('body', '')} {item.get('content', '')}"
        ).lower()
        source_url = item.get("url") or item.get("link", "")

        if not source_url or not source_url.startswith("http"):
            continue  # No URL = not trustworthy

        for event_type, keywords in TRIGGER_KEYWORDS.items():
            matched_kws = [kw for kw in keywords if kw in text]
            if matched_kws:
                category_hits.setdefault(event_type, []).append({
                    "matched_keywords": matched_kws,
                    "source_url": source_url,
                    "title": item.get("title", "").strip(),
                    "snippet": item.get("snippet", "").strip(),
                    "text_length": len(text),
                })

    # Apply corroboration: only categories with 2+ keyword hits
    detected: List[Dict[str, Any]] = []
    for event_type, hits in category_hits.items():
        # Count total unique keywords matched across all sources
        all_matched_kws = set()
        source_urls = set()
        best_title = ""
        best_snippet = ""

        for h in hits:
            all_matched_kws.update(h["matched_keywords"])
            source_urls.add(h["source_url"])
            if len(h["title"]) > len(best_title):
                best_title = h["title"]
                best_snippet = h["snippet"]

        total_keyword_hits = len(all_matched_kws)

        # CORROBORATION GATE: need 2+ distinct keyword matches
        if total_keyword_hits < MIN_KEYWORDS_PER_CATEGORY:
            logger.debug(
                "[monitor] %s: only %d keyword(s) — below threshold, skipping",
                event_type, total_keyword_hits,
            )
            continue

        # SEVERITY GATE: suppress Low-severity events
        severity = SEVERITY_WEIGHTS.get(event_type, "Low")
        if SEVERITY_RANK.get(severity, 0) < SEVERITY_RANK.get(MIN_SEVERITY_TO_ALERT, 2):
            logger.debug("[monitor] %s: severity %s below threshold — skipping", event_type, severity)
            continue

        # Compute confidence score (0-5 scale)
        conf_score = 0
        conf_score += min(total_keyword_hits, 3)   # up to 3 for keyword density
        conf_score += min(len(source_urls), 2)      # up to 2 for multi-source

        # CONFIDENCE GATE
        if conf_score < MIN_CONFIDENCE_TO_ALERT:
            logger.debug("[monitor] %s: confidence %d below threshold — skipping", event_type, conf_score)
            continue

        confidence_label = "High" if conf_score >= 4 else "Medium" if conf_score >= 2 else "Low"

        # Build evidence-backed summary (no vague "keyword detected" messages)
        summary_parts = []
        if best_title:
            summary_parts.append(best_title)
        summary_parts.append(
            f"Corroborated by {total_keyword_hits} keyword matches "
            f"across {len(source_urls)} source(s)."
        )
        if best_snippet:
            # Trim snippet to first 120 chars for conciseness
            summary_parts.append(f"Context: {best_snippet[:120].rstrip('.')}.")

        detected.append({
            "event_type": event_type,
            "event_summary": " — ".join(summary_parts),
            "severity": severity,
            "impact_score": IMPACT_SCORES[severity],
            "confidence": confidence_label,
            "confidence_score": conf_score,
            "source_url": list(source_urls)[0],  # primary source
        })

    return detected


def _build_suggested_action(event_type: str, company_name: str) -> str:
    """Build actionable strategic recommendation for each event type."""
    templates = {
        "Funding": (
            f"Reach out immediately — {company_name} has fresh capital to deploy on "
            "tooling and infrastructure. Lead with ROI framing."
        ),
        "Acquisition": (
            f"{company_name} is in integration mode — a prime window for "
            "workflow modernization tools."
        ),
        "IPO": (
            f"Post-IPO, {company_name} faces investor scrutiny on operational "
            "efficiency. DataVex directly addresses this."
        ),
        "Leadership": (
            f"New leadership at {company_name} creates a 90-day window for "
            "vendor decisions. Request introductory meeting."
        ),
        "Hiring": (
            f"{company_name} is scaling fast — ops and data workflows will "
            "strain under growth. Position as automation layer."
        ),
        "Layoffs": (
            f"{company_name} is restructuring — they need to do more with "
            "less. Pitch AI automation for efficiency gains."
        ),
        "Legal": (
            f"{company_name} faces regulatory/legal pressure. Focus on "
            "compliance efficiency and risk monitoring."
        ),
        "Expansion": (
            f"{company_name} entering new markets — outreach intelligence "
            "at scale is critical."
        ),
        "Product": (
            f"Product launch at {company_name} signals R&D velocity. "
            "Accelerate next cycle with modernization tooling."
        ),
    }
    return templates.get(
        event_type,
        f"Engage {company_name} on strategic priorities driven by this event.",
    )


# ── Core Scan Logic ──────────────────────────────────────────────────────────

def scan_company(entry, db) -> int:
    """
    Precision scan for a single WatchlistEntry.

    Pipeline:
      1. Website content diff (detect genuine page changes)
      2. Multi-source news search (only via live Tavily)
      3. Corroborated trigger detection (2+ keywords per category)
      4. Threshold gating (severity ≥ Medium, confidence ≥ Medium)
      5. De-duplication against historical snapshot
      6. Alert creation + email for High severity

    Returns count of new alerts created.
    """
    from database.models import Alert

    company_name = entry.company_name
    domain = entry.domain
    logger.info("[monitor] precision scan — %s (%s)", company_name, domain)

    # Load last snapshot for de-duplication
    try:
        last_snapshot: List[str] = json.loads(entry.last_trigger_snapshot or "[]")
    except (ValueError, TypeError):
        last_snapshot = []

    # ── Step 1: Website content diff ──────────────────────────────────────
    last_hash = getattr(entry, "content_hash", "") or ""
    website_changed, new_hash, change_keywords = _detect_website_changes(domain, last_hash)

    if website_changed:
        logger.info(
            "[monitor] website change detected for %s — %d major keywords found",
            domain, len(change_keywords),
        )
    else:
        logger.info("[monitor] no website content change for %s", domain)

    # ── Step 2: Multi-source news search ──────────────────────────────────
    news_items = _search_company_news(domain, company_name)

    # ── Step 3: Corroborated trigger detection ────────────────────────────
    new_triggers = _detect_triggers(news_items)
    logger.info("[monitor] %d corroborated trigger(s) for %s", len(new_triggers), domain)

    # ── Step 4: Cross-validation ──────────────────────────────────────────
    # For Medium severity: require BOTH news trigger AND website change
    # For High severity: news trigger alone is sufficient (major event)
    validated_triggers = []
    for trigger in new_triggers:
        severity = trigger["severity"]
        if severity == "High":
            # High severity = trust the corroborated news alone
            validated_triggers.append(trigger)
        elif severity == "Medium" and (website_changed or len(change_keywords) >= 2):
            # Medium severity = need additional corroboration from website
            validated_triggers.append(trigger)
        else:
            logger.debug(
                "[monitor] %s trigger '%s' dropped — Medium severity without website corroboration",
                domain, trigger["event_type"],
            )

    # ── Step 5: De-duplicate and create alerts ────────────────────────────
    created = 0
    new_snapshot = list(last_snapshot)

    for trigger in validated_triggers:
        # Content-based de-duplication key
        snapshot_key = (
            f"{trigger['event_type']}:"
            f"{trigger['event_summary'][:80]}:"
            f"{trigger['source_url'][:60]}"
        )
        if snapshot_key in last_snapshot:
            logger.debug("[monitor] duplicate skipped: %s", snapshot_key[:60])
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

        # Email notification for High severity only
        if trigger["severity"] == "High":
            try:
                from alerter import send_alert_email
                db.flush()
                send_alert_email(alert)
                alert.email_sent = True
            except Exception as e:
                logger.warning("[monitor] email for %s failed: %s", company_name, e)

    # ── Step 6: Update entry metadata ─────────────────────────────────────
    entry.last_scan_at = datetime.datetime.utcnow()
    entry.last_trigger_snapshot = json.dumps(new_snapshot[-200:])  # keep last 200

    # Persist the new content hash for future diffing
    if new_hash and hasattr(entry, "content_hash"):
        entry.content_hash = new_hash

    db.commit()

    if created:
        logger.info("[monitor] %d NEW alert(s) for %s", created, company_name)
    else:
        logger.info("[monitor] scan clean — 0 alerts for %s", domain)

    return created


# ── Scheduler ────────────────────────────────────────────────────────────────

class LeadMonitoringAgent:
    """
    Autonomous background agent.
    Schedules scan_all_watchlist() at a configurable interval.
    Default: weekly (168 hours).
    """

    def __init__(self):
        self.scheduler = BackgroundScheduler(timezone="UTC")
        interval_hours = int(os.environ.get("MONITOR_INTERVAL_HOURS", "168"))
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
            interval = os.environ.get("MONITOR_INTERVAL_HOURS", "168")
            logger.info("[monitor] LeadMonitoringAgent started — interval: %sh", interval)

    def stop(self):
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)

    def _run_scan(self):
        """Called by APScheduler on each tick."""
        from database.db import SessionLocal
        from database.models import WatchlistEntry

        db = SessionLocal()
        try:
            entries = (
                db.query(WatchlistEntry)
                .filter(WatchlistEntry.is_active == True)  # noqa: E712
                .all()
            )
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
            entry = (
                db.query(WatchlistEntry)
                .filter(WatchlistEntry.domain == domain)
                .first()
            )
            if entry:
                scan_company(entry, db)
        finally:
            db.close()


# Singleton used by main.py
monitoring_agent = LeadMonitoringAgent()
