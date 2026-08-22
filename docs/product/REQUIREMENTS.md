# Requirements Register

Status terms follow the repository `AGENTS.md`.

| ID | Requirement | Status | Target | Owner | Acceptance summary |
| --- | --- | --- | --- | --- | --- |
| REQ-001 | Upload a lettuce image and receive a structured Gemini analysis through the hosted backend. | validated | 0.1.0 | AI/VLM + Full-stack | User successfully selected, uploaded, and analyzed an image. |
| REQ-002 | Remove the sentence indicating that sample data is shown before backend connection from every page and remove its unused English/Chinese translations. | validated | 0.2.0 | Full-stack | Sentence is absent throughout the app; unrelated copy is unchanged; technical checks pass. |
| REQ-003 | Replace dashboard Recent Scans mock data with persisted successful scan records and show only the latest 10. | validated | 0.2.0 | Data + Full-stack | Latest 10 successful `demo` records appear newest first across supported clients; failed or incompletely persisted scans do not appear; mock fallback is removed. |
| REQ-004 | Write one structured access/API audit event per relevant FastAPI request to a dedicated Google Cloud Logging bucket retained for seven days, without using the product database. | validated | 0.2.0 | Data + Full-stack | `/access/verify` and `/api/scans/analyze` each produce one minimized event; only authorized viewers can read it; day-eight queries cannot return day-one events; forbidden sensitive fields are absent. |
| REQ-005 | Preserve each successful scan's compressed image in private Supabase Storage and its structured result in Supabase Postgres so a Recent Scan can be reopened. | validated | 0.2.0 | Data + Full-stack | Records use `data_stage=demo` and `data_purpose=user_upload`; images are private; details reopen; Demo data can be removed as a group; uploads are never treated as training data. |
| V0.3-REQ-001 | Define a fixed Severity mapping for visible water stress and explain the score and level beside `x/5`. | implemented | 0.3.0 | AI/VLM + Full-stack | Mapping is `0 none`, `1 low`, `2 low`, `3 medium`, `4 high`, `5 critical`; the UI shows `x/5`, level, and an explanation; Healthy appears only when no other visible abnormality exists. |
| V0.3-REQ-002 | Focus the structured Gemini assessment on early visible water-stress signs in greenhouse lettuce. | implemented | 0.3.0 | AI/VLM | Prompt and output validation separate visible evidence from inferred sources and do not present the result as definitive diagnosis. |
| V0.3-REQ-003 | Keep `Possible stress sources` while prioritizing water-related field checks and cautiously identifying evidenced non-water factors to rule out. | implemented | 0.3.0 | AI/VLM + Full-stack | Water-source and rule-out categories are constrained; non-water factors require visible evidence and are not presented as confirmed disease, pest, or nutrient diagnoses. |
| V0.3-REQ-004 | Keep `Recommendations` while making them specific to greenhouse context and the observed evidence. | implemented | 0.3.0 | AI/VLM + Full-stack | Recommendations may request irrigation, root-zone, nearby-plant, or available environmental checks; they do not invent sensor readings or prescribe doses, chemicals, or plant destruction. |
| V0.3-REQ-005 | Restructure the result UI for the water-stress assessment. | implemented | 0.3.0 | UX + Full-stack | Title is `Water Stress Assessment`; front-end Confidence is removed; Visible signs remains; Human review is completely hidden when false and shows structured reasons only when true. |
| V0.3-REQ-006 | Replace the fixed scan-location example with real optional Scan Context input and persisted display. | implemented | 0.3.0 | UX + Data + Full-stack | Greenhouse, section, table, row, plant/sample ID, variety, and growth stage are trimmed, empty values are omitted, stored in `location_snapshot`, and reopened in scan details without inventing UUID relationships. |
| V0.3-REQ-008 | Add a clearly labelled front-end Environmental Data demonstration without a sensor integration. | implemented | 0.3.0 | UX + Full-stack | The collapsed `Demo / Not connected` module is presentation-only and cannot enter the analyze request, Prompt, persistence, or Recommendations. |

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
- The earlier draft `REQ-006` was renumbered `V0.3-REQ-001` before implementation
  so the `0.3.0` work uses version-scoped IDs without colliding with released IDs.
- `V0.3-REQ-007` (a dated per-plant scan timeline) was discussed and explicitly
  removed from the version before implementation. Existing `created_at` values
  remain, but no timeline or trend feature was added.
- The approximately 200 unlabelled images are not a `0.3.0` dependency and are
  not training or diagnostic-evaluation data.
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
