# Changelog

This is the product-level changelog. Git history remains the code-level record.

## Unreleased

### 0.2.0 candidate — implemented and deployed, acceptance pending

- Removed the obsolete sample-data notice and its unused English/Chinese copy.
- Replaced Recent Scans mock data with the newest 10 successfully persisted Demo
  scans, with full detail reopening.
- Added private Supabase image/result persistence with compensation on partial
  failure and Demo-specific deletion boundaries.
- Added minimized FastAPI access and scan-analysis audit events written through
  keyless Vercel OIDC/GCP Workload Identity Federation to a dedicated seven-day
  Cloud Logging bucket.
- Deployed the FastAPI backend and Expo Web candidate to Vercel Production and
  completed non-sensitive technical smoke checks. User acceptance is pending, so
  this candidate is not yet a released or validated version.

## 0.1.0 — Personal independent demo

- Expo mobile/web demo with access-code gate.
- Hosted FastAPI backend on Vercel.
- Gemini Developer API image analysis with structured lettuce assessment.
- Client-side image resize/compression.
- English and Simplified Chinese interface options.
- Placeholder dashboard, crops, locations, and reports modules.
