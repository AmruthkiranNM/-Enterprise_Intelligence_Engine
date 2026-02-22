import sys
import os
import logging

# Adjust path to include the backend directory so 'database' and 'monitor' are findable
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__)))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
sys.path.append(ROOT_DIR)
sys.path.append(BACKEND_DIR)

from backend.database.db import SessionLocal, init_db, engine
from backend.database.models import Alert
from backend.monitor import scan_company
from backend.database.models import WatchlistEntry
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)

def verify_pipeline():
    print("--- Initializing Strategic Alert Architecture Verification ---")
    
    # Force Drop for Verification (Dev environment reset)
    print("Resetting database tables for new architecture...")
    try:
        with engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS alerts"))
            # For SQLAlchemy 1.4+
            if hasattr(conn, 'commit'):
                conn.commit()
        init_db()
        print("Table 'alerts' recreated.")
    except Exception as e:
        print(f"Non-critical error resetting table: {e}")

    db = SessionLocal()
    
    # Try to find or create a watchlist entry
    entry = db.query(WatchlistEntry).first()
    if not entry:
        print("No watchlist entry found. Creating a test entry for 'NVIDIA'...")
        entry = WatchlistEntry(
            company_name="NVIDIA",
            domain="nvidia.com",
            industry="Semiconductors",
            classification="Strategic"
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)

    print(f"Running scan for: {entry.company_name} ({entry.domain})...")
    try:
        # Note: In monitor.py, scan_company imports from 'database.models'.
        # Since we added BACKEND_DIR to sys.path, it should resolve.
        new_alerts = scan_company(entry, db)
        print(f"Scan complete. New alerts created: {new_alerts}")
        
        # Verify the latest alert structure
        latest = db.query(Alert).filter(Alert.company_name == entry.company_name).order_by(Alert.detected_at.desc()).first()
        if latest:
            print(f"Latest Alert Found: {latest.headline}")
            print(f"Strategic Impact Index: {latest.impact_index}")
            print(f"Action Level: {latest.action_level}")
            print(f"Source: {latest.source} ({latest.url})")
            print(f"Breakdown: MV:{latest.market_visibility}, FP:{latest.financial_pressure}, OS:{latest.operational_strain}, SA:{latest.service_alignment}")
        else:
            print("No alerts were generated. (Either no new data on RSS/Tavily or API key missing).")
            
    except Exception as e:
        print(f"Pipeline Failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    verify_pipeline()
