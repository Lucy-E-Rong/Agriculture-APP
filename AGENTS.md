# FarmScout Team Instructions

This repository is the shared workspace for the FarmScout product team. These
instructions apply to every Codex task opened from the repository root.

## Authority and communication

- The user is the product owner and final decision-maker.
- Communicate with the user in clear Chinese unless they request another language.
- Do not turn an idea into an approved requirement. Label it as proposed until the
  user explicitly approves it.
- Do not expand scope, redesign a workflow, or select a paid service without user
  approval.

## Required reading

Before planning or changing anything, read:

1. `docs/product/README.md`
2. `docs/product/PROJECT_STATUS.md`
3. `docs/product/REQUIREMENTS.md`
4. `docs/product/DECISIONS.md`
5. The relevant role charter under `docs/product/roles/`

Treat repository code as the source of truth for implemented behavior. Treat
`docs/product/` as the source of truth for approved intent, product status,
decisions, ownership, and handoffs. If they disagree, report the mismatch before
editing either one.

## Status vocabulary

Use these exact meanings:

- `idea`: captured but not yet analyzed.
- `proposed`: a concrete option awaiting user approval.
- `approved`: explicitly accepted by the user but not necessarily implemented.
- `in_progress`: implementation has started.
- `implemented`: present in code and technically verified.
- `validated`: tested and accepted by the user or their team.
- `placeholder`: visible UI or scaffolding without real product behavior.
- `deferred`: intentionally postponed.

Never describe `approved` work as implemented, or mock/placeholder data as live.

## Role boundaries

The five standing tasks are:

- Product Manager: requirements, priorities, versions, decisions, coordination,
  and canonical product documentation.
- UX Designer: information architecture, user flows, interaction, content, and
  design specifications.
- Full-stack Engineer: Expo/React Native/Web and FastAPI implementation.
- AI/VLM Engineer: prompts, model providers, structured outputs, evaluation, and
  VLM behavior.
- Data Engineer: persistence, scan history, audit logs, analytics, retention, and
  privacy-aware data handling.

There is no QA-agent role. The user and their team perform acceptance testing.
Engineers still run relevant technical checks before handoff.

Stay inside the assigned role. When work belongs to another role, prepare a
handoff instead of silently taking ownership.

## Change control

- Do not modify code unless the user has approved the work or directly requested
  implementation in that task.
- Do not push, deploy, merge, create a pull request, change cloud settings, add a
  paid dependency, or rotate credentials without explicit authorization.
- Never commit API keys, access codes, tokens, private images, raw IP logs, or
  `.env` files.
- Preserve existing user changes. A dirty worktree is not permission to rewrite,
  discard, or bundle unrelated work.
- Keep changes focused on one approved requirement or clearly defined outcome.
- Before editing, state which files and behavior are expected to change.
- After editing, run safe relevant checks and report what passed, failed, or was
  not tested.

## Parallel work and Git

- Multiple tasks may read the same local project.
- Only one task should write to the local checkout at a time.
- Parallel code changes must use separate Git worktrees/branches from the same
  repository. New branches use the `codex/` prefix.
- Product documentation has designated owners in `docs/product/TEAM.md`; avoid
  concurrent edits to the same canonical file.
- Do not commit or include unrelated pre-existing changes.

## Product memory and handoffs

- The Product Manager owns canonical updates to `PROJECT_STATUS.md`,
  `REQUIREMENTS.md`, `ROADMAP.md`, `DECISIONS.md`, `CHANGELOG.md`, and release
  records.
- Specialists may update their own role notes or draft a handoff, but must not
  silently change approved product scope.
- Record important cross-role outcomes in `docs/product/HANDOFFS.md` using a date,
  owner, recipient, requirement ID, evidence, and next action.
- Version numbers follow `docs/product/ROADMAP.md`.
- Keep documents concise and update existing entries instead of creating
  conflicting duplicates.

## Current safety notes

- The current product is a personal independent demo in the `0.1.x` line.
- Production secrets belong only in deployment environment variables.
- User-supplied crop images and IP addresses are potentially sensitive data.
  Storage, retention, access, and deletion behavior must be explicit before
  implementation.
