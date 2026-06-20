# SecEff

SecEff is a cloud governance demo for construction platforms. It connects cloud security, resource efficiency, carbon footprint tracking, and AI recommendations into one static frontend and one Node.js backend.

The project is built for a hackathon-style workflow: the frontend stays as plain HTML/CSS/JavaScript, while the backend reads a mock cloud estate dataset, analyzes risk and waste, calculates cost/carbon impact, and serves API responses for the dashboards.

## Key Features

- Cloud Security: finds public access, risky ports, encryption gaps, identity risk, and attack paths.
- Resource Efficiency: detects idle, orphaned, underused, and over-provisioned cloud resources.
- Carbon Footprint: estimates monthly carbon impact from energy use and regional carbon intensity.
- AI Recommendation: generates practical next actions using an API key when available, with a local fallback when not.
- Unified Demo UI: serves all feature pages from the same backend at `http://localhost:5000/frontend/index.html`.

## System Architecture

```text
Mock cloud estate dataset
backend/data/hilti-cloud-data.json
        |
        v
Node.js / Express backend
backend/server.js
        |
        +-- /api/security/*
        |       |
        |       v
        |   Security Analyzer
        |   backend/services/securityAnalyzer.js
        |
        +-- /api/analyze
        |       |
        |       v
        |   Python Feature 4 worker
        |   backend/python/analyze_feature4.py
        |       |
        |       v
        |   AI Recommendation Service
        |   backend/services/opsAiRecommendations.js
        |
        +-- /frontend/*
        |       |
        |       v
        |   Static HTML pages
        |   frontend/*.html
        |
        +-- /pic/*
                |
                v
            Visual assets
            pic/*.jpg, pic/*.png
```

## Architecture Layers

| Layer | Role | Main Files |
| --- | --- | --- |
| Data Sources | Mock cloud resources, relationships, usage, cost, security settings, and carbon inputs. | `backend/data/hilti-cloud-data.json` |
| Backend | Express server, CORS, JSON middleware, static frontend hosting, and API routing. | `backend/server.js` |
| Core Engines | Security audit, resource efficiency, carbon intelligence, and AI recommendation logic. | `backend/services/*`, `backend/python/analyze_feature4.py` |
| Frontend | Static dashboard pages with existing SecEff visual style. No React, no Vite, no build step. | `frontend/*.html` |
| Assets | Homepage and feature visuals. | `pic/*` |

## Project Structure

```text
ImagineHack/
  backend/
    data/
      hilti-cloud-data.json
    python/
      analyze_feature4.py
    routes/
      opsRoutes.js
      securityRoutes.js
    services/
      opsAiRecommendations.js
      opsAnalyzerRunner.js
      securityAnalyzer.js
    package.json
    server.js

  frontend/
    index.html
    secure-lean-cloud.html
    lower-carbon-lower-cost.html
    continuous-optimization.html
    construction-ready-ops.html
    optimization_data.js
    README.md

  pic/
    front.png
    images1.jpg
    images2.jpg
    images3.jpg
    images4.jpg

  legacy/
    prototypes/
      README.md
      old Python and JSX prototype files
```

Note: the active demo is served by `backend/server.js`. Older prototype scripts were moved into `legacy/prototypes/` so the project root only contains active entry points and documentation.

## Requirements

- Node.js
- npm
- Python 3

Optional:

- `ANTHROPIC_API_KEY` for remote AI recommendations.
- If no API key is configured, Feature 4 automatically uses the local recommendation fallback.

## How To Run

From the project root:

```powershell
cd backend
npm install
npm run dev
```

Then open:

```text
http://localhost:5000/frontend/index.html
```

Backend health check:

```text
http://localhost:5000/api/health
```

Feature 4 API:

```text
http://localhost:5000/api/analyze
```

If your machine uses `py` instead of `python`, run this before starting the backend:

```powershell
$env:PYTHON_BIN="py"
npm run dev
```

## Frontend Pages

| Page | Purpose |
| --- | --- |
| `frontend/index.html` | Main SecEff overview and feature entry page. |
| `frontend/secure-lean-cloud.html` | Feature 1: Cloud Security dashboard, findings, and graph. |
| `frontend/lower-carbon-lower-cost.html` | Feature 2: Resource efficiency and waste detection. |
| `frontend/continuous-optimization.html` | Feature 3: Carbon footprint and optimization insights. |
| `frontend/construction-ready-ops.html` | Feature 4: AI recommendations, cost saved, and carbon reduced. |

## API Endpoints

| Endpoint | Description |
| --- | --- |
| `GET /api/health` | Confirms the backend is running. |
| `GET /api/security/summary` | Cloud security score and summary counts. |
| `GET /api/security/findings` | Security findings, with optional filters. |
| `GET /api/security/dashboard` | Dashboard metrics for Feature 1. |
| `GET /api/security/graph` | Resource graph nodes and relationships. |
| `GET /api/security/resources/:id` | Details for a selected cloud resource. |
| `GET /api/analyze` | Feature 4 output: current state, recommendations, and projected results. |

## Analysis Logic

### Cloud Security

The security engine reviews each resource for issues such as public exposure, risky open ports, missing encryption, weak identity controls, and risky relationships. It returns findings, severity levels, dashboard totals, and graph data.

### Resource Efficiency

The efficiency logic identifies waste by checking utilization, cost, ownership, and idle/orphaned state. Resources can be classified as healthy, idle/orphaned, underused, or over-provisioned.

### Carbon Footprint

Monthly carbon impact is calculated with:

```text
carbon_kg = kwh_month * region_carbon_intensity / 1000
```

Example:

```text
1450 kWh * 408 gCO2/kWh / 1000 = 591.6 kgCO2
```

### Cost Saved

Savings are calculated only for wasteful resources:

```text
Idle or orphaned resource:
saved_per_month = monthly_cost * 1.0

Over-provisioned resource:
saved_per_month = monthly_cost * 0.6

Security-only or healthy resource:
saved_per_month = 0
```

### Reduced Carbon Emission

Carbon reduction follows the same waste-removal logic:

```text
Idle or orphaned resource:
reduced_carbon_kg = carbon_kg * 1.0

Over-provisioned resource:
reduced_carbon_kg = carbon_kg * 0.6

Security-only or healthy resource:
reduced_carbon_kg = 0
```

## AI Recommendation Flow

Feature 4 checks for an API key before generating recommendations:

1. If `ANTHROPIC_API_KEY` or `API_KEY` exists, the backend calls the remote AI model.
2. If no key exists, or the remote call fails, the backend uses the local fallback model.
3. The response still uses the same dashboard shape, so the frontend keeps working either way.

## Environment Variables

| Variable | Purpose |
| --- | --- |
| `PORT` | Backend port. Defaults to `5000`. |
| `PYTHON_BIN` | Python command used by Node. Defaults to `python`. |
| `ANTHROPIC_API_KEY` | Optional API key for AI recommendations. |
| `API_KEY` | Alternate optional API key name. |
| `ANTHROPIC_MODEL` | Optional model override. |
| `OPS_ANALYZER_TIMEOUT_MS` | Timeout for the Python analyzer worker. |
| `AI_RECOMMENDATION_TIMEOUT_MS` | Timeout for AI recommendation calls. |

## Development Notes

- Run the frontend through the backend URL: `http://localhost:5000/frontend/index.html`.
- Do not open Feature 4 from a different static server if it needs `/api/analyze`.
- The dataset filename is still `hilti-cloud-data.json` for compatibility with the current code, even though the visible product name is SecEff.
- The frontend is intentionally static and does not require a bundler.
