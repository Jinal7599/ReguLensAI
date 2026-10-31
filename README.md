# ReguLens AI

ReguLens AI is a regulatory intelligence and change impact assessment prototype. It is designed to help compliance teams discover publications, understand obligations, compare regulatory clauses and assess potential business impact.

## Architecture

The application is split into two independently deployable services:

- **Frontend:** React + TypeScript + Vite in `frontend/`
- **Backend:** FastAPI in `backend/`
- **API contract:** JSON REST endpoints under `/api/v1`
- **Deployment:** Render Blueprint with a static frontend and Python API service

The browser communicates with the backend over HTTP. The backend owns application data and business logic; the frontend handles presentation and user interactions.

## Current iteration

- Overview dashboard with summary metrics and regional coverage
- Searchable regulatory publication feed with region and status filters
- Change analysis with previous/updated clause panels and review actions
- Settings view showing the four target regional source groups
- FastAPI health, overview, publication, change and source endpoints
- Backend API tests and local Vite proxy

**All bundled publications and clause examples are synthetic demo data. They are not official regulatory publications and must not be used to make compliance decisions.** Live source monitoring, Gemini integration, OAuth and persistent storage are not enabled yet.

## Requirements

- Python 3.11+
- Node.js 20.19+ (or compatible newer LTS release)
- npm

## Run locally

### 1. Start the API

From the repository root:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

API health: http://127.0.0.1:8000/api/v1/health  
Interactive API docs: http://127.0.0.1:8000/docs

### 2. Start the frontend

In a second terminal, from the repository root:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. Vite proxies local `/api` requests to FastAPI on port 8000.

### 3. Run backend tests

From the repository root:

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/overview` | Dashboard metrics and coverage |
| GET | `/api/v1/publications` | Publication search and filters |
| GET | `/api/v1/changes` | Synthetic change assessments |
| GET | `/api/v1/sources` | Regional source configuration |

## Render deployment

The root `render.yaml` describes two services:

1. `regulens-ai-api` — Python web service rooted at `backend/`.
2. `regulens-ai-frontend` — static site rooted at `frontend/`.

Create a Blueprint deployment in Render using this repository. Set `ALLOWED_ORIGINS` on the API service to the frontend's deployed origin (for example, `https://your-frontend.onrender.com`). Set `VITE_API_BASE_URL` on the frontend service to the API's public URL (for example, `https://your-api.onrender.com`) and trigger a frontend redeploy after changing it. The sample service names in `render.yaml` may need adjustment if already taken.

Do not commit API keys, OAuth secrets, database credentials or other secrets. Add them through Render's environment settings when the corresponding integrations are implemented.

## Development principles

- Keep API routes versioned under `/api/v1`.
- Keep regulatory connectors, document processing and AI orchestration in backend modules.
- Keep the React frontend focused on presentation and user interactions.
- Keep deterministic comparison and evidence extraction separate from LLM-generated interpretation.
- Add PostgreSQL and object storage when milestones define the required records and retention behaviour.

## Disclaimer

This prototype is not certified for regulatory compliance. Regulatory interpretations and AI-generated recommendations require qualified human review.
