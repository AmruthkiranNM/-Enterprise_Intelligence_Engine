"""
database/models.py — SQLAlchemy ORM models for the monitoring system
"""
import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float
from .db import Base


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
    event_summary  = Column(Text, nullable=False)
    severity       = Column(String(20), default="Medium")  # Low / Medium / High
    impact_score   = Column(Float, default=50.0)
    confidence     = Column(String(20), default="Medium")  # Low / Medium / High
    suggested_action = Column(Text, nullable=True)
    detected_at    = Column(DateTime, default=datetime.datetime.utcnow)
    is_read        = Column(Boolean, default=False)
    email_sent     = Column(Boolean, default=False)
