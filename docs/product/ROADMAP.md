# Roadmap and Versioning

## Version convention

- `0.1.0`: current personal independent demo baseline.
- `0.1.x`: focused corrections that preserve the current product shape.
- `0.2.x`, `0.3.x`, ...: meaningful personal-demo iterations.
- `1.x`: expert-group and management-reviewed internal versions.
- `2.x`: advanced user-facing versions.

The Product Manager proposes a target version. The user approves it. A version is
not considered released until its implemented items are documented and the user
or their team has completed the intended acceptance testing.

## Near-term sequence

### Current: `0.1.0`

- Preserve the working Gemini demo.
- Document what is real versus placeholder.
- Establish the five-role workflow and shared product memory.

### Candidate: `0.1.1`

- Small copy and clarity fixes only.
- Record the already-started removal of the dashboard sample-data sentence.

### Candidate: `0.2.0`

- Dynamic Recent Scans, latest 10 (`REQ-003`, approved).
- Private image and structured-result persistence (`REQ-005`, approved).
- Seven-day operational audit record.
- Clear failure behavior and privacy notes.

`REQ-003/005` are approved for implementation. The seven-day operational audit
record (`REQ-004`) remains outside the active implementation package until its
cleanup behavior is approved.
