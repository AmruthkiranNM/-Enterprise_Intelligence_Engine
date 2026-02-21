import requests
import json
import os

def test_generate_report():
    url = "http://localhost:8000/generate-report"
    
    # Load mock data
    mock_data_path = os.path.join("backend", "mock_response.json")
    with open(mock_data_path, "r") as f:
        data = json.load(f)
    
    # Add domain if missing
    if "domain" not in data:
        data["domain"] = "druva.com"
        
    print(f"Calling {url}...")
    response = requests.post(url, json=data)
    
    if response.status_code == 200:
        print("Success!")
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"Failed! Status code: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    test_generate_report()
