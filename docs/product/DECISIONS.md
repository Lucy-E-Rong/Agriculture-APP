# Decision Log

## DEC-001 — Five standing role tasks

- Date: 2026-08-20
- Status: approved
- Decision: Maintain five independent FarmScout tasks: Product Manager, UX
  Designer, Full-stack Engineer, AI/VLM Engineer, and Data Engineer.
- Reason: Separate product, design, implementation, model, and data concerns
  without creating excessive coordination overhead.
- Consequence: Version and knowledge governance belong to the Product Manager.
  There is no separate QA task.

## DEC-002 — Shared repository instructions and durable memory

- Date: 2026-08-20
- Status: approved
- Decision: Store team-wide working rules in root `AGENTS.md` and durable product
  memory in `docs/product/`.
- Reason: Independent task transcripts are separate; repository files provide a
  shared, reviewable source of truth.
- Consequence: Every role must read these files before acting.

## DEC-003 — Safe parallel work

- Date: 2026-08-20
- Status: approved
- Decision: Tasks may share the same repository for reading, but simultaneous
  code changes must use separate worktrees/branches or be serialized.
- Reason: Prevent one task from overwriting another task's changes.

## DEC-004 — Version stages

- Date: 2026-08-20
- Status: approved
- Decision: `0.x` is the personal demo line, `1.x` is the expert/management review
  line, and `2.x` is the advanced user-facing line.

## DEC-005 — No database for the initial access audit record

- Date: 2026-08-20
- Status: implemented through DEC-007 and validated REQ-004
- Decision: The first access/API audit record should be a separate seven-day
  rolling record rather than a database feature.
- Constraint: The storage mechanism must work in the chosen deployment runtime;
  ephemeral serverless files may not satisfy retention and must be evaluated
  before implementation.

## DEC-006 — Supabase persistence for Demo scan history

- Date: 2026-08-20
- Status: approved
- Decision: Use the Supabase Free Plan for `REQ-003/005`. Store compressed scan
  images in private Storage and scan metadata plus complete structured analysis
  results in Postgres. Persist all successful Demo scans while clients display
  only the latest 10.
- Classification: Mark current records as `data_stage=demo` and
  `data_purpose=user_upload`. Expert-labelled training images remain a separate
  future dataset; Demo uploads must not be used for training or evaluation.
- Deletion: Demo records and their objects must support deliberate grouped
  deletion. Database tables are not partitioned by day.
- Access: The current Demo is restricted to the owner and engineers but does not
  provide identity-based user isolation; that limitation must not be overstated.
- Consequence: Data engineering defines the schema, private bucket controls, and
  safe deletion behavior before Full-stack integrates the scan and history flow.

## DEC-007 — Google Cloud Logging for the seven-day access audit

- Date: 2026-08-21
- Status: approved; implementation authorized 2026-08-21
- Decision: Use a dedicated `farmscout-access-audit` Google Cloud Logging bucket
  with `retention=7 days`. Vercel FastAPI will write one minimized structured
  audit event per relevant request. The bucket is completely separate from
  Supabase `scans` and `scan-images`.
- Metrics boundary: Existing Google Monitoring remains the source for aggregate
  Gemini usage metrics. The audit log must not duplicate its minute-level time
  series, quota, or aggregate status data.
- Access: Only the product owner and individually authorized engineers may view
  the dedicated log view. The runtime service account receives Logs Writer only
  and no read permission.
- Cost boundary: The Google Cloud project must have billing enabled. Demo usage
  is expected to remain within the current monthly 50 GiB logging free allotment,
  but zero cost is not guaranteed.
- Retention meaning: Events are no longer queryable after seven days; physical
  deletion is eventually consistent and is not guaranteed at an exact instant.
- Authorization boundary: Local code changes and the approved Cloud Logging
  resource/IAM setup are authorized. Commit, push, and deployment still require
  separate user authorization.

## DEC-008 — `0.3.0` greenhouse-lettuce water-stress assessment boundary

- Date: 2026-08-23
- Status: approved, implemented, and deployed as a `0.3.0` candidate; user
  acceptance pending
- Decision: Focus the Demo assessment on early visible water stress in greenhouse
  lettuce. Preserve `Visible signs`, `Possible stress sources`, and
  `Recommendations`, but separate direct observations from water-related sources
  and evidenced non-water factors that require confirmation.
- Severity: Use `0 none`, `1 low`, `2 low`, `3 medium`, `4 high`, `5 critical`.
  Show Healthy only for a usable lettuce image with no visible water-stress or
  other abnormality.
- Safety: Do not introduce an Unable/unknown/null Severity state. Unusable and
  non-lettuce images use retake/change-image gates and do not trigger Human review
  solely for that reason. Confidence thresholds do not trigger Human review.
- Human review: The UI is absent when false. When true, it shows structured
  reasons limited to high/critical water stress, an evidenced non-water factor to
  rule out, or genuinely ambiguous visible evidence.

## DEC-009 — `0.3.0` context and demonstration boundaries

- Date: 2026-08-23
- Status: approved, implemented, and deployed as a `0.3.0` candidate; user
  acceptance pending
- Decision: Replace the fixed scan-location example with optional per-scan text
  context stored in `location_snapshot`; do not create location UUID links from
  free text or add a per-plant timeline in this version.
- Environmental Data: Provide only a clearly labelled, collapsed front-end Demo
  in `0.3.0`. Demo values cannot enter requests, prompts, persistence, audit logs,
  or recommendations. Real sensor integration requires a later approved design.
- Compatibility: Hide Confidence only in the front end. Retain the API and
  database field so existing scan history remains readable.
