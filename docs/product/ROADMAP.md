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

### Released: `0.1.0`

- Preserve the working Gemini demo.
- Document what is real versus placeholder.
- Establish the five-role workflow and shared product memory.

### Released: `0.2.0`

- Removed obsolete sample-data notices.
- Added persisted Recent Scans and private image/result storage.
- Added detail reopening and Demo-data deletion boundaries.
- Added a minimized seven-day operational access audit.
- `REQ-001` through `REQ-005` are user-validated.

### Next candidate: `0.3.0`

- Fixed severity-score/water-stress-level mapping and explicit level display
  beside `x/5` (`REQ-006`, approved; detailed presentation pending).
- Prompt and structured-output consistency improvements (proposed; scope and
  acceptance criteria pending user approval).
- Optional structure-regression evaluation using authorized unlabelled images;
  not a diagnostic-accuracy claim (proposed).

The broader `0.3.0` package remains a candidate until the user approves each
requirement. The approximately 200 unlabelled images are not an implementation
dependency and will not be treated as training or diagnostic evaluation data.
