# DataVex — Strategic Enterprise Intelligence Engine

Run both the backend and frontend with the commands below.

---

## Prerequisites

- Python ≥ 3.9 with `fastapi` and `uvicorn` installed
- Node.js ≥ 18 with npm

---

## 1 — Start the FastAPI Backend

```powershell
# From the repo root
cd d:\Sahyadri\VexStorm_Track2

# Run the backend server
uvicorn backend.main:app --reload --port 8000
```

The API will be available at: **http://localhost:8000**

Interactive docs: **http://localhost:8000/docs**

---

## 2 — Start the React Frontend

```powershell
# In a new terminal
cd d:\Sahyadri\VexStorm_Track2\frontend

npm run dev
```

The app will open automatically at: **http://localhost:5173**

---

## Project Structure

```
VexStorm_Track2/
├── backend/
│   ├── main.py              # FastAPI server (POST /analyze-domain, POST /analyze-region)
│   └── mock_response.json   # Example API response for testing
│
├── company_discovery/       # Existing intelligence engine (unchanged)
│   ├── main.py
│   ├── intelligence.py
│   ├── scoring.py
│   └── ...
│
└── frontend/
    ├── src/
    │   ├── App.jsx                       # Main app shell + layout
    │   ├── api.js                        # API client + mock data
    │   ├── index.css                     # Design system (Tailwind + custom tokens)
    │   └── components/
    │       ├── AnalysisForm.jsx          # Input: domain/region toggle + fields
    │       ├── SummaryCard.jsx           # Section 1: company info + pressure gauge
    │       ├── LeadScoreChart.jsx        # Section 2: radar chart + score
    │       ├── SignalsPanel.jsx          # Section 3: growth, scale, trigger signals
    │       ├── BottleneckCards.jsx       # Section 4: bottlenecks with severity
    │       ├── OutreachStrategy.jsx      # Section 5: outreach email + copy button
    │       ├── ResearchTrace.jsx         # Section 6: agent reasoning timeline
    │       └── RegionResultCards.jsx     # Region mode: discovery result cards
    ├── vite.config.js
    ├── tailwind.config.js
    └── package.json
```

---

## API Reference

### POST /analyze-domain
```json
{
  "domain": "druva.com",
  "threshold": "10Cr+"
}
```

### POST /analyze-region
```json
{
  "region": "Pune",
  "threshold": "10Cr+"
}
```

---

## Testing with Mock Data

To test without the backend, open `src/api.js` and use the exported mock objects
(`MOCK_DOMAIN_RESPONSE`, `MOCK_REGION_RESPONSE`) directly in `App.jsx`.
