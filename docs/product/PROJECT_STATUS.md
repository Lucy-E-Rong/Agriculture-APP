# Project Status

Last reviewed: 2026-08-22

## Current version

`0.2.0` — released and user-validated personal independent demo.

The demo proves that a user can access the app, choose a crop image, send a
compressed image to a hosted backend, receive a structured Gemini analysis, and
view the result on mobile or web.

The user confirmed acceptance of `REQ-001` through `REQ-005` on 2026-08-22. The
release includes persisted scan history and images, detail reopening, and the
seven-day operational access audit.

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
- Successful Demo scans are persisted to private Supabase Storage and Postgres;
  Recent Scans shows the newest 10 successful records and can reopen details.
- The production FastAPI runtime emits minimized allowlist audit events for
  access verification and scan analysis through keyless GCP Workload Identity
  Federation to a dedicated seven-day Cloud Logging bucket.
- Production deployments are available at
  `https://agriculture-app-green.vercel.app` and
  `https://farmscout-web-demo.vercel.app`.

## Implemented scaffolding but not an active product workflow

- A local VLM adapter can call `LOCAL_VLM_URL`, but a reachable compatible local
  GPU service has not been established as part of the deployed demo.
- API-provider and mock-provider adapters exist but are not the primary tested
  production path.

## Placeholder or mock UI

- Dashboard values for today's scans, active alerts, and greenhouse count.
- Crops page content and add-crop preview.
- Locations hierarchy and greenhouse/section/table/row records.
- Reports charts, risk rows, and scan lists.
- Workspace name/domain and prompt-settings explanation in Settings.
- Scan location context is fixed to `GH1 · SA · T1 · R1` rather than chosen by the
  user.

## Known current limitations

- In-memory settings are still lost on refresh or restart.
- There is no user identity, organization account, real crop/location management,
  database-backed reporting, or user-facing audit-log viewer.
- The web analytics view does not identify a person and may not contain the
  application-level API details needed by the product.
- The current backend converts provider failures into an HTTP 502 response.
- The current UI does not display the full technical error details returned by the
  backend.

## Next version

`0.3.0` is the next personal-demo iteration. Its first approved requirement is
to define a fixed severity-score/water-stress-level mapping and show the level
beside `x/5` in the UI. Broader Prompt and structure-consistency work remains
proposed pending product discussion.
