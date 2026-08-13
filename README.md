# FarmScout

FarmScout is a cross-platform mobile app for greenhouse crop scouting. The mobile app lets a user select an exact crop location, capture or upload an image, and request an AI analysis from a Python backend. The backend can call either an external AI API provider or a local GPU-hosted VLM.

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
- Auth-ready mobile app shell.
- Dashboard, Crops, Scan, Locations, Reports, and Settings screens.
- Python backend with a single scan analysis endpoint.
- AI provider abstraction for Gemini, OpenAI/Anthropic, mock responses, and a local VLM.
- Structured lettuce assessment with crop checks, image-quality gates, visible symptoms, possible causes, and field recommendations.
- Supabase Postgres schema for organizations, profiles, locations, crops, scans, and AI settings.

## Project Docs

- [Agriculture lab image dataset requirements](docs/agriculture-lab-dataset-requirements.md)
- [VLM dataset collection and model strategy](docs/vlm-dataset-and-model-strategy.md)
- [VLM 图像数据集采集与模型策略（中文）](docs/vlm-dataset-and-model-strategy.zh.md)

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
