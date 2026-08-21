# Project Status

Last reviewed: 2026-08-20

## Current version

`0.1.0` — personal independent demo.

The demo proves that a user can access the app, choose a crop image, send a
compressed image to a hosted backend, receive a structured Gemini analysis, and
view the result on mobile or web.

## Implemented and working

- Expo/React Native app runs on iOS through Expo Go and exports a web demo.
- FastAPI backend is deployed to Vercel in the `iad1` region.
- Mobile/web clients use `https://agriculture-app-green.vercel.app` by default.
- Demo access-code verification is implemented by the backend.
- Image library selection and client-side JPEG resize/compression are implemented.
- Gemini Developer API image analysis is implemented and was manually tested by
  the user successfully.
- Gemini responses use a structured schema covering image quality, lettuce
  confidence, visible symptoms, possible causes, stress level, severity,
  recommendations, and human-review need.
- English and Simplified Chinese UI switching exists in memory for the running
  session.
- Vercel Web Analytics component exists for the web build.

## Implemented scaffolding but not an active product workflow

- A local VLM adapter can call `LOCAL_VLM_URL`, but a reachable compatible local
  GPU service has not been established as part of the deployed demo.
- Supabase schema/migration files exist, but the current scan flow does not save
  scan records or images to Supabase.
- API-provider and mock-provider adapters exist but are not the primary tested
  production path.

## Placeholder or mock UI

- Dashboard values for today's scans, active alerts, and greenhouse count.
- Dashboard recent scans.
- Crops page content and add-crop preview.
- Locations hierarchy and greenhouse/section/table/row records.
- Reports charts, risk rows, and scan lists.
- Workspace name/domain and prompt-settings explanation in Settings.
- Scan location context is fixed to `GH1 · SA · T1 · R1` rather than chosen by the
  user.

## Known current limitations

- Successful analyses are not persisted and therefore do not enter Recent Scans.
- Refreshing or restarting loses the current scan result and in-memory settings.
- There is no user identity, organization account, real crop/location management,
  database-backed reporting, or complete audit trail.
- The web analytics view does not identify a person and may not contain the
  application-level API details needed by the product.
- The current backend converts provider failures into an HTTP 502 response.
- The current UI does not display the full technical error details returned by the
  backend.
- `REQ-004` Cloud Logging data infrastructure is configured and verified in GCP:
  the dedicated `farmscout-access-audit` bucket is active in `us-east1` with
  seven-day retention, and its sink, dedicated view, and keyless Logs Writer
  service account exist. FastAPI event emission, Vercel-to-GCP workload identity,
  deployment, and end-to-end validation are not complete.

## Existing local change to preserve

The user-approved `REQ-002` removal is implemented locally but remains
uncommitted. The target sentence was removed from Dashboard, Crops, and Reports,
and its unused English/Chinese translations were removed. ESLint, TypeScript,
residual-text search, and diff checks passed. Do not discard or bundle these
changes unintentionally; user acceptance is still pending.
