# SecEff

AI-powered cloud security, resource efficiency, and carbon intelligence for construction platforms.

## Project Title and Description

**SecEff** is a cloud governance demo built for construction technology teams. It helps teams understand whether their connected cloud platforms are secure, resource-efficient, and carbon-aware.

The platform analyzes a mock cloud estate dataset and turns raw scan data into four connected outputs:

- **Cloud Security**: public access, risky ports, encryption gaps, identity risk, and attack paths.
- **Resource Efficiency**: idle, orphaned, underused, and over-provisioned workloads.
- **Carbon Footprint**: monthly carbon impact based on energy usage and regional carbon intensity.
- **AI Recommendation**: practical next actions for reducing security risk, cost waste, and carbon emissions.

Instead of showing separate dashboards for security, cost, and sustainability, SecEff combines them into one decision layer for safer and leaner cloud operations.

## Team Name and Team Members

**Team Name:** Chill Chill

**Team Members:**

- Aloysius Ting Zi Heng
- Edixon Teo Zan Wei
- Hing Zhen Nam
- Chong Yi Han
- Hassan Mehdi

## Technologies Used

- **HTML, CSS, JavaScript** - static frontend pages and interactive UI.
- **Node.js** - backend runtime.
- **Express.js** - REST API server and static frontend hosting.
- **CORS** - frontend/backend API access.
- **Python** - backend analysis worker for Feature 4.
- **JSON** - mock cloud estate dataset and API response format.
- **vis-network** - cloud security relationship graph visualization.
- **Chart.js** - dashboard charts and metrics visualization.
- **Anthropic API** - optional AI recommendation generation when an API key is available.
- **Local rule-based recommendation engine** - fallback recommendation logic when no API key is configured.
- **GitHub** - version control and project submission.

## Challenge and Approach

### Challenge

Construction cloud platforms often support many different workflows: worker safety AI, BIM processing, IoT monitoring, site analytics, and operational dashboards. These systems can create security exposure, wasted cloud spend, and high carbon impact.

The main challenge is that these problems are usually reviewed separately:

- security teams look at vulnerabilities and attack paths;
- operations teams look at resource usage and cost;
- sustainability teams look at energy and carbon impact.

This makes it hard to decide which cloud resources need attention first.

### Approach

SecEff uses one shared mock cloud dataset and runs it through four engines:

1. **Security Audit** identifies risky cloud configurations and connected attack paths.
2. **Resource Efficiency** detects idle, orphaned, and over-provisioned resources.
3. **Carbon Intelligence** estimates carbon emissions using energy consumption and regional carbon intensity.
4. **AI Recommendation** summarizes the best next actions based on security, cost, and carbon impact.

The goal is not just to detect problems, but to explain which actions will create the highest operational value.

### Cost and Carbon Logic

Cost savings are only counted when a resource is wasteful. Fixing a security issue does not automatically reduce cost.

```text
Idle or orphaned resource:
saved_per_month = monthly_cost * 1.0

Over-provisioned resource:
saved_per_month = monthly_cost * 0.6

Security-only or healthy resource:
saved_per_month = 0
```

Carbon emissions are calculated with:

```text
carbon_kg = kwh_month * region_carbon_intensity / 1000
```

Carbon reduction follows the same waste-removal logic:

```text
Idle or orphaned resource:
reduced_carbon_kg = carbon_kg * 1.0

Over-provisioned resource:
reduced_carbon_kg = carbon_kg * 0.6

Security-only or healthy resource:
reduced_carbon_kg = 0
```

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

The active demo is served by `backend/server.js`. Older prototype scripts are kept in `legacy/prototypes/` for reference only.

## Usage Instructions

### Prerequisites

- Node.js
- npm
- Python 3

Optional:

- `ANTHROPIC_API_KEY` for remote AI recommendations.
- If no API key is configured, SecEff uses the local fallback recommendation engine.

### Run the Project

From the project root:

```powershell
cd backend
npm install
npm run dev
```

Open the frontend:

```text
http://localhost:5000/frontend/index.html
```

Health check:

```text
http://localhost:5000/api/health
```

Feature 4 analysis API:

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

## Demo Notes

- The frontend should be opened through `http://localhost:5000/frontend/index.html`.
- Do not open Feature 4 from a different static server if it needs `/api/analyze`.
- The dataset filename is still `hilti-cloud-data.json` for compatibility with the current code, even though the visible product name is SecEff.
- The frontend is intentionally static and does not require a bundler.
