# Product Scope

## Product purpose

FarmScout is an AI-assisted greenhouse crop scouting tool. Its immediate purpose
is to let a small internal group upload lettuce images, receive cautious visible-
symptom assessments, and collect feedback before building a production system.

It is an assistance tool, not a definitive plant-disease diagnosis service.

## Version stages

### `0.x` — personal independent demo

- Prove the image-to-analysis workflow.
- Improve prompts, result clarity, and basic usability.
- Replace misleading mock content gradually.
- Add lightweight scan history and operational visibility suitable for a small
  demo.
- Iterations may use `0.1.x`, `0.2.x`, `0.3.x`, and so on.

### `1.x` — expert and management review

- Incorporate agricultural expert and manager feedback.
- Define accepted labels, severity standards, and review workflows.
- Improve evaluation evidence and domain correctness.
- Support structured internal trials.

### `2.x` — user-facing product

- Add production-grade identity, organizations, security, privacy, retention,
  reliability, data management, and release processes.
- Build real crop/location workflows and useful reporting.
- Prepare formal iOS/Android distribution only when justified.

## Out of scope for the current setup task

- Implementing scan persistence or audit logging.
- Changing the Gemini prompt.
- Activating Supabase.
- Building new screens or replacing mock modules.
- Deploying or pushing changes.
- Publishing through App Store or TestFlight.
