# ReguLens AI

ReguLens AI is a regulatory intelligence and change impact assessment prototype. It helps compliance teams discover publications, understand obligations, compare regulatory clauses and assess potential business impact.

## Architecture

- **Frontend:** React + TypeScript + Vite in frontend/
- **Backend:** FastAPI in backend/
- **Database:** PostgreSQL in production; local SQLite fallback for development
- **Migrations:** Alembic in backend/migrations/
- **API contract:** JSON REST endpoints under /api/v1
- **Deployment:** Render Blueprint with a static frontend and Python API service

The browser communicates with the backend over HTTP. The backend owns application data and business logic; the frontend handles presentation and user interactions.

## Current iteration

- Overview dashboard with summary metrics and regional coverage
- Searchable regulatory publication feed with region and status filters
- Change analysis with previous/updated clause panels and review actions (currently synthetic examples)
- Settings view showing four target regional source groups
- Manual PDF, DOCX and TXT upload with Gemini structured extraction and rule-based fallback
- PostgreSQL-ready persistence for authorities, instruments, publications, document versions, extracted sections, obligations, document relationships and analysis jobs
- SHA-256 duplicate detection; identical uploads reuse the existing document version
- Persisted extracted text and analysis results can be listed and reopened after a browser refresh in local development
- Alembic initial schema migration and API tests for persistence

**All bundled publications and clause examples are synthetic demo data. They are not official regulatory publications and must not be used to make compliance decisions.** Live source monitoring, automatic historical matching, clause comparison, OAuth and original-file object storage are not enabled yet.

## Requirements

- Python 3.11+
- Node.js 20.19+ (or compatible newer LTS release)
- npm
- PostgreSQL for shared / production persistence (SQLite is used automatically for local development if DATABASE_URL is empty)

## Run locally

### 1. Configure the backend

Create a repository-root .env file (it is Git-ignored):

    cp .env.example .env

Set GEMINI_API_KEY if you want LLM extraction. Set DATABASE_URL to a PostgreSQL URL to use PostgreSQL locally; otherwise the backend creates backend/.local/regulens.db using SQLite.

Install dependencies and apply the schema:

    cd backend
    python -m venv .venv
    source .venv/bin/activate  # Windows: .venv\Scripts\activate
    pip install -r requirements-dev.txt
    alembic upgrade head
    uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

- API health: http://127.0.0.1:8000/api/v1/health
- Storage diagnostics: http://127.0.0.1:8000/api/v1/diagnostics/storage
- Interactive API docs: http://127.0.0.1:8000/docs

### 2. Start the frontend

In a second terminal, from the repository root:

    cd frontend
    npm install
    npm run dev

Open http://localhost:5173. Vite proxies local /api requests to FastAPI on port 8000.

### 3. Run backend tests

From the repository root:

    cd backend
    pip install -r requirements-dev.txt
    python -m pytest -q

Tests use isolated SQLite databases and do not call the Gemini API. CI also runs the Alembic migration against SQLite.

## Persistence behaviour

- POST /api/v1/documents uploads, analyzes and persists a PDF, DOCX or TXT document. The existing POST /api/v1/documents/analyze route remains as a compatibility alias.
- GET /api/v1/documents lists persisted document versions with search, jurisdiction filter and pagination.
- GET /api/v1/documents/{document_version_id} returns the stored extraction result and source-section references.
- GET /api/v1/publications includes persisted uploads alongside synthetic demo records in local development.
- SHA-256 hashes prevent the same file content from being analyzed and stored repeatedly.

The database stores extracted text, metadata, source sections, obligations and the structured extraction result. **The original uploaded binary is not retained in this milestone**; object storage and download/retention policies are a later step. Do not upload confidential customer or production documents.

## Render deployment

1. Provision a managed PostgreSQL database in Render (or use another reachable PostgreSQL provider).
2. Set the API service's DATABASE_URL to the database connection string. Use the internal database URL when the database and API are in the same Render region.
3. Keep APP_ENV=production. The database schema can be migrated, but document upload/list/detail APIs remain disabled on the public deployment until authentication and access controls are implemented. The API also refuses persistent uploads when DATABASE_URL is missing rather than silently writing to Render's ephemeral filesystem.
4. Set ALLOWED_ORIGINS to the exact frontend origin, e.g. https://regulens-ai-frontend.onrender.com (no trailing slash).
5. Set frontend VITE_API_BASE_URL to the API origin, e.g. https://regulens-ai-api.onrender.com, and redeploy the frontend because Vite embeds this value at build time.
6. The API start command runs alembic upgrade head when DATABASE_URL is configured, then starts FastAPI.

Verify:
- API health: https://<api-service>.onrender.com/api/v1/health
- Storage diagnostics: https://<api-service>.onrender.com/api/v1/diagnostics/storage
- API docs: https://<api-service>.onrender.com/docs

Keep Gemini disabled on a public upload API until authentication / access controls, rate limiting and abuse protections are enabled. Never put the key in frontend environment variables or commit it to GitHub.

## Development principles

- Keep API routes versioned under /api/v1.
- Keep regulatory connectors, document processing and AI orchestration in backend modules.
- Keep deterministic comparison and evidence extraction separate from LLM-generated interpretation.
- Treat PostgreSQL as the system of record; use Alembic migrations for schema changes.
- Keep original document wording immutable and retain source-section references for every extracted obligation.

## Disclaimer

This prototype is not certified for regulatory compliance. Regulatory interpretations and AI-generated recommendations require qualified human review.
