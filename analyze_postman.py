import sys
import os
import json

# Add the project root to sys.path
sys.path.append(os.getcwd())

from company_discovery.main import run_domain_pipeline

def analyze_postman():
    print("Running analysis pipeline for postman.com...")
    # Postman is a well-known scaleup, so we use Medium/High threshold context
    result = run_domain_pipeline("postman.com", threshold="medium")
    
    # Save results to a file for review
    with open("postman_analysis_raw.json", "w") as f:
        json.dump(result, f, indent=2)
    
    print("\nAnalysis Complete. Results saved to postman_analysis_raw.json")
    print(f"Lead Score: {result.get('lead_score', {}).get('total')}")
    print(f"Classification: {result.get('lead_score', {}).get('classification')}")

if __name__ == "__main__":
    analyze_postman()
