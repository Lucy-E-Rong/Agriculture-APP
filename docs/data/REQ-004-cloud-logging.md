# REQ-004 Cloud Logging Contract

Status: implemented and deployed on 2026-08-21; technical production checks
passed. User acceptance remains pending, so REQ-004 is not yet validated.

## Resource boundary

- Google Cloud project: `vlm-api-2026-001`
- Dedicated log bucket: `farmscout-access-audit`
- Region: `us-east1`
- Retention: 7 days
- Dedicated log ID: `farmscout-access-audit`
- Dedicated view: `farmscout-access-audit-view`
- Dedicated sink: `farmscout-access-audit-sink`

This audit stream is operational data. It must not be written to Supabase
Postgres, `scans`, `scan-images`, a training/evaluation dataset, or Vercel's
ephemeral filesystem. Google Monitoring remains the source for aggregated
Gemini request counts and status time series; those aggregates are not copied
into these events.

## One-event-per-request contract

Exactly one event is emitted after each relevant request finishes:

- `GET /access/verify` -> action `access_verify`
- `POST /api/scans/analyze` -> action `scan_analyze`

The payload is an allowlist. No other fields may be merged from request,
response, exception, provider, or framework objects.

```json
{
  "schema_version": "1",
  "event_id": "uuid",
  "occurred_at_utc": "RFC3339 timestamp",
  "request_id": "opaque generated uuid",
  "environment": "production|preview|development",
  "action": "access_verify|scan_analyze",
  "client_ip": "validated IPv4/IPv6 or null",
  "ip_source": "x-vercel-forwarded-for|x-forwarded-for|unavailable|invalid",
  "external_api_used": true,
  "provider": "gemini|api_provider|local_vlm|mock|null",
  "provider_outcome": "succeeded|failed|not_called",
  "outcome": "succeeded|failed",
  "http_status": 200,
  "error_category": "allowlisted value or null"
}
```

Rules:

- `event_id` and `request_id` are generated server-side and contain no product
  identifier.
- `occurred_at_utc` records request completion in UTC.
- `action` is mapped from the matched route; do not record a raw URL.
- `external_api_used=false` requires `provider=null` and
  `provider_outcome=not_called`.
- `external_api_used=true` requires a supported provider and a succeeded/failed
  provider outcome.
- `http_status` is the final application response status, not a provider status.
- Audit write failure must not change the already-determined application status.
  It may produce a sanitized non-audit operational signal without the event
  payload or client IP.

Allowed error categories:

- `auth_failed`
- `validation_failed`
- `provider_timeout`
- `provider_rejected`
- `provider_invalid_response`
- `persistence_failed`
- `internal_error`
- `audit_write_failed` (operational signal only; never recursively audit it)

Successful events use `error_category=null`. Unknown exception text is mapped to
`internal_error`; it is never copied into the event.

## Trusted client IP rule

In a verified Vercel runtime:

1. Read `x-vercel-forwarded-for` first.
2. Fall back to `x-forwarded-for` only when the Vercel-specific header is absent.
3. Accept exactly one syntactically valid IPv4 or IPv6 address after trimming.
4. Normalize it with a standard IP-address parser.
5. Store `null` with `ip_source=invalid` for malformed or multi-value input.
6. Store `null` with `ip_source=unavailable` when no trusted header exists.

Outside a verified Vercel runtime, client-supplied forwarding headers are not
trusted and `client_ip` remains null. If a proxy/CDN is later placed in front of
Vercel, this rule must be reassessed before claiming that the original visitor
IP is retained.

## Forbidden content

Never record:

- demo access codes, API keys, service-account credentials, database passwords,
  cookies, `Authorization`, or any request headers other than the single parsed
  IP value;
- images, Base64, image paths, object URLs, scan IDs, crop/location IDs, or any
  other product-record identifier;
- request or response bodies, raw query strings, form data, filenames, prompts,
  full model/provider responses, diagnosis, symptoms, causes, recommendations,
  or confidence/severity results;
- raw exception messages, stack traces, library diagnostics, user agents,
  referrers, geolocation headers, or arbitrary labels.

## IAM and runtime identity

- Runtime service account: `farmscout-audit-writer`
- Runtime role: `roles/logging.logWriter` only; no log viewer or project-wide
  editor/owner role.
- Owner and each authorized engineer use individual Google identities. Do not
  share credentials.
- Read access targets the dedicated view, not the whole project, using
  `roles/logging.viewAccessor` at the view resource when supported by the setup.
- Do not create or commit a downloaded JSON service-account key.

Preferred Vercel credential design is keyless Workload Identity Federation using
Vercel's deployment OIDC token. Expected non-secret configuration values are:

- `GCP_PROJECT_ID=vlm-api-2026-001`
- `GCP_AUDIT_LOG_ID=farmscout-access-audit`
- `GCP_SERVICE_ACCOUNT_EMAIL=farmscout-audit-writer@vlm-api-2026-001.iam.gserviceaccount.com`
- Workload identity pool/provider resource names required by the Google auth
  library

No secret environment variable is defined until the credential mechanism is
verified. If keyless federation cannot be supported by the deployed Python
runtime, a service-account key would require a separate explicit security
decision, secure Vercel-only storage, rotation, and revocation procedure.

## Verification checklist

- [x] Bucket is active in `us-east1` with 7-day retention, Observability
  Analytics disabled, and no Supabase dependency.
- [x] Sink routes only
  `logName="projects/vlm-api-2026-001/logs/farmscout-access-audit"` to the
  dedicated bucket.
- [x] Dedicated view uses `LOG_ID("farmscout-access-audit")` and returned the
  contract-conformant synthetic event `synthetic-req004-validation-v2`.
- [x] Runtime identity has exactly `roles/logging.logWriter`; the predefined
  role contains only `logging.logEntries.create` and
  `logging.logEntries.route`. The service account has no key.
- [x] A production Vercel request wrote a contract-conformant event through
  keyless federation using the production runtime identity; no service-account
  credential was created for testing.
- Owner and individually approved engineers can query the view; other test
  identities cannot.
- [x] Local request-contract tests cover one-event-per-request behavior for both
  relevant endpoints and the supported outcome/IP mappings.
- [x] Production 401 smoke produced an `access_verify` event with the expected
  allowlisted fields and did not change the business response.
- [x] Negative code tests and production payload inspection found none of the
  forbidden fields or values.
- Day-eight queries cannot return day-one events. Physical purge timing remains
  eventually consistent per the approved decision.
