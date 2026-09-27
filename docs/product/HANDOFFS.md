# Handoffs

Use this file only for concise cross-role handoffs. Do not paste complete chat
transcripts.

## Open handoffs

Date: 2026-08-23
Requirement ID: V0.3-REQ-001 through V0.3-REQ-006, V0.3-REQ-008
From: AI/VLM Engineer, UX Designer, Data Engineer, Full-stack Engineer
To: Product Manager and user
Status: implemented and deployed to Vercel Production; user validation pending
Approved scope: Greenhouse-lettuce water-stress assessment, result presentation,
real Scan Context, and front-end-only Environmental Data Demo.
Evidence/files: Gemini Prompt/schema/validators and tests; Expo result/context/Demo
components; persistence compatibility; 34 backend tests; Python compilation;
ESLint; TypeScript; 14-route Expo Web export; `git diff --check`.
Decisions already made: No Unable state, no confidence-triggered review, no
timeline, no database migration, no real sensor connection.
Open questions: Product-owner acceptance of real image analysis, Scan Context
save/reopen behavior, result presentation, and supported mobile behavior.
Requested next action: Complete product-owner acceptance testing; the branch is
now aligned with `origin/codex/v0.3-water-stress`.

## Completed handoffs

Date: 2026-09-28
Requirement ID: Local Milestone 1 image preparation (separate from App 0.3.0)
From: Data Engineer and product owner
To: Product Manager
Status: 263 originals processed; 1,956 crops produced; product owner confirms
visual quality review complete. No symptom labels or model evaluation.
Evidence/files: `scripts/crop_dataset.py`, `scripts/DATASET_CROPPING.md`,
`dataset/run_20260927_195010_509506/summary.json`, and `manifest.csv`.
Requested next action: Keep the local research batch separate from Demo user
uploads; define expert labels and evaluation only as a later approved workflow.

Date: 2026-08-21
Requirement ID: REQ-002, REQ-003, REQ-004, REQ-005
From: Full-stack Engineer
To: Product Manager and user
Status: validated and released in `0.2.0`
Evidence/files: production FastAPI and Expo Web deployments; backend tests;
Expo lint, TypeScript, and Web export; production health/access/API/Web smoke;
real Vercel WIF Cloud Logging event; `docs/product/releases/v0.2.0.md`
Requested next action: Complete. Preserve `0.2.0` as the released baseline.

Date: 2026-08-21
Requirement ID: REQ-003, REQ-005
From: Data Engineer
To: Full-stack Engineer
Status: implemented locally; technical checks passed; deployment and user
validation pending
Evidence/files: Supabase migrations and persistence documentation; FastAPI
persistence endpoints and contract tests; Expo/Web Recent Scans and detail flow
Requested next action: Obtain deployment authorization, deploy, and complete
user acceptance before marking either requirement `validated`.

## Template

```text
Date:
Requirement ID:
From:
To:
Status:
Approved scope:
Evidence/files:
Decisions already made:
Open questions:
Requested next action:
```
