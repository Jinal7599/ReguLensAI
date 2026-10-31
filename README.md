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

**All bundled publications and clause examples are synthetic demo data. They are not official regulatory publications and must not be used to make compliance decisions.** Live source monitoring, OAuth and persistent storage are not enabled yet.

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
python -m pytest
```

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/overview` | Dashboard metrics and coverage |
| GET | `/api/v1/publications` | Publication search and filters |
| GET | `/api/v1/changes` | Synthetic change assessments |
| GET | `/api/v1/sources` | Regional source configuration |\n| POST | `/api/v1/documents/analyze` | Upload and analyze a PDF, DOCX or TXT document |

## Render deployment

This repository uses a Render Blueprint, similar to MailStorm, to provision the frontend and API together.

1. Open the Render Dashboard and choose **New → Blueprint**.
2. Connect the GitHub repository `pancholi-deep/ReguLensAI`.
3. Select the feature branch containing the React + FastAPI foundation while PR #1 is still open. After merging, use `main`.
4. Render reads the root `render.yaml` and proposes two services:
   - `regulens-ai-api` — Python web service rooted at `backend/`.
   - `regulens-ai-frontend` — static site rooted at `frontend/`.
5. Complete the initial deploy. Render will assign each service a public `onrender.com` URL.
6. In the API service's environment settings, set `ALLOWED_ORIGINS` to the exact frontend origin, e.g. `https://regulens-ai-frontend.onrender.com` (no trailing slash).
7. In the frontend static site's environment settings, set `VITE_API_BASE_URL` to the API's public origin, e.g. `https://regulens-ai-api.onrender.com` (no trailing slash).
8. Trigger a new frontend deploy after setting `VITE_API_BASE_URL`, because Vite embeds this value at build time. Redeploy the API after changing `ALLOWED_ORIGINS`.

Verify the deployment:
- API health: `https://<api-service>.onrender.com/api/v1/health`
- API docs: `https://<api-service>.onrender.com/docs`
- Open the frontend URL and confirm that the dashboard loads API data.

The Blueprint uses Render's Free plan for the initial prototype. Free services may spin down when idle and take time to wake on the next request. Change the plan in Render if always-on availability is needed. The sample service names in `render.yaml` may need adjustment if already taken in your Render workspace.

To test the upload flow, use the synthetic example at `examples/sample_synthetic_rbi_circular.txt` (this is invented sample content, not an official RBI document). Gemini extraction is implemented but should remain disabled on the public deployment until Google OAuth / access control and abuse protections are added: the current API is public, so an exposed upload endpoint could consume your API quota. For a private local test environment only, set `GEMINI_API_KEY` on the backend. The default model is `gemini-flash-latest`; override it with `GEMINI_MODEL` when needed. Never put the key in the frontend or commit it to GitHub. Without the key, uploads still work through a rule-based candidate-clause extractor.\n\nThe current upload flow does not retain documents or extracted results on the server. Render Free web services have ephemeral filesystems, so persistent publication history and document storage are a later milestone. Do not upload confidential customer or production documents to this prototype.

## Development principles

- Keep API routes versioned under `/api/v1`.
- Keep regulatory connectors, document processing and AI orchestration in backend modules.
- Keep the React frontend focused on presentation and user interactions.
- Keep deterministic comparison and evidence extraction separate from LLM-generated interpretation.
- Add PostgreSQL and object storage when milestones define the required records and retention behaviour.

## Disclaimer

This prototype is not certified for regulatory compliance. Regulatory interpretations and AI-generated recommendations require qualified human review.
