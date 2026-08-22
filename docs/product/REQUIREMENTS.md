# Requirements Register

Status terms follow the repository `AGENTS.md`.

| ID | Requirement | Status | Target | Owner | Acceptance summary |
| --- | --- | --- | --- | --- | --- |
| REQ-001 | Upload a lettuce image and receive a structured Gemini analysis through the hosted backend. | validated | 0.1.0 | AI/VLM + Full-stack | User successfully selected, uploaded, and analyzed an image. |
| REQ-002 | Remove the sentence indicating that sample data is shown before backend connection from every page and remove its unused English/Chinese translations. | validated | 0.2.0 | Full-stack | Sentence is absent throughout the app; unrelated copy is unchanged; technical checks pass. |
| REQ-003 | Replace dashboard Recent Scans mock data with persisted successful scan records and show only the latest 10. | validated | 0.2.0 | Data + Full-stack | Latest 10 successful `demo` records appear newest first across supported clients; failed or incompletely persisted scans do not appear; mock fallback is removed. |
| REQ-004 | Write one structured access/API audit event per relevant FastAPI request to a dedicated Google Cloud Logging bucket retained for seven days, without using the product database. | validated | 0.2.0 | Data + Full-stack | `/access/verify` and `/api/scans/analyze` each produce one minimized event; only authorized viewers can read it; day-eight queries cannot return day-one events; forbidden sensitive fields are absent. |
| REQ-005 | Preserve each successful scan's compressed image in private Supabase Storage and its structured result in Supabase Postgres so a Recent Scan can be reopened. | validated | 0.2.0 | Data + Full-stack | Records use `data_stage=demo` and `data_purpose=user_upload`; images are private; details reopen; Demo data can be removed as a group; uploads are never treated as training data. |
| REQ-006 | Define a fixed mapping between severity score and water stress level, and show the level beside the existing `x/5` severity display. | approved | 0.3.0 | AI/VLM + Full-stack | The score/level mapping is consistent in model output and UI; the detail result shows `x/5` with `none`, `low`, `medium`, `high`, or `critical`; exact presentation is approved before implementation. |

## Important interpretation notes

- `REQ-003` and `REQ-005` were approved for implementation on 2026-08-20 and
  share one persistence design. The database retains all successful Demo scans;
  the client displays only the latest 10.
- `REQ-003/005` use the Supabase Free Plan. Images belong in a private Storage
  bucket, while scan metadata and structured results belong in Postgres. Do not
  partition the database by day; dates may organize object paths and queries.
- Demo uploads are product data, not expert-labelled training data, and must not
  enter training or evaluation datasets.
- `REQ-004` uses a dedicated `farmscout-access-audit` Cloud Logging bucket with
  seven-day retention. It remains separate from Supabase scan data and from
  Google Monitoring's Gemini aggregate metrics. The production runtime uses
  Vercel OIDC and a production-subject-only GCP Workload Identity Federation
  binding; no long-lived service-account key exists.
- `REQ-001/002/003/004/005` were accepted by the user and are validated in the
  released `0.2.0` Demo.
- `REQ-006` is the first approved `0.3.0` requirement. Its detailed mapping and
  presentation remain to be finalized before implementation.
- IP addresses and crop images are potentially sensitive. Their use must be
  transparent and minimized.

## New requirement template

```text
ID:
Title:
Source/date:
Problem:
Proposed behavior:
Non-goals:
Acceptance criteria:
Dependencies:
Privacy/security impact:
Status:
Target version:
Owner:
```
