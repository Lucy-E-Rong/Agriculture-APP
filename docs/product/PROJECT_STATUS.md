# Project Status

Last reviewed: 2026-09-28

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
- Environmental Data is an explicitly labelled front-end Demo and is not a real
  sensor connection.

## Known current limitations

- In-memory settings are still lost on refresh or restart.
- There is no user identity, organization account, real crop/location management,
  database-backed reporting, or user-facing audit-log viewer.
- Scan Context is a per-scan text snapshot, not a validated location hierarchy or
  per-plant timeline.
- The web analytics view does not identify a person and may not contain the
  application-level API details needed by the product.
- The current backend converts provider failures into an HTTP 502 response.
- The current UI does not display the full technical error details returned by the
  backend.

## Next version

`0.3.0` is implemented, technically verified, committed, pushed to
`origin/codex/v0.3-water-stress`, and deployed to the existing Vercel Production
services. Product-owner acceptance of the App update remains pending, so `0.2.0`
remains the latest released and validated version.

The candidate focuses FarmScout on early visible water-stress assessment for
greenhouse lettuce. It adds the fixed Severity mapping and explanation, focused
Prompt/source/recommendation rules, conditional human-review reasons, real Scan
Context input, and a clearly labelled front-end-only Environmental Data Demo.

Technical evidence: 34 backend tests, Python compilation, ESLint, TypeScript,
Expo Web export for 14 routes, `git diff --check`, fixed-location residue search,
and front-end Confidence-rendering residue search all passed.

Production deployments completed 2026-08-23:

- Backend: `dpl_BsmEJBqdiTvk11u2gmzADCA3vVcj` at
  `https://agriculture-app-green.vercel.app` (`READY`).
- Web: `dpl_3LStyeRaLVrQMTPYFUfMEzBQK3pC` at
  `https://farmscout-web-demo.vercel.app` (`READY`).

## Local research image preparation

- The local source collection contains 263 HEIC photos in five Period folders.
- The full 2026-09-27 cropping run processed all 263 without processing errors
  and generated 1,956 JPEG candidate crops, four review flags, 940 rejected
  edge candidates, and 263 annotated previews. Its summary and manifest are in
  `dataset/run_20260927_195010_509506/`.
- The 1,956 JPEG crops total 627,163,692 bytes (598.11 MiB). The full run,
  including previews and manifests, uses about 675 MB on this Mac.
- The product owner confirmed on 2026-09-28 that visual quality review of this
  batch is complete and accepted the resulting count. The 70% completeness rule
  remains a geometric estimate, not an expert instance-segmentation measure.
- The batch has no expert symptom or water-stress labels, no confirmed plant/time
  linkage, and no measured before/after Prompt evaluation. It has not been used
  to train or evaluate the deployed model and is not stored in the App database.
- `Photos/` and `dataset/` remain local research data outside Git and are not
  uploaded to the App backend or Supabase. The cropper source and instructions
  are versioned with the repository.
