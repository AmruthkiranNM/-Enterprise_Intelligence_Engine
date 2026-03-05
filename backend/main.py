"""
backend/main.py — DataVex Strategic Enterprise Intelligence Engine API
=======================================================================
REST endpoints for:
  - Analysis (domain & region)
  - Watchlist CRUD
  - Alert management
  - Monitoring agent lifecycle
"""

import sys
import os
import datetime
import json
import logging
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session

# ── path setup ────────────────────────────────────────────────────────────────
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BACKEND_DIR)

if BACKEND_DIR not in sys.path:
    sys.path.append(BACKEND_DIR)
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

# ── load .env if present ──────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
except ImportError:
    pass

# ── database ──────────────────────────────────────────────────────────────────
from database.db import init_db, get_db
from database.models import WatchlistEntry, Alert, ServiceCatalog, User
from auth import hash_password, verify_password, create_access_token, get_current_user

# ── intelligence engine ───────────────────────────────────────────────────────
try:
    from company_discovery.main import run_domain_pipeline, run_region_pipeline
    from company_discovery.agents.service_catalog_agent import build_service_catalog
    from company_discovery.agents.auditor_agent import run_auditor
    from company_discovery.agents.context_agent import run_context_hunter
    from company_discovery.agents.gap_analysis_agent import identify_gaps
    from company_discovery.agents.verdict_agent import generate_verdict
    from company_discovery.agents.report_agent import generate_report
except ImportError as e:
    logging.warning("company_discovery import failed: %s", e)
    def run_domain_pipeline(domain, threshold=None): return {"error": "Module not found", "domain": domain}
    def run_region_pipeline(region, threshold): return []

# ── monitoring agent ──────────────────────────────────────────────────────────
from monitor import monitoring_agent

# ── report generation ─────────────────────────────────────────────────────────
try:
    from reports import generate_strategic_risk_report, generate_executive_targeting_report
except ImportError:
    logging.warning("reports.py import failed")
    def generate_strategic_risk_report(*args): pass
    def generate_executive_targeting_report(*args): pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)-24s | %(levelname)-5s | %(message)s")

# ═══════════════════════════════════════════════════════════════════════════════
# App
# ═══════════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="Lead Intelligence Platform API",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static files for reports ──────────────────────────────────────────────────
REPORTS_DIR = os.path.join(BACKEND_DIR, "static", "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)
app.mount("/reports", StaticFiles(directory=REPORTS_DIR), name="reports")


@app.on_event("startup")
def startup():
    init_db()
    # Refresh intelligence services from catalog.json
    try:
        from company_discovery.intelligence import _load_catalog_services
        import company_discovery.intelligence as intel
        intel.DATAVEX_SERVICES = _load_catalog_services()
        logging.info("Service catalog synchronized successfully")
    except Exception as e:
        logging.warning("Failed to sync service catalog: %s", e)
    monitoring_agent.start()


@app.on_event("shutdown")
def shutdown():
    monitoring_agent.stop()


# ═══════════════════════════════════════════════════════════════════════════════
# Pydantic schemas
# ═══════════════════════════════════════════════════════════════════════════════

class DomainAnalysisRequest(BaseModel):
    domain: str
    threshold: Optional[str] = None

class RegionAnalysisRequest(BaseModel):
    region: str
    threshold: str

class OnboardRequest(BaseModel):
    company_url: str

class ProspectAnalysisRequest(BaseModel):
    prospect_url: str
    service_catalog: dict

# ── Auth Schemas ─────────────────────────────────────────────────────
class SignupRequest(BaseModel):
    name: str
    email: str
    password: str

class SigninRequest(BaseModel):
    email: str
    password: str

class WatchlistAddRequest(BaseModel):
    company_name: str
    domain: str
    industry: Optional[str] = "Unknown"
    classification: Optional[str] = "Not Priority"
    lead_score: Optional[float] = 0.0
    strategic_pressure: Optional[float] = 0.0

class WatchlistOut(BaseModel):
    id: int
    company_name: str
    domain: str
    industry: str
    classification: str
    lead_score: float
    strategic_pressure: float
    added_at: datetime.datetime
    last_scan_at: Optional[datetime.datetime]
    is_active: bool

    class Config:
        from_attributes = True

class AlertOut(BaseModel):
    id: int
    company_name: str
    domain: str
    event_type: str
    headline: str
    source: Optional[str]
    url: Optional[str]
    event_date: datetime.datetime
    
    impact_index: float
    market_visibility: float
    financial_pressure: float
    operational_strain: float
    service_alignment: float
    
    severity_label: str
    action_level: str
    impact_drivers: str # JSON string from DB
    strategic_relevance: Optional[str]
    confidence_score: float

    detected_at: datetime.datetime
    is_read: bool
    email_sent: bool

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════════════════════
# Health
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/")
async def root():
    return {"status": "ok", "version": "2.0.0", "service": "Lead Intelligence Platform"}


# ═══════════════════════════════════════════════════════════════════════════════
# Auth Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/auth/signup")
def signup(request: SignupRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        name=request.name,
        email=request.email,
        password_hash=hash_password(request.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token({"sub": str(user.id)})
    return {
        "token": token,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "is_onboarded": user.is_onboarded,
        }
    }

@app.post("/auth/signin")
def signin(request: SigninRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token({"sub": str(user.id)})
    return {
        "token": token,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "is_onboarded": user.is_onboarded,
        }
    }

@app.get("/auth/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "is_onboarded": current_user.is_onboarded,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Analysis Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/analyze-domain")
async def analyze_domain(request: DomainAnalysisRequest):
    try:
        results = run_domain_pipeline(request.domain, request.threshold)
        if isinstance(results, dict) and results.get("error"):
            raise HTTPException(status_code=400, detail=results["error"])
        return results
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze-region")
async def analyze_region(request: RegionAnalysisRequest):
    try:
        results = run_region_pipeline(request.region, request.threshold)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/onboard")
async def onboard_company(
    request: OnboardRequest,
    db: Session = Depends(get_db),
    credentials=Depends(__import__("auth").bearer_scheme),
):
    try:
        catalog_data = build_service_catalog(request.company_url)

        existing = db.query(ServiceCatalog).filter(ServiceCatalog.company_url == catalog_data["company_url"]).first()
        if existing:
            existing.company_name = catalog_data["company_name"]
            existing.industry = catalog_data["industry"]
            existing.services = json.dumps(catalog_data["services"])
            existing.tech_expertise = json.dumps(catalog_data["tech_expertise"])
            existing.target_industries = json.dumps(catalog_data["target_industries"])
            db.commit()
        else:
            new_cat = ServiceCatalog(
                company_name=catalog_data["company_name"],
                company_url=catalog_data["company_url"],
                industry=catalog_data["industry"],
                services=json.dumps(catalog_data["services"]),
                tech_expertise=json.dumps(catalog_data["tech_expertise"]),
                target_industries=json.dumps(catalog_data["target_industries"])
            )
            db.add(new_cat)
            db.commit()

        # Mark user as onboarded if they are logged in
        if credentials:
            from auth import decode_token
            payload = decode_token(credentials.credentials)
            if payload:
                uid = payload.get("sub")
                if uid:
                    user = db.query(User).filter(User.id == int(uid)).first()
                    if user and not user.is_onboarded:
                        user.is_onboarded = True
                        db.commit()

        return catalog_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/service-catalog")
def get_service_catalog(db: Session = Depends(get_db)):
    cat = db.query(ServiceCatalog).order_by(ServiceCatalog.created_at.desc()).first()
    if cat:
        return {
            "company_name": cat.company_name,
            "company_url": cat.company_url,
            "industry": cat.industry,
            "services": json.loads(cat.services),
            "tech_expertise": json.loads(cat.tech_expertise),
            "target_industries": json.loads(cat.target_industries)
        }
    return None

@app.post("/prospect-analysis")
async def analyze_prospect(request: ProspectAnalysisRequest):
    try:
        prospect_domain = request.prospect_url.replace("https://", "").replace("http://", "").split("/")[0]
        
        # Phase 3: Swarm
        prospect_profile = run_auditor(prospect_domain)
        context_signals = run_context_hunter(prospect_domain, prospect_profile.get("raw_text", ""))
        gap_analysis = identify_gaps(request.service_catalog, prospect_profile, context_signals)
        
        # Phase 4: Verdict & Strategy
        verdict_data = generate_verdict(gap_analysis, context_signals)
        report = generate_report(prospect_profile, context_signals, gap_analysis, verdict_data, request.service_catalog)
        
        report["mode"] = "prospect"
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Report Generation Endpoints ───────────────────────────────────────────────

@app.post("/generate-report")
async def generate_report(data: Dict[str, Any]):
    """
    Generate two PDFs (Internal Strategic Intel & Outreach Blueprint).
    Returns URLs to the generated static files.
    """
    try:
        domain = data.get("domain", "unknown").replace(".", "_")
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        intel_filename = f"strategic_intel_{domain}_{timestamp}.pdf"
        outreach_filename = f"outreach_blueprint_{domain}_{timestamp}.pdf"
        
        intel_path = os.path.join(REPORTS_DIR, intel_filename)
        outreach_path = os.path.join(REPORTS_DIR, outreach_filename)
        
        # Run generation
        generate_strategic_risk_report(data, intel_path)
        generate_executive_targeting_report(data, outreach_path)
        
        return {
            "enterprise_pdf_url": f"/reports/{intel_filename}",
            "outreach_pdf_url": f"/reports/{outreach_filename}"
        }
    except Exception as e:
        logging.error("Failed to generate PDF: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# Watchlist Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/watchlist", response_model=List[WatchlistOut])
def list_watchlist(db: Session = Depends(get_db)):
    return db.query(WatchlistEntry).filter(WatchlistEntry.is_active == True).order_by(WatchlistEntry.added_at.desc()).all()  # noqa: E712


@app.post("/watchlist", response_model=WatchlistOut, status_code=201)
def add_to_watchlist(request: WatchlistAddRequest, db: Session = Depends(get_db)):
    existing = db.query(WatchlistEntry).filter(WatchlistEntry.domain == request.domain).first()
    if existing:
        if not existing.is_active:
            existing.is_active = True
            existing.company_name = request.company_name
            existing.classification = request.classification
            existing.lead_score = request.lead_score
            existing.strategic_pressure = request.strategic_pressure
            db.commit()
            db.refresh(existing)
            return existing
        raise HTTPException(status_code=409, detail=f"{request.domain} is already on the watchlist")

    entry = WatchlistEntry(
        company_name=request.company_name,
        domain=request.domain,
        industry=request.industry,
        classification=request.classification,
        lead_score=request.lead_score,
        strategic_pressure=request.strategic_pressure,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@app.delete("/watchlist/{entry_id}", status_code=204)
def remove_from_watchlist(entry_id: int, db: Session = Depends(get_db)):
    entry = db.query(WatchlistEntry).filter(WatchlistEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Watchlist entry not found")
    entry.is_active = False
    db.commit()


@app.post("/watchlist/{entry_id}/scan")
def scan_now(entry_id: int, db: Session = Depends(get_db)):
    entry = db.query(WatchlistEntry).filter(WatchlistEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Watchlist entry not found")
    # Run scan in background thread
    import threading
    thread = threading.Thread(
        target=monitoring_agent.scan_one_now,
        args=(entry.domain,),
        daemon=True,
    )
    thread.start()
    return {"message": f"Scan triggered for {entry.company_name}", "domain": entry.domain}


# ═══════════════════════════════════════════════════════════════════════════════
# Alert Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/alerts", response_model=List[AlertOut])
def list_alerts(unread_only: bool = False, db: Session = Depends(get_db)):
    q = db.query(Alert)
    if unread_only:
        q = q.filter(Alert.is_read == False)  # noqa: E712
    return q.order_by(Alert.detected_at.desc()).limit(100).all()


@app.get("/alerts/unread-count")
def unread_count(db: Session = Depends(get_db)):
    count = db.query(Alert).filter(Alert.is_read == False).count()  # noqa: E712
    return {"count": count}


@app.post("/alerts/{alert_id}/read", response_model=AlertOut)
def mark_alert_read(alert_id: int, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.is_read = True
    db.commit()
    db.refresh(alert)
    return alert


@app.post("/alerts/read-all")
def mark_all_read(db: Session = Depends(get_db)):
    db.query(Alert).filter(Alert.is_read == False).update({"is_read": True})  # noqa: E712
    db.commit()
    return {"message": "All alerts marked as read"}


@app.delete("/alerts/{alert_id}", status_code=204)
def delete_alert(alert_id: int, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    db.delete(alert)
    db.commit()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
