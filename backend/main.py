import sys
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

# Add the parent directory to sys.path to allow importing from company_discovery
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from company_discovery.main import run_domain_pipeline, run_region_pipeline
except ImportError as e:
    print(f"Error importing company_discovery: {e}")
    # Fallback or dummy functions for testing if imports fail during initialization
    def run_domain_pipeline(domain: str, threshold: Optional[str] = None):
        return {"error": "Module not found", "domain": domain}
    def run_region_pipeline(region: str, threshold: str):
        return []

app = FastAPI(
    title="Strategic Enterprise Intelligence Engine API",
    description="Backend for the Strategic Enterprise Intelligence Engine",
    version="1.0.0"
)

# Setup CORS for frontend development (default Vite port is 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DomainAnalysisRequest(BaseModel):
    domain: str
    threshold: Optional[str] = None

class RegionAnalysisRequest(BaseModel):
    region: str
    threshold: str

@app.get("/")
async def root():
    return {"message": "Strategic Enterprise Intelligence Engine API is running"}

@app.post("/analyze-domain")
async def analyze_domain(request: DomainAnalysisRequest):
    """Deep-research a single company domain."""
    try:
        results = run_domain_pipeline(request.domain, request.threshold)
        if results.get("error"):
            raise HTTPException(status_code=400, detail=results["error"])
        return results
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze-region")
async def analyze_region(request: RegionAnalysisRequest):
    """Discover companies in a region."""
    try:
        results = run_region_pipeline(request.region, request.threshold)
        return results
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
