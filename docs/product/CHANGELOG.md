# Changelog

This is the product-level changelog. Git history remains the code-level record.

## Unreleased

- Implement the local `0.3.0` candidate for early visible water-stress assessment
  in greenhouse lettuce.
- Add fixed Severity mapping and explanations, retain Visible signs, focus
  Possible stress sources and Recommendations, and show Human review reasons only
  when review is triggered.
- Rename the result to Water Stress Assessment and remove front-end Confidence
  while keeping backend/history compatibility.
- Replace the fixed scan-location example with persisted optional Scan Context.
- Add an explicitly front-end-only Environmental Data Demo; no sensor data is
  connected, sent, or stored.
- Remove the proposed per-plant timeline from this version.

## 0.2.0 — Validated personal Demo release (2026-08-22)

- Removed the obsolete sample-data notice and its unused English/Chinese copy.
- Replaced Recent Scans mock data with the newest 10 successfully persisted Demo
  scans, with full detail reopening.
- Added private Supabase image/result persistence with compensation on partial
  failure and Demo-specific deletion boundaries.
- Added minimized FastAPI access and scan-analysis audit events written through
  keyless Vercel OIDC/GCP Workload Identity Federation to a dedicated seven-day
  Cloud Logging bucket.
- Fixed Supabase signed-image URL normalization so persisted private images can
  reopen reliably across signed URL response variants.
- Deployed the FastAPI backend and Expo Web to Vercel Production, completed
  non-sensitive technical smoke checks, and received user acceptance for
  `REQ-001` through `REQ-005`.

## 0.1.0 — Personal independent demo

- Expo mobile/web demo with access-code gate.
- Hosted FastAPI backend on Vercel.
- Gemini Developer API image analysis with structured lettuce assessment.
- Client-side image resize/compression.
- English and Simplified Chinese interface options.
- Placeholder dashboard, crops, locations, and reports modules.
