# FarmScout Product Memory

This directory is the durable shared memory for all FarmScout tasks. Chat history
is useful context, but these documents contain the canonical decisions and status
that future tasks should rely on.

## Reading order

1. `PROJECT_STATUS.md` — what exists now.
2. `PRODUCT_SCOPE.md` — what each product stage is trying to achieve.
3. `REQUIREMENTS.md` — approved, proposed, and deferred requirements.
4. `ROADMAP.md` — version scheme and near-term sequence.
5. `DECISIONS.md` — decisions and their reasoning.
6. `TEAM.md` — role ownership and collaboration flow.
7. `HANDOFFS.md` — work moving between roles.
8. `CHANGELOG.md` and `releases/` — version history.

## Rules for updating memory

- Code is evidence of implemented behavior; user acceptance is evidence of
  validated behavior.
- Every requirement uses an ID such as `REQ-001`.
- Every durable decision uses an ID such as `DEC-001`.
- Do not erase old decisions. Mark them superseded and link the replacement.
- The Product Manager is the canonical editor for scope, requirement status,
  roadmap, decisions, changelog, and release records.
- Specialists submit evidence and handoffs; the Product Manager reconciles them
  into the canonical documents.
- Never store secrets, private crop images, or raw production logs here.

## Current snapshot

- Product: FarmScout
- Current version: `0.2.0`
- Stage: personal independent demo
- Primary crop focus: lettuce
- Mobile/web client: Expo + React Native + Expo Router
- Backend: FastAPI deployed on Vercel
- Active external VLM path: Gemini Developer API
