# FarmScout Backend

FastAPI backend for mobile clients and AI scan analysis.

Successful analyses are persisted for `REQ-003/REQ-005`: the compressed JPEG
submitted to the model is uploaded to the private Supabase `scan-images` bucket,
then the complete validated result is inserted into Postgres. If the row insert
fails, the backend deletes the exact uploaded object as compensation.

## AI Providers

`POST /api/scans/analyze` accepts:

```json
{
  "provider": "gemini",
  "language": "en",
  "imageBase64": "...",
  "imageMimeType": "image/jpeg",
  "cropId": "crop-id",
  "greenhouseId": "greenhouse-id",
  "sectionId": "section-id",
  "tableId": "table-id",
  "rowId": "row-id"
}
```

Provider options:

- `gemini`: calls the Gemini Developer API using `GEMINI_API_KEY` and `GEMINI_MODEL`.
- `api_provider`: uses OpenAI when `OPENAI_API_KEY` is set, Anthropic when `ANTHROPIC_API_KEY` is set, otherwise a mock response.
- `local_vlm`: calls `LOCAL_VLM_URL`, expected to return the same JSON response schema.
- `mock`: always returns a deterministic sample response for local UI development.

## Gemini setup

Copy `.env.example` to `.env`, then set the key only in the backend environment:

```env
GEMINI_API_KEY=your-key-from-google-ai-studio
GEMINI_MODEL=gemini-3.6-flash
```

Never add the key to `mobile/.env` or commit `backend/.env`.

## Supabase persistence

Configure these values only in the backend environment:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-server-only-secret-key
SUPABASE_STORAGE_BUCKET=scan-images
SUPABASE_SIGNED_URL_TTL_SECONDS=300
```

`sb_secret_...` keys are sent only in Supabase's `apikey` header; they are never
sent to clients or treated as bearer JWTs. Legacy service-role JWTs remain
supported for local migration compatibility.

The history API is protected by the existing Demo access code:

- `GET /api/scans/recent` returns at most 10 successful Demo/user-upload records,
  newest first.
- `GET /api/scans/{scan_id}` returns the validated structured result and a
  short-lived signed image URL. It does not return `raw_model_response` or the
  Storage service key.

## Seven-day access audit

`GET /access/verify` and `POST /api/scans/analyze` each attempt exactly one
minimized structured event after the final application status is known. Events
go to the dedicated `farmscout-access-audit` Cloud Logging stream; they are not
stored in Supabase and do not duplicate Google Monitoring aggregate metrics.

Production uses keyless Vercel OIDC to impersonate the Logs Writer-only service
account through GCP Workload Identity Federation. Configure these non-secret
values for the Vercel Production environment only:

```env
GCP_PROJECT_ID=vlm-api-2026-001
GCP_PROJECT_NUMBER=694852084507
GCP_SERVICE_ACCOUNT_EMAIL=farmscout-audit-writer@vlm-api-2026-001.iam.gserviceaccount.com
GCP_WORKLOAD_IDENTITY_POOL_ID=farmscout-vercel
GCP_WORKLOAD_IDENTITY_POOL_PROVIDER_ID=farm-scout-production
GCP_AUDIT_LOG_ID=farmscout-access-audit
```

Vercel injects the short-lived `x-vercel-oidc-token` at runtime. Never save,
print, forward, or add that token as an environment variable. No JSON service
account key is used. Audit failures emit only a fixed operational message and
do not change the already-determined API response.

## Deploy to Vercel

Import the GitHub repository in Vercel and set the project's Root Directory to
`backend`. The included `vercel.json` pins the FastAPI function to the
Washington, D.C. region (`iad1`). Configure these Vercel environment variables:

```env
APP_ENV=production
GEMINI_API_KEY=your-current-key
GEMINI_MODEL=gemini-3.6-flash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-server-only-secret-key
```

## Response

```json
{
  "crop_is_lettuce": true,
  "crop_confidence": 0.96,
  "image_quality": {
    "usable": true,
    "issues": [],
    "retake_guidance": []
  },
  "plant_stress_detected": true,
  "stress_level": "medium",
  "severity_score": 3,
  "confidence": 0.74,
  "diagnosis": "string",
  "observed_symptoms": [],
  "possible_causes": [],
  "detected_issues": ["string"],
  "recommendations": ["string"],
  "needs_human_review": true
}
```
