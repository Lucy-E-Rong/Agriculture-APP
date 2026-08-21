# Handoffs

Use this file only for concise cross-role handoffs. Do not paste complete chat
transcripts.

## Open handoffs

Date: 2026-08-21
Requirement ID: REQ-004
From: Product Manager
To: Full-stack Engineer
Status: in progress; GCP data layer verified and Full-stack integration requested
Approved scope: Dedicated `farmscout-access-audit` Cloud Logging bucket with
seven-day retention; one minimized structured event per relevant FastAPI
request; dedicated view and least-privilege IAM; no product-database storage.
Evidence/files: REQUIREMENTS.md; DEC-005; DEC-007
Decisions already made: Existing Google Monitoring continues to supply Gemini
aggregate metrics; only the owner and individually authorized engineers may
view; runtime identity is Logs Writer only; billing must be enabled; estimated
Demo usage is within the current logging free allotment but zero cost is not
guaranteed; seven days means no longer queryable, with eventually consistent
physical deletion.
Open questions: Vercel Team issuer, team slug, and project name must be confirmed
before creating a production-subject-only GCP Workload Identity Federation
binding. Do not create a long-lived service-account JSON key or grant an entire
identity pool access.
Requested next action: Full-stack Engineer enables/configures the approved
Vercel-to-GCP keyless identity boundary, implements centralized FastAPI audit
event emission, and completes local/identity integration checks. Commit, push,
and deployment are not authorized.
Evidence/files: `docs/data/REQ-004-cloud-logging.md`; active GCP bucket
`farmscout-access-audit` (`us-east1`, seven-day retention, Analytics off); sink
`farmscout-access-audit-sink` restricted to the matching log name; view
`farmscout-access-audit-view`; keyless writer service account
`farmscout-audit-writer@vlm-api-2026-001.iam.gserviceaccount.com` with Logs Writer
only; allowlisted synthetic event successfully written and queried through the
dedicated view.

## Completed handoffs

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
