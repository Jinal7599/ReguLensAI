# ReguLens AI

AI-powered Regulatory Change Intelligence & Impact Assessment.

ReguLens AI is a hackathon prototype intended to help compliance teams discover regulatory publications, understand obligations, compare historical requirements and assess potential business impact.

## Iteration 1: UI foundation

This iteration provides a lightweight Streamlit application with:
- Overview dashboard and illustrative metrics
- Searchable regulatory feed with region and status filters
- Clause-level change analysis screen
- Regulatory source settings placeholder
- Render deployment blueprint

**Important:** All bundled publications and clause examples are synthetic demo data. They are not official regulatory publications and must not be used to make compliance decisions.

## Run locally

Requires Python 3.11 or newer.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
streamlit run app/main.py
```

Open the local URL printed by Streamlit (normally http://localhost:8501).

## Configuration

Copy `.env.example` to `.env` for future integrations. Do not commit API keys, OAuth secrets, database credentials or Streamlit secrets.

No external API credentials are required for the Iteration 1 UI.

## Deployment on Render

The repository includes `render.yaml` for a basic Streamlit web service. Connect the GitHub repository in Render and create a Blueprint deployment. Persistent database and object storage configuration will be added in a later iteration.

## Project structure

- `app/main.py`: Streamlit entry point and navigation
- `app/pages/`: UI screens
- `app/data/sample_data.py`: synthetic demo records
- `render.yaml`: Render service configuration

## Disclaimer

This prototype is not certified for regulatory compliance. AI-generated interpretations and recommendations require qualified human review.
