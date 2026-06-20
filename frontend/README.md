# SecEff Frontend

This folder contains the static HTML frontend for the SecEff demo. It is not a React, Vite, or build-step frontend.

## Pages

| File | Purpose |
| --- | --- |
| `index.html` | Main overview and feature entry page. |
| `secure-lean-cloud.html` | Feature 1: Cloud Security. |
| `lower-carbon-lower-cost.html` | Feature 2: Resource Efficiency. |
| `continuous-optimization.html` | Feature 3: Carbon Footprint. |
| `construction-ready-ops.html` | Feature 4: AI Recommendation and projected savings. |
| `optimization_data.js` | Shared static optimization data used by frontend pages. |

## How To Open

Start the backend from the project root:

```powershell
cd backend
npm install
npm run dev
```

Then open:

```text
http://localhost:5000/frontend/index.html
```

Use the backend URL instead of opening the HTML files directly when testing API-powered pages. Feature 1 and Feature 4 call backend endpoints under `/api`.

## Related Backend APIs

| API | Used By |
| --- | --- |
| `/api/security/summary` | Cloud Security score cards. |
| `/api/security/findings` | Findings table. |
| `/api/security/dashboard` | Security dashboard charts. |
| `/api/security/graph` | Security graph visualization. |
| `/api/analyze` | AI recommendation, cost saved, and carbon reduced. |

For the full architecture and setup notes, see the root `README.md`.
