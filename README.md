# FarmScout

FarmScout is an Expo mobile/web demo for early visible water-stress assessment in greenhouse lettuce. A user selects an image, may enter scan context, and receives a structured assessment from a hosted FastAPI backend using the Gemini Developer API. Results and compressed images from successful Demo scans are stored privately and can be reopened from Recent Scans.

`0.2.0` is the latest user-validated release. The `0.3.0` assessment update is implemented and deployed; product-owner acceptance is still pending. The dashboard, crop/location management, reports, and sensor connection are placeholders or demos rather than live product workflows.

## Architecture

```text
mobile/  React Native + Expo app for iOS and Android
backend/ Python FastAPI API, database access, storage hooks, AI provider adapters
supabase/ SQL schema for Postgres tables, indexes, RLS, and storage notes
```

```text
Mobile App
  -> Python FastAPI Backend
    -> Supabase Postgres
    -> Supabase Storage
    -> AI Provider Adapter
      -> gemini: Gemini Developer API (default prototype path)
      -> api_provider: OpenAI / Claude-compatible API
      -> local_vlm: GPU server VLM endpoint
```

## Current Scope

- Default English UI with optional Simplified Chinese.
- Demo access-code gate; no individual user accounts.
- Dashboard, Crops, Scan, Locations, Reports, and Settings screens.
- Python backend with a single scan analysis endpoint.
- Gemini is the active deployed provider. Other API, mock, and local VLM adapters are scaffolding.
- Structured greenhouse-lettuce assessment with image-quality gates, visible signs, fixed water-stress Severity, possible sources, and recommendations.
- Successful Demo scans use private Supabase Storage and Postgres. Scan Context is a per-scan snapshot; location hierarchy and individual accounts are not live workflows.

## Project Docs

- [Product status, requirements, and decisions](docs/product/README.md)
- [Local image cropping and quality checks](scripts/DATASET_CROPPING.md)
- [Historical VLM dataset and model strategy (Chinese)](docs/archive/vlm-dataset-and-model-strategy.zh.md)

The local research image batch contains 263 source photos. A full cropping run produced 1,956 JPEG crops; the product owner reports completing visual quality review. These are not symptom-labelled examples and have not been used for model training or a measured before/after evaluation. The source photos and generated crops stay outside Git.

## Run Locally

Mobile:

```bash
cd mobile
npm install
npm run start
```

Backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```
