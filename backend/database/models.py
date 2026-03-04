"""
database/models.py — SQLAlchemy ORM models for the monitoring system
"""
import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float
from database.db import Base


class WatchlistEntry(Base):
    """A company being actively monitored."""
    __tablename__ = "watchlist"

    id = Column(Integer, primary_key=True, index=True)
    company_name       = Column(String(255), nullable=False)
    domain             = Column(String(255), nullable=False, unique=True)
    industry           = Column(String(255), default="Unknown")
    classification     = Column(String(100), default="Not Priority")
    lead_score         = Column(Float, default=0.0)
    strategic_pressure = Column(Float, default=0.0)
    added_at           = Column(DateTime, default=datetime.datetime.utcnow)
    last_scan_at       = Column(DateTime, nullable=True)
    last_trigger_snapshot = Column(Text, default="[]")   # JSON list of trigger strings
    is_active          = Column(Boolean, default=True)


class Alert(Base):
    """A detected strategic trigger event for a monitored company."""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    company_name   = Column(String(255), nullable=False)
    domain         = Column(String(255), nullable=False, index=True)
    event_type     = Column(String(100), nullable=False)   # Funding / Hiring / Acquisition / Product / Leadership
    headline       = Column(String(500), nullable=False)
    source         = Column(String(100), nullable=True)
    url            = Column(Text, nullable=True)
    event_date     = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Analytical Scoring
    impact_index       = Column(Float, default=0.0)
    market_visibility   = Column(Float, default=0.0)
    financial_pressure  = Column(Float, default=0.0)
    operational_strain  = Column(Float, default=0.0)
    service_alignment   = Column(Float, default=0.0)
    
    severity_label     = Column(String(50), default="Informational")
    action_level       = Column(String(50), default="Monitor")
    impact_drivers     = Column(Text, default="[]")  # JSON list
    strategic_relevance = Column(Text, nullable=True)
    confidence_score   = Column(Float, default=0.0)

    detected_at    = Column(DateTime, default=datetime.datetime.utcnow)
    is_read        = Column(Boolean, default=False)
    email_sent     = Column(Boolean, default=False)

class ServiceCatalog(Base):
    """The user's own company service capabilities for gap analysis."""
    __tablename__ = "service_catalog"

    id = Column(Integer, primary_key=True, index=True)
    company_name   = Column(String(255), nullable=False)
    company_url    = Column(String(255), nullable=False, unique=True)
    industry       = Column(String(255), default="Unknown")
    services       = Column(Text, default="[]") # JSON list
    tech_expertise = Column(Text, default="[]") # JSON list
    target_industries = Column(Text, default="[]") # JSON list
    created_at     = Column(DateTime, default=datetime.datetime.utcnow)
